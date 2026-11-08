
import math
from dataclasses import dataclass
from typing import NamedTuple

DEFAULT_SCORE = 0.5


class MessageBand(NamedTuple):
    upper_limit: float
    text: str
    inclusive: bool = False


def interpolate(
    value: float,
    points: tuple[tuple[float, float], ...],
) -> float:
    """Interpolate between score points, clamping values beyond the endpoints."""
    if math.isnan(value):
        return DEFAULT_SCORE
    if value <= points[0][0]:
        return points[0][1]

    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if value <= x2:
            return y1 + (value - x1) / (x2 - x1) * (y2 - y1)

    return points[-1][1]


@dataclass(frozen=True)
class Scorer:
    """Map a weather value to an interpolated score and a threshold message."""

    points: tuple[tuple[float, float], ...]
    messages: tuple[MessageBand, ...]
    unknown: str = "Data unavailable"

    def __post_init__(self) -> None:
        if len(self.points) < 2:
            raise ValueError("A scorer requires at least two score points")
        if any(not math.isfinite(value) for value, _ in self.points):
            raise ValueError("Scorer score-point values must be finite")
        if any(right[0] <= left[0] for left, right in zip(self.points, self.points[1:])):
            raise ValueError("Scorer score points must have increasing values")
        if any(not math.isfinite(score) or not 0 <= score <= 1 for _, score in self.points):
            raise ValueError("Scorer scores must be between 0 and 1")
        if not self.messages or self.messages[-1].upper_limit != math.inf:
            raise ValueError("Scorer messages must end with an infinite upper limit")
        if any(not math.isfinite(band.upper_limit) for band in self.messages[:-1]):
            raise ValueError("Only the final Scorer message may have an infinite upper limit")
        if any(
            right.upper_limit <= left.upper_limit
            for left, right in zip(self.messages, self.messages[1:])
        ):
            raise ValueError("Scorer message limits must be increasing")

    def __call__(
        self,
        value: float | int | None,
        **message_values: float,
    ) -> tuple[float, str]:
        if value is None:
            return DEFAULT_SCORE, self.unknown

        numeric_value = float(value)
        score = interpolate(numeric_value, self.points)
        for band in self.messages:
            if numeric_value < band.upper_limit or (
                band.inclusive and numeric_value == band.upper_limit
            ):
                return score, band.text.format(v=value, **message_values)

        return score, self.messages[-1].text.format(v=value, **message_values)
