import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import src.forecast.activities.activity_recommendations as recommendations
from src.forecast.activities.activity_recommendations import ACTIVITIES_CFG, build_activity


class ActivityRecommendationsTests(unittest.TestCase):
    def setUp(self):
        self.current = {
            "time_step_fr": "2026-11-08T10:00:00Z",
            "temperature_celsius": 17.5,
            "wind_speed_m_per_s": 3.2,
            "wind_gust_m_per_s": 7.1,
            "precipitation_mm": 0.0,
            "snow_precipitation_mm": 0.0,
            "total_cloud_cover": 20.0,
            "humidity_percentage": 60.0,
        }
        start = datetime(2026, 11, 8, 10, tzinfo=timezone.utc)
        self.forecast = [
            {
                **self.current,
                "time_step_fr": (start + timedelta(hours=hour)).isoformat(),
            }
            for hour in range(50)
        ]

    def test_builds_recommendations_for_configured_activities(self):
        for activity in ACTIVITIES_CFG:
            with self.subTest(activity=activity):
                result = build_activity(self.current, self.forecast, activity)
                self.assertEqual(result["id"], activity)
                self.assertEqual(len(result["hourly"]), 48)
                self.assertEqual(
                    set(result),
                    {
                        "id",
                        "icon",
                        "label",
                        "status",
                        "message",
                        "current_status",
                        "best_window",
                        "hourly",
                    },
                )

    def test_best_window_is_limited_to_forecast_horizon(self):
        result = build_activity(self.current, self.forecast, "cycling")

        self.assertEqual(len(result["best_window"]), 1)
        self.assertEqual(
            result["best_window"][0]["from"],
            self.forecast[0]["time_step_fr"],
        )
        self.assertEqual(
            result["best_window"][0]["to"],
            self.forecast[47]["time_step_fr"],
        )

    def test_scores_each_forecast_hour_once(self):
        with patch.object(
            recommendations,
            "_score_hour",
            wraps=recommendations._score_hour,
        ) as score_hour:
            build_activity(self.current, self.forecast, "cycling")

        self.assertEqual(score_hour.call_count, 49)

    def test_unknown_activity_lists_available_choices(self):
        with self.assertRaisesRegex(ValueError, "cycling"):
            build_activity(self.current, self.forecast, "unknown")


if __name__ == "__main__":
    unittest.main()
