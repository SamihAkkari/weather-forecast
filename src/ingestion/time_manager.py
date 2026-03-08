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
    
    def last_arome_forecast_run_time():
        now = TimeManager.utc_now()
        for update_time in reversed(Config.AROME_FORECAST_UPDATE_TIMES):           
            update_dt = datetime.strptime(update_time, "%H:%M:%S").time()
            candidate_dt = datetime.combine(now.date(), update_dt, tzinfo=timezone.utc)
            if candidate_dt <= now:
                return candidate_dt
        # If no update time is before now, return the last one from yesterday
        last_update_time = Config.AROME_FORECAST_UPDATE_TIMES[-1]
        last_update_dt = datetime.strptime(last_update_time, "%H:%M:%S").time()
        return datetime.combine(now.date() - timedelta(days=1), last_update_dt, tzinfo=timezone.utc)

    def last_arome_forecast_run_time_iso():
        return TimeManager.last_arome_forecast_run_time().strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )