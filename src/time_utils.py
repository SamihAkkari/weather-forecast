from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
PARIS = ZoneInfo("Europe/Paris")

_TRUNCATE = {
    "day": {"hour": 0, "minute": 0, "second": 0, "microsecond": 0},
    "hour": {"minute": 0, "second": 0, "microsecond": 0},
    "minute": {"second": 0, "microsecond": 0},
    "second": {"microsecond": 0},
}


def utc_now_truncated(to: str = "minute") -> datetime:
    if to not in _TRUNCATE:
        raise ValueError(f"'to' must be one of {sorted(_TRUNCATE)}")
    return datetime.now(timezone.utc).replace(**_TRUNCATE[to])


def to_iso(dt: datetime) -> str:
    return dt.strftime(ISO_FORMAT)


def from_iso(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def current_utc_iso(truncation: str = "hour") -> str:
    """Current UTC time, e.g. '2026-10-30T14:00:00Z'."""
    return to_iso(utc_now_truncated(truncation))


def current_france_date_iso() -> str:
    return datetime.now(PARIS).date().isoformat()


def last_interval_iso(step_seconds: int, steps_back: int) -> str:
    """Latest multiple of `step_seconds` (UTC), moved back by `steps_back` steps."""
    step_minutes = step_seconds // 60
    now = utc_now_truncated("minute")
    floored = now - timedelta(minutes=now.minute % step_minutes)
    return to_iso(floored - timedelta(minutes=step_minutes * steps_back))
