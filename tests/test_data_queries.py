import unittest
from datetime import datetime
from unittest.mock import patch

from src.data import queries
from src.data.models import SilverObservationListeStationsRecords as Station


class DataQueriesTests(unittest.TestCase):
    def setUp(self):
        queries._stations_cache = None

    def test_observations_at_serializes_timestamps(self):
        timestamp = datetime(2026, 11, 8, 12)
        rows = [{"station_id": "01014002", "time_step_fr": timestamp}]

        with patch("src.data.queries.fetch_dicts", return_value=rows) as fetch:
            result = queries.get_observations_at("01014002", "2026-11-08T12:00:00Z")

        self.assertEqual(
            result,
            [{"station_id": "01014002", "time_step_fr": "2026-11-08T12:00:00"}],
        )
        self.assertIn("time_step_fr = %s", fetch.call_args.args[0])
        self.assertEqual(
            fetch.call_args.args[1], ("01014002", "2026-11-08T12:00:00Z")
        )

    def test_observations_for_day_uses_inclusive_start_and_exclusive_end(self):
        with patch("src.data.queries.fetch_dicts", return_value=[]) as fetch:
            result = queries.get_observations_for_day("01014002", "2026-11-08")

        self.assertEqual(result, [])
        self.assertIn("time_step_fr >= %s AND time_step_fr < %s", fetch.call_args.args[0])
        self.assertEqual(
            fetch.call_args.args[1],
            (
                "01014002",
                datetime(2026, 11, 8),
                datetime(2026, 11, 9),
            ),
        )

    def test_forecast_queries_use_latest_run_per_time_step(self):
        with patch("src.data.queries.fetch_dicts", return_value=[]) as fetch:
            queries.get_forecasts_after("01014002", "2026-11-08T12:00:00Z")

        sql, params = fetch.call_args.args
        self.assertIn("DISTINCT ON (station_id, time_step_fr)", sql)
        self.assertIn("time_step_fr > %s", sql)
        self.assertIn("ORDER BY station_id, time_step_fr, run_time DESC", sql)
        self.assertEqual(params, ("01014002", "2026-11-08T12:00:00Z"))

    def test_stations_are_built_by_column_name_and_cached(self):
        row = {
            "station_id": "01014002",
            "department_id": "75",
            "location_name": "paris",
            "latitude": 48.8,
            "longitude": 2.3,
            "altitude": 35.0,
            "openning_date": datetime(2000, 1, 1),
            "station_type": "automatic",
            "transfer_time_fr": datetime(2026, 11, 8),
        }
        queries._stations_cache = None

        with (
            patch("src.data.queries.fetch_dicts", return_value=[row]) as fetch,
            patch("src.data.queries.time.monotonic", return_value=100.0),
        ):
            stations = queries.get_stations()
            cached_stations = queries.get_stations()

        self.assertEqual(stations, [Station(**row)])
        self.assertIs(cached_stations, stations)
        fetch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
