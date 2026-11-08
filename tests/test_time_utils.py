import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from src import time_utils


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 8, 12, 17, 43, tzinfo=timezone.utc)


class TimeUtilsTests(unittest.TestCase):
    def test_truncates_utc_datetime_to_requested_precision(self):
        with patch("src.time_utils.datetime", FrozenDateTime):
            self.assertEqual(
                time_utils.utc_now_truncated("day"),
                datetime(2026, 11, 8, tzinfo=timezone.utc),
            )
            self.assertEqual(
                time_utils.utc_now_truncated("hour"),
                datetime(2026, 11, 8, 12, tzinfo=timezone.utc),
            )
            self.assertEqual(
                time_utils.utc_now_truncated("minute"),
                datetime(2026, 11, 8, 12, 17, tzinfo=timezone.utc),
            )
            self.assertEqual(
                time_utils.utc_now_truncated("second"),
                datetime(2026, 11, 8, 12, 17, 43, tzinfo=timezone.utc),
            )

    def test_rejects_unknown_truncation(self):
        with self.assertRaisesRegex(ValueError, "day"):
            time_utils.utc_now_truncated("week")

    def test_iso_conversion_round_trips_utc_datetime(self):
        value = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)

        self.assertEqual(time_utils.to_iso(value), "2026-11-08T12:00:00Z")
        self.assertEqual(time_utils.from_iso("2026-11-08T12:00:00Z"), value)

    def test_last_interval_floors_and_steps_back(self):
        with patch("src.time_utils.datetime", FrozenDateTime):
            self.assertEqual(
                time_utils.last_interval_iso(360, 2),
                "2026-11-08T12:00:00Z",
            )
            self.assertEqual(
                time_utils.last_interval_iso(3600, 1),
                "2026-11-08T11:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
