"""
WMO Weather Interpretation Code computation.

This script is dapted from the open-meteo implementation:
https://github.com/open-meteo/open-meteo/blob/main/Sources/App/Helper/WeatherCode.swift

Variables used from AROME forecast:
    precipitation_mm      : accumulated precipitation for the timestep (mm)
    snow_precipitation_mm : total snow precipitation (mm water equivalent)
    cape_m2_s2            : CAPE instantaneous (J/kg)
    total_cloud_cover     : total cloud cover (%)
    temperature_celsius   : 2m temperature (°C)
    wind_gust_m_per_s     : 10m wind gust (m/s) optional, used for thunderstorm

Variables NOT available from meteofrance that open-meteo uses (skipped in this implementation):
    categoricalFreezingRain  → freezing rain codes (56, 57, 66, 67) skipped
    visibilityMeters         → fog codes (45, 48) skipped
    liftedIndex              → thunderstorm probability degraded
    convectiveInhibition     → thunderstorm probability degraded
    pblHeight                → thunderstorm probability degraded
    convectivePrecipitation  → we use cape >= 800 as proxy instead

Snow detection:
    tsnowp is in mm water equivalent.
    open-meteo uses snowfall in centimeters of snow depth.
    Conversion: 1 mm water equivalent ≈ 1 cm snow depth (density ~100 kg/m³)
    This is an approximation — fresh snow density varies.
"""

from __future__ import annotations
import math

# {
# 	"0": "Clear sky",
# 	"1": "Mainly clear",
# 	"2": "Partly cloudy",
# 	"3": "Overcast",
# 	"45": "Fog",
# 	"48": "Depositing rime fog",
# 	"51": "Light drizzle",
# 	"53": "Moderate drizzle",
# 	"55": "Dense drizzle",
# 	"56": "Light freezing drizzle",
# 	"57": "Dense freezing drizzle",
# 	"61": "Slight rain",
# 	"63": "Moderate rain",
# 	"65": "Heavy rain",
# 	"66": "Light freezing rain",
# 	"67": "Heavy freezing rain",
# 	"71": "Slight snowfall",
# 	"73": "Moderate snowfall",
# 	"75": "Heavy snowfall",
# 	"77": "Snow grains",
# 	"80": "Slight rain showers",
# 	"81": "Moderate rain showers",
# 	"82": "Violent rain showers",
# 	"85": "Slight snow showers",
# 	"86": "Heavy snow showers",
# 	"95": "Thunderstorm",
# 	"96": "Thunderstorm with slight hail",
# 	"97": "Heavy thunderstorm",
# 	"99": "Thunderstorm with heavy hail"
# }

# ── Model timestep ─────────────────────────────────────────────────────────────
# AROME SP1 package timestep is 1 hour.
# All thresholds from open-meteo are in per-hour rates,
# so dividing by MODEL_DT_HOURS gives the hourly rate.
MODEL_DT_HOURS: float = 1.0


# ── Guard ──────────────────────────────────────────────────────────────────────

def _ok(*values) -> bool:
    """True if all values are not None and finite."""
    return all(v is not None and math.isfinite(float(v)) for v in values)


# ── Thunderstorm ───────────────────────────────────────────────────────────────

def _thunderstorm_probability(
    cape: float,
    precip: float,
    cloud_cover: float,
    gusts: float | None,
) -> float:
    """
    Simplified version of open-meteo calculateThunderstormProbability.
    We drop CIN, LiftedIndex and PBL since we don't have them.
    Without those terms the weights are renormalized automatically
    because we track accumulatedScore / totalWeight.
    """

    # Hard blockers — same as open-meteo
    if cape <= 10.0:
        return 0.0
    if cloud_cover < 30.0:
        return 0.0

    accumulated = 0.0
    total_weight = 0.0

    # CAPE score (weight 0.25 in open-meteo)
    cape_weight = 0.25
    cape_score = max(0.0, min((cape - 300.0) / (2500.0 - 300.0), 1.0))
    accumulated += cape_score * cape_weight
    total_weight += cape_weight

    # Precipitation score (weight 0.25 in open-meteo)
    # Without convective precip field we use total precip with a 0.6 penalty
    precip_weight = 0.25
    reference_precip = 2.0 * MODEL_DT_HOURS  # 2 mm/h reference
    fallback_reference = reference_precip * 1.6
    precip_score = max(0.0, min(precip / fallback_reference, 1.0))
    accumulated += precip_score * precip_weight * 0.6
    total_weight += precip_weight * 0.6

    # Gust score (weight 0.075 in open-meteo)
    if _ok(gusts):
        gust_weight = 0.075
        gust_score = max(0.0, min((gusts - 5.0) / 13.0, 1.0))
        accumulated += gust_score * gust_weight
        total_weight += gust_weight

    probability = (accumulated / total_weight) * 100.0

    # Cloud cover dampening
    if cloud_cover >= 60.0:
        cloud_factor = 1.0
    else:
        cloud_factor = 0.6 + 0.4 * ((cloud_cover - 30.0) / 30.0)
    probability *= cloud_factor

    return max(0.0, min(probability, 100.0))


