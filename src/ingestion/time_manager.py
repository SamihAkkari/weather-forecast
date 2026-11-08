from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


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
        """Convert an aware datetime to France local time, including DST."""
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
    def current_utc_iso(truncation="hour"):
        """Current real UTC time, e.g. '2026-10-30T14:00:00Z'."""
        return TimeManager.convert_to_iso(TimeManager.utc_now_truncated(to=truncation))

    @staticmethod
    def current_france_date_iso() -> str:
        return datetime.now(ZoneInfo("Europe/Paris")).date().isoformat()