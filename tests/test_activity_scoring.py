import math
import unittest

from src.forecast.activities.activity_config import ACTIVITIES_CFG
from src.forecast.activities.activity_scoring import DEFAULT_SCORE, MessageBand, Scorer, interpolate


class ActivityScoringTests(unittest.TestCase):
    def test_interpolation_clamps_and_interpolates(self):
        points = ((0.0, 0.0), (10.0, 1.0))

        self.assertEqual(interpolate(-1.0, points), 0.0)
        self.assertEqual(interpolate(5.0, points), 0.5)
        self.assertEqual(interpolate(11.0, points), 1.0)
        self.assertEqual(interpolate(float("nan"), points), DEFAULT_SCORE)

    def test_score_selects_messages_at_exclusive_and_inclusive_boundaries(self):
        scorer = Scorer(
            points=((0.0, 0.0), (10.0, 1.0)),
            messages=(
                MessageBand(5.0, "low: {v:.1f}"),
                MessageBand(10.0, "middle: {v:.1f}", inclusive=True),
                MessageBand(math.inf, "high: {v:.1f}"),
            ),
            unknown="unknown",
        )

        self.assertEqual(Scorer(None), (DEFAULT_SCORE, "unknown"))
        self.assertAlmostEqual(Scorer(4.9)[0], 0.49)
        self.assertEqual(Scorer(4.9)[1], "low: 4.9")
        self.assertEqual(Scorer(5.0), (0.5, "middle: 5.0"))
        self.assertEqual(Scorer(10.0), (1.0, "middle: 10.0"))
        self.assertEqual(Scorer(10.1), (1.0, "high: 10.1"))

    def test_Scorer_rejects_invalid_points_and_message_limits(self):
        with self.assertRaisesRegex(ValueError, "increasing values"):
            Scorer(
                points=((0.0, 0.0), (0.0, 1.0)),
                messages=(MessageBand(math.inf, "message"),),
            )

        with self.assertRaisesRegex(ValueError, "infinite upper limit"):
            Scorer(
                points=((0.0, 0.0), (1.0, 1.0)),
                messages=(MessageBand(1.0, "message"),),
            )

    def test_cycling_wind_message_uses_aligned_eight_meters_threshold(self):
        scorer = ACTIVITIES_CFG["cycling"]["parameters"]["wind"].scorer

        self.assertIn("moderate breeze", scorer(7.99)[1])
        self.assertIn("fresh breeze", scorer(8.0)[1])

    def test_driving_wind_keeps_kilometers_per_hour_in_message(self):
        scorer = ACTIVITIES_CFG["driving"]["parameters"]["wind"].scorer

        self.assertIn("72 km/h", scorer(20.0)[1])


if __name__ == "__main__":
    unittest.main()
