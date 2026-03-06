import time
import logging
from src.config.config import Config
from datetime import datetime, timezone, timedelta
from src.data.repository import DatabaseRepository


    
import tempfile
import numpy as np
import pandas as pd
import cfgrib
import requests


logger = logging.getLogger(__name__)

class TimeManager:
    """Time utilities for ingestion"""

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc)

    @staticmethod
    def utc_now_minute():
        return (
            datetime.now(timezone.utc)
            .replace(second=0, microsecond=0)
        )

    @staticmethod
    def utc_now_iso():
        return TimeManager.utc_now_minute().strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    @staticmethod
    def last_interval_minutes(interval: int = Config.API_INFRAHORAIRE6m_TIME_STEPS, steps_back = 1):
        """
        Floor UTC time to the last multiple of `interval` minutes
        """
        now = TimeManager.utc_now_minute()
        remainder = now.minute % interval
        floored = now - timedelta(minutes=remainder)
        if steps_back > 0:
            floored -= timedelta(minutes=interval * steps_back)
        return floored

    @staticmethod
    def last_interval_iso(interval: int = Config.API_INFRAHORAIRE6m_TIME_STEPS):
        return TimeManager.last_interval_minutes(interval).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    
class RealTimeIngestor:
    """Continuously ingest real-time weather observations"""

    def __init__(self, api_client, interval_seconds=60):
        self.api_client = api_client
        # self.repository = repository
        self.interval = interval_seconds
        self.running = False

    def fetch(self, date):
        """Fetch data from API"""
        try:
            if not DatabaseRepository._this_date_is_already_ingested(date):
                data = self.api_client.get_json(params = {'date': date})  # your API method
                logger.info(f"Fetched {len(data)} stations")
            else:
                data = []
                logger.info(f"The data of date: {date} has already been ingested")
        except Exception as e:
            logger.error(f"Ingestion error: {e}")
        return data

    def ingest(self, data):
        """Ingest the fetched data into the database"""
        try:
            if data != []:
                DatabaseRepository.ingest(data)
                logger.info(f"Ingested {len(data)} stations")
            else:
                logger.info("Empty list data: data have probably not been yet ingested into the API or have already been ingested into the database")
        except Exception as e:
            logger.error(f"Ingestion error: {e}")

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

    def stop(self):
        self.running = False
        logger.info("Ingestor stopped")