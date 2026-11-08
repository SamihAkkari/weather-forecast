import copy
import logging
import time
import subprocess

from src.data.repository import DatabaseRepository
from src.ingestion.processors.arome_grib import GribProcessor
from src.ingestion.processors.observations import ObservationProcessor
from src.ingestion.time_manager import TimeManager
from datetime import timedelta
from urllib.parse import urlparse, parse_qs
from src.config.config import Config

import random

from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError,
    Timeout,
    HTTPError,
)

logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
import logging

class BaseIngestor(ABC):
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fetch(self, *args): ...

    @abstractmethod
    def ingest(self, data): ...

    @abstractmethod
    def run(self, *args): ...

    def trigger_dbt(self, tag): # rigid function to change later         
        if Config.DBT_MODE == "docker_exec":
            cmd = ["docker", "exec", "-w", "/usr/app/dbt/weather_project",
                   "dbt_runner", "dbt", "run", "--select", f"tag:{tag}"]
        else:
            cmd = [Config.DBT_BIN, "run", "--select", f"tag:{tag}",
                   "--project-dir", Config.DBT_PROJECT_DIR,
                   "--profiles-dir", Config.DBT_PROFILES_DIR]
        try:
            subprocess.run(cmd, check=True, 
            capture_output=True, # This captures stdout and stderr
            text=True            # This returns strings instead of bytes
            )
            logger.info("dbt model executed successfully Success!")

        except subprocess.CalledProcessError as e:
            if "Completed successfully" in e.stdout and "PASS=1" in e.stdout:
                logger.info("dbt logic passed, but dbt crashed during logging/cleanup.")
            else:
                logger.error("dbt failed with exit code %s", e.returncode)
                logger.error("--- STDOUT ---\n%s", e.stdout)
                logger.error("--- STDERR ---\n%s", e.stderr)
                raise
             
    def _log_fetch(self, identifier, count):
        self.logger.info(f"Fetched {count} records for {identifier}")

    def _log_ingest(self, identifier, count):
        self.logger.info(f"Ingested {count} records for {identifier}")

    def _log_skip(self, reason):
        self.logger.info(f"Skipped   {reason}")

    def _log_error(self, context, error):
        self.logger.error(f"{context}: {error}")

class ObservationsIngestor(BaseIngestor):
    """Continuously ingest real-time weather observations"""

    def __init__(self, api_client):
        super().__init__()
        # self.repository = repository
        self.api_client = api_client
        self.retry_frequency = api_client.api.retry_frequency_seconds
        self.steps_back = api_client.api.steps_back
        self.time_steps_seconds = api_client.api.time_step_seconds
        self.data_base_target_table = api_client.api.bronze_table
        self.records_class = api_client.api.record_class
        self.max_retries = api_client.api.max_retries
        self.running = False

    # def sleep_until_next_hour(self):
    #     now = TimeManager.utc_now()
    #     next_hour = TimeManager.utc_truncated(now + timedelta(hours=1), to='hour')
    #     sleep_seconds = (next_hour - now).total_seconds()
    #     time.sleep(sleep_seconds)

    def fetch(self, params):
        """Fetch data from API"""
        try:
            response = self.api_client.fetch_data(params = params)  # your API method
            observation_processor = ObservationProcessor(response)
            records = observation_processor.get_ready_to_ingest_records(self.records_class)
            self._log_fetch("observations", len(records))
        except Exception as e:
            self._log_error("Observations fetching error", e)
            raise
        return records

    def ingest(self, records):
        """Ingest the fetched data into the database"""
        try:
            DatabaseRepository.insert_observations(records, self.data_base_target_table)
            self._log_ingest("observations", len(records))
        except Exception as e:
            self._log_error("Observations ingestion error", e)
            raise

    def run(self):
        """This can be used later with advanced schedulers"""        
        ingested_any = False
        for step_back in reversed(range(0, self.steps_back)):
            date = TimeManager.last_interval_iso(self.time_steps_seconds, step_back)

            if DatabaseRepository._this_date_is_already_ingested(date, self.data_base_target_table):
                self._log_skip(f"The data of date: {date} has already been ingested")
                continue

            logger.info(f"Fetching data for the date: {date}")
            
            try:
                records = self.fetch({"date": date, "format": "json"})
            except Exception:
                logger.exception("Fetch failed for %s, the next scheduled run will retry", date)
                break

            if not records or records == []:
                logger.info("Data for %s not available yet, the next run will retry", date)
                break

            self.ingest(records)
            ingested_any = True
        
        if ingested_any:
            self.trigger_dbt(tag=self.data_base_target_table)
        return ingested_any
    
            # if records != []:
            #     logger.info(f"Ingesting the data obtained with {len(records)} stations after {retry_count} retries")
            #     self.ingest(records)
            #     self.trigger_dbt(tag = self.data_base_target_table) #Here we use the bronze table name since bronze and silver have the same tables names just schema is what differs  
            #     break # stop retrying

            # retry_count += 1
            # if retry_count < self.max_retries:
            #     logger.info(f"Data not available yet, retrying {retry_count}/{self.max_retries} in {self.retry_frequency}s")
            #     time.sleep(self.retry_frequency)
            # else:
            #     logger.warning(f"Giving up on observation at time {date} after {self.max_retries} retries")
    
        
    # def run_loop(self):
    #     """Start continuous ingestion loop"""
    #     self.running = True
    #     logger.info("Real-time ingestor started")
    #     while self.running:
    #         for step_back in reversed(range(0, self.steps_back)):
    #             date = TimeManager.last_interval_iso(self.time_steps_seconds, step_back)
    #             self.run_once(date)
    #         logger.info(f"Sleeping until next hour...")
    #         self.sleep_until_next_hour()

    # def stop(self):
    #     self.running = False
    #     logger.info("Ingestor stopped")


class ForecastIngestor(BaseIngestor):
    """
    Ingest one AROME forecast run per call.
    Trigger externally (cron, scheduler)   this class does not manage timing.
    """

    def __init__(self, data_api_clients, description_api_client):
        super().__init__()
        self.data_api_clients = data_api_clients
        self.description_api_client = description_api_client
        
        self.update_frequency = data_api_clients[0].api.update_frequency_seconds # takes the update frequency of the first ny default needs to update
        # self.data_base_target_table = data_api_client.api.bronze_table
        # self.data_api_record_class = data_api_client.api.record_class
   
    
    
    def fetch(self, client, params: dict) -> list | None:
        """Fetch and process GRIB data with retries for transient API failures."""
    
        max_attempts = 3
        base_delay = 1.0
        max_delay = 10.0
    
        reference_time = params.get("referencetime")
    
        # Retry the network operation only, not GRIB processing.
        for attempt in range(1, max_attempts + 1):
            try:
                response = client.fetch_data(params=params)
                break
    
            except (
                ChunkedEncodingError,
                ConnectionError,
                Timeout,
                HTTPError,
            ) as exc:
                # Retry only transient network errors and selected HTTP statuses.
                retryable = not isinstance(exc, HTTPError) or (
                    exc.response is not None
                    and exc.response.status_code
                    in {429, 500, 502, 503, 504}
                )
    
                if not retryable or attempt == max_attempts:
                    logger.exception(
                        "Fetch failed for run %s on attempt %s/%s",
                        reference_time,
                        attempt,
                        max_attempts,
                    )
                    raise
    
                # Exponential backoff with jitter.
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                delay += random.uniform(0, 0.5)
    
                logger.warning(
                    "Transient fetch error for run %s "
                    "(attempt %s/%s): %s. Retrying in %.2f seconds.",
                    reference_time,
                    attempt,
                    max_attempts,
                    exc,
                    delay,
                )
    
                time.sleep(delay)
    
        # Process the response only after a successful fetch.
        if not response:
            self._log_skip(
                f"No GRIB data found for reference time {reference_time}"
            )
            return None
    
        try:
            grib_processor = GribProcessor(response, reference_time)
            records = grib_processor.get_ready_to_ingest_records(
                client.api.record_class
            )
    
            self._log_fetch("forecast", len(records))
            return records
    
        except Exception:
            logger.exception(
                "GRIB processing failed for run %s",
                reference_time,
            )
            raise

    def ingest(self, client, records: list[dict]) -> None:
        """Insert records into DB."""
        try:
            DatabaseRepository.insert_forecasts(records, client.api.bronze_table)
            logger.info(f"Ingested {len(records)} forecast records")
        except Exception as e:
            logger.error(f"Ingestion error: {e}")
            raise

    def extract_referencetime(self, href):
        """Extract referencetime from URL if present"""
        if "referencetime=" not in href:
            return None

        parsed = urlparse(href)
        query = parse_qs(parsed.query)
        reference_time = query["referencetime"][0]
        return reference_time

    def get_latest_run_time(self):
        response = self.description_api_client.fetch_data()
        runs_history = response.get("links", [])
        
        latest_run_time = None
        for item in runs_history:
            href = item.get("href")

            if not href:
                continue

            ref_time_iso_format = self.extract_referencetime(href)

            # skip items without referencetime
            if ref_time_iso_format is None:
                continue

            ref_time_datetime = TimeManager.convert_iso_datetime(ref_time_iso_format)

            if latest_run_time is None or ref_time_datetime > latest_run_time:
                latest_run_time = ref_time_datetime

        if latest_run_time is None:
            logger.error("No valid forecast run found in the api")
            raise ValueError("No valid forecast run found in the api")
        else:
            return TimeManager.convert_to_iso(latest_run_time)
        

    def run(self) -> None:
        """Fetch and ingest missing forecast intervals."""
    
        run_time = self.get_latest_run_time()
        intervals = ["00H06H","07H12H","13H18H","19H24H","25H30H","31H36H","37H42H","43H48H","49H51H",]
    
        # params = {
        #     "referencetime": run_time,
        #     "time": [
        #         "00H06H",
        #         "07H12H",
        #         "13H18H",
        #         "19H24H",
        #         "25H30H",
        #         "31H36H",
        #         "37H42H",
        #         "43H48H",
        #         "49H51H",
        #     ],
        #     "format": "grib2",
        # }
    
        # MAX_RETRIES = 5
        # WAIT_SECONDS = 6 * 60
        ingested_any = False
        for client in self.data_api_clients:
            for interval in intervals:
                if DatabaseRepository.forecast_interval_already_ingested(
                        reference_time=run_time,
                        forecast_interval=interval,
                        target_table_name=client.api.bronze_table):
                    self._log_skip(
                        f"Run {run_time}, interval {interval} "
                        "already ingested   skipping"
                    )
                    continue
    
                parameters = {"referencetime": run_time, "time": interval, "format": "grib2"}
                logger.info("Fetching data for run: %s, forecast interval: %s", run_time, interval)
                try:
                    records = self.fetch(client, parameters)
                except Exception:
                    logger.exception("Fetch failed for %s / %s", run_time, interval)
                    break

                if not records or records == []:
                    logger.info("Run %s interval %s not available yet", run_time, interval)
                    break  # later intervals won't be there either

                self.ingest(client, records)
                ingested_any = True

        if ingested_any:
            self.trigger_dbt(tag="forecast_arome")
        return ingested_any        
    
        #         records = None
    
        #         for attempt in range(1, MAX_RETRIES + 1):
        #             records = self.fetch(client, parameters)
    
        #             if records:
        #                 logger.info(
        #                     "Data found for interval %s on attempt %s/%s",
        #                     interval,
        #                     attempt,
        #                     MAX_RETRIES,
        #                 )
        #                 break
    
        #             if attempt < MAX_RETRIES:
        #                 logger.info(
        #                     "No data yet for interval %s; "
        #                     "retrying in %s seconds (attempt %s/%s)",
        #                     interval,
        #                     WAIT_SECONDS,
        #                     attempt,
        #                     MAX_RETRIES,
        #                 )
        #                 time.sleep(WAIT_SECONDS)
    
        #         if records:
        #             logger.info("Ingesting %s records", len(records))
        #             self.ingest(client, records)
        #         else:
        #             logger.warning(
        #                 "Giving up on interval %s after %s attempts",
        #                 interval,
        #                 MAX_RETRIES,
        #             )
    
        # self.trigger_dbt(tag="forecast_arome")

        
        # if DatabaseRepository.forecast_run_already_ingested(params.get("referencetime"), self.data_base_target_table):
        #     self._log_skip(f"Forecast run {params.get("referencetime")} already ingested   skipping")
        # else:
        #     parameters = copy.deepcopy(params)       
        #     for value in params.get("time"):
        #         parameters['time'] = value 
        #         logger.info(f"Fetching data for the forecast run time: {run_time} and forecast time: {value}")
        #         records = self.fetch(parameters)
        #         if records:
        #             logger.info(f"Ingesting the data obtained with {len(records)} stations")
        #             self.ingest(records)  
        #         else:
        #             logger.info(f"No data to ingest for forecast run time: {run_time} and forecast time: {value}")    
        #     self.trigger_dbt(tag = "forecast")


    # def run_loop(self):
    #     """Start continuous ingestion loop"""
    #     self.running = True
    #     logger.info("Real-time ingestor started")
    #     while self.running:
    #         self.run_once()
    #         time.sleep(self.update_frequency)