# ── Main function ──────────────────────────────────────────────────────────────

def compute_hourly_code(entry: dict) -> int:
    """
    Assigns a WMO weather code to a single forecast timestep.

    Logic follows open-meteo WeatherCode.calculate() order:
        1. Thunderstorm
        2. (Freezing rain — skipped, no data)
        3. Convective snow showers
        4. Rain showers (convective)
        5. Stratiform snowfall
        6. Stratiform rain / drizzle
        7. (Fog — skipped, no visibility data)
        8. Cloud cover
    """

    precip    = entry.get("precipitation_mm")     # mm accumulated
    tsnowp    = entry.get("tsnowp")               # mm water eq. accumulated
    cape      = entry.get("cape_m2_s2")
    cloud     = entry.get("total_cloud_cover")    # %
    temp      = entry.get("temperature_celsius")  # °C
    gusts     = entry.get("fg10")                 # m/s, optional

    # Hourly rates (open-meteo normalises everything to per-hour)
    precip_rate = precip / MODEL_DT_HOURS if _ok(precip) else None
    # tsnowp is mm water eq. → treat as cm snow depth (density ≈ 100 kg/m³)
    snow_rate   = tsnowp / MODEL_DT_HOURS if _ok(tsnowp) else None

    # ── 1. Thunderstorm ────────────────────────────────────────────────────
    if _ok(cape, precip, cloud):
        prob = _thunderstorm_probability(cape, precip, cloud, gusts)
        if prob > 85:
            return 96   # thunderstorm strong
        if prob > 60:
            return 95   # thunderstorm slight or moderate

    # ── 2. Freezing rain — skipped (no categoricalFreezingRain) ───────────

    # ── 3 & 4. Convective precipitation — showers ─────────────────────────
    # open-meteo condition: convectivePrecipitation > 0 OR cape >= 800
    # We use cape >= 800 as proxy since we have no convective precip field
    is_convective = _ok(cape) and cape >= 800

    if is_convective:
        # Convective snow showers
        if _ok(snow_rate):
            if 0.01 <= snow_rate < 0.2:
                return 85   # slight snow showers
            if snow_rate >= 0.2:
                return 86   # heavy snow showers

        # Convective rain showers
        if _ok(precip_rate):
            if 1.3 <= precip_rate < 2.5:
                return 80   # slight rain showers
            if 2.5 <= precip_rate < 7.6:
                return 81   # moderate rain showers
            if precip_rate >= 7.6:
                return 82   # violent rain showers

    # ── 5. Stratiform snowfall ─────────────────────────────────────────────
    if _ok(snow_rate):
        if 0.01 <= snow_rate < 0.2:
            return 71   # slight snowfall
        if 0.2 <= snow_rate < 0.8:
            return 73   # moderate snowfall
        if snow_rate >= 0.8:
            return 75   # heavy snowfall

    # ── 6. Stratiform rain / drizzle ──────────────────────────────────────
    # open-meteo thresholds (mm/h):
    # 0.01–0.5  → drizzle light
    # 0.5–1.0   → drizzle moderate
    # 1.0–1.3   → drizzle dense
    # 1.3–2.5   → light rain
    # 2.5–7.6   → moderate rain
    # 7.6+      → heavy rain
    if _ok(precip_rate):
        if 0.01 <= precip_rate < 0.5:
            return 51   # light drizzle
        if 0.5 <= precip_rate < 1.0:
            return 53   # moderate drizzle
        if 1.0 <= precip_rate < 1.3:
            return 55   # dense drizzle
        if 1.3 <= precip_rate < 2.5:
            return 61   # light rain
        if 2.5 <= precip_rate < 7.6:
            return 63   # moderate rain
        if precip_rate >= 7.6:
            return 65   # heavy rain

    # ── 7. Fog — skipped (no visibility data) ─────────────────────────────

    # ── 8. Cloud cover ─────────────────────────────────────────────────────
    # open-meteo thresholds: 0–20 clear, 20–50 mainly clear,
    # 50–80 partly cloudy, 80+ overcast
    if _ok(cloud):
        if cloud < 20:
            return 0    # clear sky
        if cloud < 50:
            return 1    # mainly clear
        if cloud < 80:
            return 2    # partly cloudy
        return 3        # overcast

    # Fallback if no data at all
    return 0


def compute_daily_code(entries: list[dict]) -> int:
    """
    Returns the most severe WMO code across all hourly entries of a day.
    Severity order mirrors open-meteo: thunderstorm > showers > snow > rain
    > drizzle > cloudy > clear.
    """
    if not entries:
        return 0

    def severity(code: int) -> int:
        if code >= 95: return 9   # thunderstorm
        if code in (85, 86): return 8  # snow showers
        if code in (80, 81, 82): return 7  # rain showers
        if code in (71, 73, 75, 77): return 6  # snowfall
        if code in (61, 63, 65, 66, 67): return 5  # rain
        if code in (51, 53, 55, 56, 57): return 4  # drizzle
        if code == 45: return 3   # fog
        if code == 3:  return 2   # overcast
        if code == 2:  return 1   # partly cloudy
        return 0

    return max((compute_hourly_code(e) for e in entries), key=severity)