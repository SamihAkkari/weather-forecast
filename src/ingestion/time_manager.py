import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

class TimeManager:
    """Time utilities for ingestion"""

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc)
    
    @staticmethod
    def utc_truncated(_time, to="minute"):
        if to == "day":
            return _time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif to == "hour":
            return _time.replace(minute=0, second=0, microsecond=0)
        elif to == "minute":
            return _time.replace(second=0, microsecond=0)
        elif to == "second":
            return _time.replace(microsecond=0)
        else:
            raise ValueError("Invalid value for 'to'. Use: 'hour', 'minute', or 'second'")

    @staticmethod
    def utc_to_france(dt: datetime) -> datetime:
        """
        Convert a UTC datetime to France local time (handles DST automatically).
        """
        if dt.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware (UTC)")

        return dt.astimezone(ZoneInfo("Europe/Paris"))

    def utc_now_truncated(to="minute"):
        now = datetime.now(timezone.utc)
        if to == "day":
            return TimeManager.utc_truncated(now, to="day")
        elif to == "hour":
            return TimeManager.utc_truncated(now, to="hour")
        elif to == "minute":
            return TimeManager.utc_truncated(now, to="minute")
        elif to == "second":
            return TimeManager.utc_truncated(now, to="second")
        else:
            raise ValueError("Invalid value for 'to'. Use: 'hour', 'minute', or 'second'")


    # @staticmethod
    # def utc_now_minute():
    #     return (
    #         datetime.now(timezone.utc)
    #         .replace(second=0, microsecond=0)
    #     )

    # @staticmethod
    # def utc_now_iso():
    #     return TimeManager.utc_now_minute().strftime(
    #         "%Y-%m-%dT%H:%M:%SZ"
    #     )

    @staticmethod
    def last_interval_minutes(time_step, steps_back):
        """
        Floor UTC time to the last multiple of `time_step` minutes
        """
        now = TimeManager.utc_now_truncated(to="minute")
        remainder = now.minute % time_step
        floored = now - timedelta(minutes=remainder)
        if steps_back > 0:
            floored -= timedelta(minutes=time_step * steps_back)
        return floored

    @staticmethod
    def last_interval_iso(time_step: int, steps_back: int):
        return TimeManager.last_interval_minutes(time_step/60, steps_back).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    
    @staticmethod
    def convert_iso_datetime(time_iso):
        return datetime.fromisoformat(time_iso.replace("Z", "+00:00"))

    @staticmethod
    def convert_to_iso(time):
        return time.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    @staticmethod
    def current_france_time_iso(time_truncation = "hour"):
        time = TimeManager.utc_now_truncated(to=time_truncation)
        time = TimeManager.utc_to_france(time)
        time = TimeManager.convert_to_iso(time)
        return time

    @staticmethod
    def get_time_before(days):
        now_utc = TimeManager.utc_now_truncated(to="hour")
        now_france = TimeManager.utc_to_france(now_utc)
        fr_time_before_specified_days = now_france - timedelta(days=days)
        return fr_time_before_specified_days 




    # def last_arome_forecast_run_time():
    #     now = TimeManager.utc_now()
    #     for update_time in reversed(Config.AROME_FORECAST_UPDATE_TIMES):           
    #         update_dt = datetime.strptime(update_time, "%H:%M:%S").time()
    #         candidate_dt = datetime.combine(now.date(), update_dt, tzinfo=timezone.utc)
    #         if candidate_dt <= now:
    #             return candidate_dt
    #     # If no update time is before now, return the last one from yesterday
    #     last_update_time = Config.AROME_FORECAST_UPDATE_TIMES[-1]
    #     last_update_dt = datetime.strptime(last_update_time, "%H:%M:%S").time()
    #     return datetime.combine(now.date() - timedelta(days=1), last_update_dt, tzinfo=timezone.utc)

    # def last_arome_forecast_run_time_iso():
    #     return TimeManager.last_arome_forecast_run_time().strftime(
    #         "%Y-%m-%dT%H:%M:%SZ"
    #     )
    
    # def last_arome_forecast_run_time(href):
    #     parsed = urlparse(href)
    #     query = parse_qs(parsed.query)
    #     reference_time = query["referencetime"][0]
    #     return reference_time