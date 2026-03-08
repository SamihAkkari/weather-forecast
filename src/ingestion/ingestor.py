import copy
import logging

from src.data.repository import DatabaseRepository
from src.processing.arome_forecast_processor import GribProcessor
from src.processing.observations_processor import ObservationProcessor
from src.ingestion.time_manager import TimeManager

logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
import logging

class BaseIngestor(ABC):
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fetch(self, *args): ...

    @abstractmethod
    def ingest(self, data): ...

    @abstractmethod
    def run_once(self, *args): ...

    def _log_fetch(self, identifier, count):
        self.logger.info(f"Fetched {count} records for {identifier}")

    def _log_ingest(self, identifier, count):
        self.logger.info(f"Ingested {count} records for {identifier}")

    def _log_skip(self, reason):
        self.logger.info(f"Skipped — {reason}")

    def _log_error(self, context, error):
        self.logger.error(f"{context}: {error}")

class ObservationsIngestor(BaseIngestor):
    """Continuously ingest real-time weather observations"""

    def __init__(self, api_client, interval_seconds=60):
        super().__init__(api_client)
        # self.repository = repository
        self.interval = interval_seconds
        self.running = False

    def fetch(self, params):
        """Fetch data from API"""
        try:
            if not DatabaseRepository._this_date_is_already_ingested(params.get("date")):
                response = self.api_client.fetch_data(params = params)  # your API method
                observation_processor = ObservationProcessor(response)
                records = observation_processor.get_ready_to_ingest_records()
                self._log_fetch("observations", len(records))
            else:
                records = []
                self._log_skip(f"The data of date: {params.get("date")} has already been ingested")
        except Exception as e:
            self._log_error("Observations fetching error", e)
            raise
        return records

    def ingest(self, records):
        """Ingest the fetched data into the database"""
        try:
            if records != []:
                DatabaseRepository.insert_observations(records)
                self._log_ingest("observations", len(records))
            else:
                self._log_skip("No new data to ingest")
        except Exception as e:
            self._log_error("Observations ingestion error", e)
            raise

    def run_once(self):
        """This can be used later with advanced schedulers"""
        date = TimeManager.last_interval_iso()
        logger.info(f"Fetching data for the date: {date}")
        data = self.fetch(date)
        logger.info(f"Ingesting the data obtained with {len(data)} stations")
        self.ingest(data)
        
    def run_loop(self):
        """Start continuous ingestion loop"""
        self.running = True
        logger.info("Real-time ingestor started")
        while self.running:
            self.run_once()
            time.sleep(self.interval)

    # def stop(self):
    #     self.running = False
    #     logger.info("Ingestor stopped")


class ForecastIngestor(BaseIngestor):
    """
    Ingest one AROME forecast run per call.
    Trigger externally (cron, scheduler) — this class does not manage timing.
    """

    def __init__(self, api_client):
        super().__init__(api_client)
        self.api_client = api_client

    def fetch(self, params: dict) -> str | None:
        """Download GRIB file to a temp path. Returns path or None on failure."""
        try:       
            response = self.api_client.fetch_data(params = params)  # your API method
            if response:
                grib_processor = GribProcessor(response, params.get("referencetime"))
                records = grib_processor.get_ready_to_ingest_records()
                self._log_fetch("forecast", len(records))
            else:
                records = None
                self._log_skip(f"No GRIB data found for reference time {params.get("referencetime")}")
            return records
        except Exception as e:
            logger.error(f"Fetch error for run {params.get("referencetime")}: {e}")
            raise

    def ingest(self, records: list[dict]) -> None:
        """Insert records into DB."""
        try:
            if records:
                DatabaseRepository.insert_forecasts(records)
                logger.info(f"Ingested {len(records)} forecast records")
            else:
                logger.info("No records to ingest")
        except Exception as e:
            logger.error(f"Ingestion error: {e}")
            raise

    def run_once(self) -> None:
        """This can be used later with advanced schedulers"""
        run_time = TimeManager.last_arome_forecast_run_time_iso()

        params = {
            "referencetime" : "2026-03-08T09:00:00Z",
            "time": ["00H06H", "07H12H", "13H18H", "19H24H", "25H30H", "31H36H", "37H42H", "43H48H", "49H51H"],
            "format": "grib2"
        }

        # params = {
        #     "referencetime" : run_time,
        #     "time": ["00H06H", "07H12H", "13H18H", "19H24H", "25H30H", "31H36H", "37H42H", "43H48H", "49H51H"],
        #     "format": "grib2"
        # }

        if DatabaseRepository.forecast_run_already_ingested(params.get("referencetime")):
            self._log_skip(f"Forecast run {params.get("referencetime")} already ingested — skipping")
        else:
            parameters = copy.deepcopy(params)       
            for value in params.get("time"):
                parameters['time'] = value 
                logger.info(f"Fetching data for the forecast run time: {run_time}")
                records = self.fetch(parameters)
                if records:
                    logger.info(f"Ingesting the data obtained with {len(records)} stations")
                    self.ingest(records)   
                else:
                    logger.info(f"No data to ingest for forecast run time: {run_time} and forecast time: {value}")     