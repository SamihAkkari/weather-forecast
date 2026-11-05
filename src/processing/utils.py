from src.data.getter import DatabaseGetter
import logging

from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError,
    Timeout,
    HTTPError,
)

logger = logging.getLogger(__name__)

# ── Activity helpers ───────────────────────────────────────────────────────────

def _activity_representative_score(scores: list[float]) -> float:
    return min(scores)

def _activity_status(scores: list[float]) -> str:
    """
    Combines multiple parameter scores into one overall status.
    The weakest parameter drives the overall status   a chain is only
    as strong as its weakest link. This matches how real conditions work:
    perfect temperature doesn't help if it's pouring rain.
    """
    if isinstance(scores, list):
        representative_score = _activity_representative_score(scores)
    elif isinstance(scores, float):
        representative_score  = scores
    else:
        logger.error("To get the activity status, the score passed need to be either a list of floats or a float")
        raise
    return _status(representative_score)

def _param(score: float, status: str, description: str) -> dict:
    return {"score": score, "status": status, "description": description}

def _status(score: float) -> str:
    if score >= 0.9: return "dark_green"
    if score >= 0.8: return "green"
    if score >= 0.7: return "light_green"
    if score >= 0.6: return "yellow_green"
    if score >= 0.5: return "yellow"
    if score >= 0.4: return "yellow_orange"
    if score >= 0.3: return "orange"
    if score >= 0.2: return "dark_orange"
    if score >= 0.1: return "red"
    return "dark_red"

# ── Per-variable scorers ───────────────────────────────────────────────────────
# Each returns (score, description) using actual values in the message.


def _interpolate_score(value, points, default=0.5):
    """
    Linearly interpolate a score between reference points.

    points: ordered list of (input_value, score) pairs.
    Values outside the range are clamped to endpoint scores.
    """
    if value is None:
        return default

    if value <= points[0][0]:
        return points[0][1]

    if value >= points[-1][0]:
        return points[-1][1]

    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 <= value <= x2:
            ratio = (value - x1) / (x2 - x1)
            return y1 + ratio * (y2 - y1)

    return default


# ============================================================
# CYCLING
# ============================================================

def _score_temp_cycling(t):
    points = [(-5, 0.0), (2, 0.1), (7, 0.4), (10, 0.7), (14, 1.0), (28, 1.0), (33, 0.5), (38, 0.2)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < 2:         msg = f"{t:.1f}°C   dangerously cold for cycling, risk of ice"
    elif t < 7:         msg = f"{t:.1f}°C   cold, dress in thermal layers"
    elif t < 10:        msg = f"{t:.1f}°C   cool, arm warmers recommended"
    elif t <= 28:       msg = f"{t:.1f}°C   comfortable cycling temperature"
    elif t <= 33:       msg = f"{t:.1f}°C   warm, carry extra water"
    else:               msg = f"{t:.1f}°C   too hot, risk of heat exhaustion"

    return score, msg


def _score_wind_cycling(w):
    points = [(3.4, 1.0), (5.5, 0.8), (8.0, 0.7), (10.8, 0.5), (13.9, 0.2), (14, 0.0)]
    score = _interpolate_score(w, points)

    if w is None:     msg = "Wind unknown"
    elif w < 3.4:       msg = f"{w:.0f} m/s   light breeze or calmer, easy riding"
    elif w < 5.5:      msg = f"{w:.0f} m/s   gentle breeze, slight resistance on open roads"
    elif w < 8.8:      msg = f"{w:.0f} m/s   moderate breeze, noticeable resistance on open roads"
    elif w < 10.8:      msg = f"{w:.0f} m/s   fresh breeze, hard going into the wind"
    elif w < 13.9:      msg = f"{w:.0f} m/s   strong breeze, very tiring, handling affected"
    else:               msg = f"{w:.0f} m/s   near gale or stronger, dangerous for cycling"

    return score, msg

def _score_gust_cycling(g):
    points = [(11.0, 1.0), (14.0, 0.7), (17.0, 0.4), (21.0, 0.2), (22.0, 0.0)]
    score = _interpolate_score(g, points)

    if g is None:     msg = "Gust unknown"
    elif g < 11.0:       msg = f"{g:.0f} m/s   light gusts, no concern"
    elif g < 14.0:      msg = f"{g:.0f} m/s   moderate gusts, gusts may unsettle the bike"
    elif g < 17.0:      msg = f"{g:.0f} m/s   strong gusts, risky on exposed roads"
    elif g < 21.0:      msg = f"{g:.0f} m/s   very strong gusts, very risky, avoid exposed roads"
    else:               msg = f"{g:.0f} m/s   extreme gusts, dangerous, do not cycle"

    return score, msg


def _score_rain_cycling(p):
    points = [(0.1, 1.0), (1.3, 0.6), (2.5, 0.4), (7.6, 0.2), (8.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:        msg = "Dry   good grip on roads"
    elif p < 1.3:       msg = f"{p:.1f} mm   drizzle, damp roads"
    elif p < 2.5:       msg = f"{p:.1f} mm   light rain, longer braking distances"
    elif p < 7.6:       msg = f"{p:.1f} mm   moderate rain, wet roads, reduced grip and visibility"
    else:               msg = f"{p:.1f} mm   heavy rain, unsafe to ride"

    return score, msg


def _score_snow_cycling(s):
    points = [(0.0, 1.0), (0.05, 1.0), (0.12, 0.3), (0.5, 0.1), (1.0, 0.0)]
    score = _interpolate_score(s, points)

    if s is None or s < 0.05: msg = "No snowfall"
    elif s < 0.12:            msg = f"{s:.1f} mm light snow   slippery roads, extreme caution"
    elif s<0.5:             msg = f"{s:.1f} mm moderate snow   slippery and poor visibility"
    else:                    msg = f"{s:.1f} mm snow   do not cycle, roads dangerous"

    return score, msg


# ============================================================
# RUNNING
# ============================================================

def _score_temp_running(t):
    points = [(-10, 0.0), (-5, 0.1), (0, 0.3), (5, 0.6), (8, 1.0), (18, 1.0), (24, 0.7), (30, 0.4), (35, 0.1)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < -5:        msg = f"{t:.0f}°C   extreme cold, risk of hypothermia"
    elif t < 0:         msg = f"{t:.0f}°C   freezing, icy paths likely"
    elif t < 5:         msg = f"{t:.0f}°C   cold, warm up thoroughly"
    elif t < 18:        msg = f"{t:.0f}°C   ideal running temperature"
    elif t < 24:        msg = f"{t:.0f}°C   warm, hydrate well"
    elif t < 30:        msg = f"{t:.0f}°C   hot, reduce your pace and carry water"
    else:               msg = f"{t:.0f}°C   dangerous heat, avoid running outdoors"

    return score, msg


def _score_wind_running(w):
    points = [(3.4, 1.0), (5.5, 1.0), (8.0, 0.8), (10.8, 0.5), (13.9, 0.3), (14.0, 0.1)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 3.4:       msg = f"{w:.0f} m/s    light breeze or calmer: no effect"
    elif w < 5.5:       msg = f"{w:.0f} m/s    gentle breeze: little effect"
    elif w < 8.0:       msg = f"{w:.0f} m/s    moderate breeze: noticeable on exposed sections"
    elif w < 10.8:      msg = f"{w:.0f} m/s    fresh breeze: slows you down"
    elif w < 13.9:      msg = f"{w:.0f} m/s    strong breeze: hard going"
    else:               msg = f"{w:.0f} m/s    near gale or stronger: not recommended"

    return score, msg


def _score_rain_running(p):
    points = [(0.1, 1.0), (1.3, 0.7), (2.5, 0.5), (7.6, 0.3), (8.0, 0.1)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: good conditions"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: a light waterproof helps"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: wet, slippery paths"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: poor visibility, slippery"
    else:               msg = f"{p:.1f} mm/h   heavy rain: not recommended"

    return score, msg


# ============================================================
# HIKING
# ============================================================

def _score_temp_hiking(t):
    points = [(-15, 0.0), (-10, 0.1), (0, 0.4), (5, 0.6), (8, 1.0), (22, 1.0), (28, 0.6), (34, 0.2)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < -10:       msg = f"{t:.0f}°C   extreme cold, dangerous at altitude"
    elif t < 0:         msg = f"{t:.0f}°C   freezing, pack warm layers (and crampons in the mountains)"
    elif t < 5:         msg = f"{t:.0f}°C   cold, thermal layers essential"
    elif t < 22:        msg = f"{t:.0f}°C   ideal hiking temperature"
    elif t < 28:        msg = f"{t:.0f}°C   warm, carry at least 2 L of water"
    else:               msg = f"{t:.0f}°C   too hot for strenuous hiking"

    return score, msg


def _score_wind_hiking(w):
    points = [(3.4, 1.0), (5.5, 1.0), (8.0, 1.0), (10.8, 0.7), (13.9, 0.4), (14.0, 0.1)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 3.4:       msg = f"{w:.0f} m/s    light breeze or calmer, comfortable"
    elif w < 5.5:       msg = f"{w:.0f} m/s    gentle breeze, comfortable"
    elif w < 8.0:       msg = f"{w:.0f} m/s    moderate breeze, comfortable"
    elif w < 10.8:      msg = f"{w:.0f} m/s    fresh breeze, breezy on open terrain"
    elif w < 13.9:      msg = f"{w:.0f} m/s    take care on ridges and exposed terrain"
    else:               msg = f"{w:.0f} m/s    dangerous on exposed terrain"

    return score, msg

def _score_gust_hiking(g):
    points = [(11.0, 1.0), (14.0, 0.8), (17.0, 0.5), (21.0, 0.2), (22.0, 0.0)]
    score = _interpolate_score(g, points)

    if g is None:     msg = "Gust unknown"
    elif g < 11.0:       msg = f"{g:.0f} m/s   light gusts, no concern"
    elif g < 14.0:      msg = f"{g:.0f} m/s   moderate gusts, gusty on ridges"
    elif g < 17.0:      msg = f"{g:.0f} m/s   strong gusts, take care on ridges"
    elif g < 21.0:      msg = f"{g:.0f} m/s   very strong gusts, dangerous on exposed terrain"
    else:               msg = f"{g:.0f} m/s   do not hike on ridges"

    return score, msg

def _score_rain_hiking(p):
    points = [(0.1, 1.0), (1.3, 0.7), (2.5, 0.5), (7.6, 0.3), (8.0, 0.1)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: good trail conditions"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: trails getting damp"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: slippery trails"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: slippery trails, reduced visibility"
    else:               msg = f"{p:.1f} mm/h   heavy rain: avoid exposed trails"

    return score, msg


def _score_snow_hiking(s):
    points = [(0.0, 1.0), (0.05, 1.0), (0.12, 0.5), (0.5, 0.2), (1.0, 0.0)]
    score = _interpolate_score(s, points)

    if s is None or s < 0.05: msg = "No snowfall"
    elif s < 0.2:              msg = f"{s:.1f} mm/h snow (water eq.)   light snow: paths may be icy"
    elif s < 0.8:              msg = f"{s:.1f} mm/h snow (water eq.)   moderate snow: paths treacherous"
    else:                      msg = f"{s:.1f} mm/h snow (water eq.)   heavy snow: do not hike"

    return score, msg


# ============================================================
# PICNIC
# ============================================================

def _score_wind_picnic(w):
    points = [(3.4, 1.0), (5.5, 0.8), (8.0, 0.5), (10.8, 0.2), (13.9, 0.0), (14.0, 0.0)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 3.4:       msg = f"{w:.0f} m/s    light breeze or calmer: ideal"
    elif w < 5.5:       msg = f"{w:.0f} m/s    gentle breeze: pleasant, light items may move"
    elif w < 8.0:       msg = f"{w:.0f} m/s    moderate breeze: napkins and light items will blow away"
    elif w < 10.8:      msg = f"{w:.0f} m/s    fresh breeze: uncomfortable outdoors"
    elif w < 13.9:      msg = f"{w:.0f} m/s    strong breeze: too windy"
    else:               msg = f"{w:.0f} m/s    near gale or stronger: too windy"

    return score, msg


def _score_temp_picnic(t):
    points = [(0, 0.0),(5, 0.15),(10, 0.45),(13, 0.65),(18, 0.9),(22, 1.0),(26, 1.0),(30, 0.7),(34, 0.35),(38, 0.1)]
    score = _interpolate_score(t, points)

    if t is None:
        msg = "Temperature unknown"
    elif t < 5:
        msg = f"{t:.0f}°C   too cold for a comfortable picnic"
    elif t < 10:
        msg = f"{t:.0f}°C   chilly, bring warm clothes and a blanket"
    elif t < 15:
        msg = f"{t:.0f}°C   cool but pleasant in sunshine"
    elif t < 26:
        msg = f"{t:.0f}°C   ideal temperature for a picnic"
    elif t < 30:
        msg = f"{t:.0f}°C   warm, find some shade"
    elif t < 34:
        msg = f"{t:.0f}°C   hot, seek shade and stay hydrated"
    else:
        msg = f"{t:.0f}°C   too hot for a comfortable picnic"

    return score, msg

# def _score_temp_picnic(t):
#     points = [(4, 0.0), (8, 0.2), (13, 0.6), (16, 1.0), (26, 1.0), (32, 0.5), (36, 0.2)]
#     score = _interpolate_score(t, points)

#     if t is None:       msg = "Temperature unknown"
#     elif t < 8:         msg = f"{t:.0f}°C   too cold for a comfortable picnic"
#     elif t < 13:        msg = f"{t:.0f}°C   cool, bring a blanket"
#     elif t < 26:        msg = f"{t:.0f}°C   pleasant temperature for a picnic"
#     elif t < 32:        msg = f"{t:.0f}°C   warm, find some shade"
#     else:               msg = f"{t:.0f}°C   too hot, seek shade"

#     return score, msg


def _score_rain_picnic(p):
    points = [(0.1, 1.0), (1.3, 0.5), (2.5, 0.2), (7.6, 0.0), (8.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: ideal"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: bring a shelter"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: likely to spoil the picnic"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: not suitable"
    else:               msg = f"{p:.1f} mm/h   heavy rain: not suitable"

    return score, msg


# ============================================================
# FISHING
# ============================================================

def _score_wind_fishing(w):
    points = [(3.4, 1.0), (5.5, 0.8), (8.0, 0.5), (10.8, 0.2), (13.9, 0.0), (14.0, 0.0)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 3.4:       msg = f"{w:.0f} m/s    light breeze or calmer: excellent casting conditions"
    elif w < 5.5:       msg = f"{w:.0f} m/s    gentle breeze: good casting conditions"
    elif w < 8.0:       msg = f"{w:.0f} m/s    moderate breeze: casting more difficult"
    elif w < 10.8:      msg = f"{w:.0f} m/s    fresh breeze: difficult to fish"
    elif w < 13.9:      msg = f"{w:.0f} m/s    strong breeze: too windy"
    else:               msg = f"{w:.0f} m/s    near gale or stronger: too windy"

    return score, msg


def _score_rain_fishing(p):
    points = [(0.1, 0.9), (1.3, 0.9), (2.5, 0.6), (7.6, 0.3), (8.0, 0.1)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: comfortable"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: manageable with waterproofs"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: wet but workable"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: uncomfortable, poor visibility"
    else:               msg = f"{p:.1f} mm/h   heavy rain: unsafe, seek shelter"

    return score, msg


# ============================================================
# PHOTOGRAPHY
# ============================================================

def _score_cloud_photography(c):
    points = [(0, 0.6), (15, 0.7), (30, 0.9), (55, 1.0), (80, 0.7), (90, 0.5), (100, 0.3)]
    score = _interpolate_score(c, points)

    if c is None:       msg = "Cloud cover unknown"
    elif c < 15:        msg = f"{c:.0f}% cloud   clear sky, harsh direct light at midday"
    elif c < 40:        msg = f"{c:.0f}% cloud   light cloud, soft even light"
    elif c < 70:        msg = f"{c:.0f}% cloud   overcast, ideal diffused light for portraits"
    elif c < 90:        msg = f"{c:.0f}% cloud   heavy cloud, may be too dark"
    else:               msg = f"{c:.0f}% cloud   dense overcast, very flat light"

    return score, msg


def _score_rain_photography(p):
    points = [(0.1, 1.0), (1.3, 0.6), (2.5, 0.3), (7.6, 0.1), (8.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: equipment safe"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: protect your equipment"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: risk to camera equipment"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: do not expose your camera"
    else:               msg = f"{p:.1f} mm/h   heavy rain: do not expose your camera"

    return score, msg


# ============================================================
# STARGAZING
# ============================================================

def _score_cloud_stargazing(c):
    points = [(0, 1.0), (10, 0.9), (25, 0.7), (50, 0.4), (75, 0.1), (90, 0.0)]
    score = _interpolate_score(c, points)

    if c is None:       msg = "Cloud cover unknown"
    elif c < 10:        msg = f"{c:.0f}% cloud   near clear sky, excellent visibility"
    elif c < 25:        msg = f"{c:.0f}% cloud   mostly clear, good stargazing"
    elif c < 50:        msg = f"{c:.0f}% cloud   partial cloud, interrupted views"
    elif c < 75:        msg = f"{c:.0f}% cloud   heavy cloud, poor visibility"
    else:               msg = f"{c:.0f}% cloud   overcast, no stargazing possible"

    return score, msg


def _score_humidity_stargazing(h):
    points = [(0, 1.0), (50, 1.0), (70, 0.8), (85, 0.5), (100, 0.2)]
    score = _interpolate_score(h, points)

    if h is None:       msg = "Humidity unknown"
    elif h < 50:        msg = f"{h:.0f}% humidity   dry air, sharp visibility"
    elif h < 70:        msg = f"{h:.0f}% humidity   good transparency"
    elif h < 85:        msg = f"{h:.0f}% humidity   some atmospheric blurring"
    else:               msg = f"{h:.0f}% humidity   very humid, hazy sky"

    return score, msg


def _score_rain_stargazing(p):
    points = [(0.1, 1.0), (1.3, 0.0), (2.5, 0.0), (7.6, 0.0), (8.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: no precipitation"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: no stargazing possible"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: no stargazing possible"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: no stargazing possible"
    else:               msg = f"{p:.1f} mm/h   heavy rain: no stargazing possible"

    return score, msg


# ============================================================
# GARDENING
# ============================================================

def _score_temp_gardening(t):
    points = [(-5, 0.0), (0, 0.1), (5, 0.3), (10, 0.7), (13, 1.0), (25, 1.0), (32, 0.6), (36, 0.2)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < 0:         msg = f"{t:.0f}°C   frozen ground, do not garden"
    elif t < 5:         msg = f"{t:.0f}°C   very cold, essential tasks only"
    elif t < 10:        msg = f"{t:.0f}°C   cool, suitable for light gardening"
    elif t < 25:        msg = f"{t:.0f}°C   ideal gardening temperature"
    elif t < 32:        msg = f"{t:.0f}°C   warm, garden early morning or evening"
    else:               msg = f"{t:.0f}°C   too hot, risk of heat stress"

    return score, msg


def _score_rain_gardening(p):
    points = [(0.1, 0.9), (1.3, 1.0), (2.5, 0.6), (7.6, 0.2), (8.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: water plants if needed"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: natural watering for plants"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: soil getting wet, avoid digging"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: too wet to work outside"
    else:               msg = f"{p:.1f} mm/h   heavy rain: stay indoors"

    return score, msg


# ============================================================
# CLOTHING
# ============================================================

def _score_temp_clothing(t):
    points = [(-5, 0.1), (0, 0.2), (5, 0.3), (10, 0.5), (15, 0.6), (20, 0.8), (23, 1.0), (26, 1.0), (32, 0.7)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < 0:         msg = f"{t:.0f}°C   heavy winter coat essential"
    elif t < 5:         msg = f"{t:.0f}°C   warm coat and layers needed"
    elif t < 10:        msg = f"{t:.0f}°C   jacket required"
    elif t < 15:        msg = f"{t:.0f}°C   light jacket recommended"
    elif t < 20:        msg = f"{t:.0f}°C   comfortable, light layers are enough"
    elif t < 26:        msg = f"{t:.0f}°C   warm, t-shirt weather"
    else:               msg = f"{t:.0f}°C   hot, light breathable clothing"

    return score, msg


def _score_rain_clothing(p):
    points = [(0.1, 1.0), (1.3, 0.7), (2.5, 0.4), (7.6, 0.2), (8.0, 0.2)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: no rain protection needed"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: an umbrella or light waterproof is useful"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: a waterproof jacket is needed"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: full waterproofs essential"
    else:               msg = f"{p:.1f} mm/h   heavy rain: full waterproofs essential"

    return score, msg


def _score_wind_clothing(w):
    points = [(3.4, 1.0), (5.5, 1.0), (8.0, 0.9), (10.8, 0.7), (13.9, 0.5), (14.0, 0.3)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 3.4:       msg = f"{w:.0f} m/s    light breeze or calmer: no effect"
    elif w < 5.5:       msg = f"{w:.0f} m/s    gentle breeze: little effect"
    elif w < 8.0:       msg = f"{w:.0f} m/s    moderate breeze: slight chill"
    elif w < 10.8:      msg = f"{w:.0f} m/s    fresh breeze: a windbreaker is useful"
    elif w < 13.9:      msg = f"{w:.0f} m/s    strong breeze: feels noticeably colder, wear a windproof layer"
    else:               msg = f"{w:.0f} m/s    near gale or stronger: warm windproof clothing essential"

    return score, msg


# ============================================================
# DRIVING
# ============================================================

def _score_rain_driving(p):
    points = [(0.1, 1.0), (1.3, 0.8), (2.5, 0.6), (7.6, 0.3), (8.0, 0.1)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: dry roads"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: damp roads"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: wet roads, reduce speed, keep your distance"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: reduced visibility, aquaplaning risk"
    else:               msg = f"{p:.1f} mm/h   heavy rain: very poor visibility, avoid driving if possible"

    return score, msg


def _score_snow_driving(s):
    points = [(0.0, 1.0), (0.05, 1.0), (0.12, 0.5), (0.5, 0.2), (1.0, 0.0)]
    score = _interpolate_score(s, points)

    if s is None or s < 0.05: msg = "No snowfall"
    elif s < 0.2:              msg = f"{s:.1f} mm/h snow (water eq.)   light snow: snow on roads, winter tyres advised"
    elif s < 0.8:              msg = f"{s:.1f} mm/h snow (water eq.)   moderate snow: hazardous driving"
    else:                      msg = f"{s:.1f} mm/h snow (water eq.)   heavy snow: avoid driving"

    return score, msg


def _score_wind_driving(g):
    points = [(15, 1.0), (20, 0.8), (25, 0.5), (30, 0.2), (35, 0.0)]
    score = _interpolate_score(g, points)

    if g is None:       msg = "Gust data unknown"
    elif g < 15:        msg = f"gusts {g:.0f} m/s ({g * 3.6:.0f} km/h)   no significant effect on driving"
    elif g < 20:        msg = f"gusts {g:.0f} m/s ({g * 3.6:.0f} km/h)   take care on bridges and open roads"
    elif g < 25:        msg = f"gusts {g:.0f} m/s ({g * 3.6:.0f} km/h)   strong gusts, high-sided vehicles at risk"
    elif g < 30:        msg = f"gusts {g:.0f} m/s ({g * 3.6:.0f} km/h)   very strong gusts, dangerous for trucks and caravans"
    else:               msg = f"gusts {g:.0f} m/s ({g * 3.6:.0f} km/h)   extreme gusts, avoid driving if possible"

    return score, msg


# ============================================================
# DOG WALKING
# ============================================================

def _score_temp_dogwalk(t):
    points = [(-10, 0.1), (-5, 0.2), (2, 0.6), (5, 1.0), (22, 1.0), (28, 0.6), (32, 0.3), (36, 0.1)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < -5:        msg = f"{t:.0f}°C   very cold, limit walk time for small breeds"
    elif t < 2:         msg = f"{t:.0f}°C   cold, boots may help sensitive paws"
    elif t < 22:        msg = f"{t:.0f}°C   comfortable for dogs"
    elif t < 28:        msg = f"{t:.0f}°C   warm, carry water for your dog"
    elif t < 32:        msg = f"{t:.0f}°C   hot, walk early morning or late evening"
    else:               msg = f"{t:.0f}°C   dangerous heat, hot pavement can burn paws"

    return score, msg


def _score_rain_dogwalk(p):
    points = [(0.1, 1.0), (1.3, 0.8), (2.5, 0.5), (7.6, 0.3), (8.0, 0.2)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p < 0.1:       msg = "Dry: great for a walk"
    elif p < 1.3:       msg = f"{p:.1f} mm/h   drizzle: most dogs don't mind"
    elif p < 2.5:       msg = f"{p:.1f} mm/h   light rain: keep the walk short"
    elif p < 7.6:       msg = f"{p:.1f} mm/h   moderate rain: short outing only"
    else:               msg = f"{p:.1f} mm/h   heavy rain: quick toilet break only"

    return score, msg


def _score_wind_dogwalk(w):
    points = [(3.4, 1.0), (5.5, 1.0), (8.0, 1.0), (10.8, 0.8), (13.9, 0.5), (14.0, 0.2)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 3.4:       msg = f"{w:.0f} m/s    light breeze or calmer: good walking conditions"
    elif w < 5.5:       msg = f"{w:.0f} m/s    gentle breeze: good walking conditions"
    elif w < 8.0:       msg = f"{w:.0f} m/s    moderate breeze: fine for most dogs"
    elif w < 10.8:      msg = f"{w:.0f} m/s    fresh breeze: breezy, fine for most dogs"
    elif w < 13.9:      msg = f"{w:.0f} m/s    strong breeze: small dogs may struggle"
    else:               msg = f"{w:.0f} m/s    near gale or stronger: keep dogs on a lead"

    return score, msg

# ── Summary message builder ────────────────────────────────────────────────────
def _summary_message(params: dict) -> str:
    """
    Builds the one-line summary shown in the LifestyleWidget card.
    Shows the worst parameter description if status is not all green,
    otherwise shows the best positive message.
    """
    values = list(params.values())
    non_green = [p for p in values if p["score"] < 0.7]
    if non_green:
        worst = min(non_green, key=lambda p: p["score"])
        return worst["description"]
    return values[0]["description"] if values else ""


# ── Activities configurations ──────────────────────────────────────────────────────────
ACTIVITIES_CFG = {
    "cycling":{
        "id": "cycling",
        "icon": "🚴",
        "label": "Cycling",
        "parameters":[
            {"name": "temperature", "scorer_function": _score_temp_cycling, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": _score_wind_cycling, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "gust", "scorer_function": _score_gust_cycling, "scorer_function_inputs": ["wind_gust_m_per_s"]},
            {"name": "rain", "scorer_function": _score_rain_cycling, "scorer_function_inputs": ["precipitation_mm"]},
            {"name": "snow", "scorer_function": _score_snow_cycling, "scorer_function_inputs": ["snow_precipitation_mm"]}
            ]
        },
    "running":{
        "id": "running",
        "icon": "🏃",
        "label": "Running",
        "parameters":[
            {"name": "temperature", "scorer_function": _score_temp_running, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": _score_wind_running, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": _score_rain_running, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "hiking":{
        "id": "hiking",
        "icon": "🥾",
        "label": "Hiking",
        "parameters":[
            {"name": "temperature", "scorer_function": _score_temp_hiking, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": _score_wind_hiking, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "gust", "scorer_function": _score_gust_hiking, "scorer_function_inputs": ["wind_gust_m_per_s"]},
            {"name": "rain", "scorer_function": _score_rain_hiking, "scorer_function_inputs": ["precipitation_mm"]},
            {"name": "snow", "scorer_function": _score_snow_hiking, "scorer_function_inputs": ["snow_precipitation_mm"]}
            ]
        },
    "picnic":{
        "id": "picnic",
        "icon": "🧺",
        "label": "Picnic",
        "parameters":[
            {"name": "temperature", "scorer_function": _score_temp_picnic, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": _score_wind_picnic, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": _score_rain_picnic, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "fishing":{
        "id": "fishing",
        "icon": "🎣",
        "label": "Fishing",
        "parameters":[
            {"name": "wind", "scorer_function": _score_wind_fishing, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": _score_rain_fishing, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "photography":{
        "id": "photography",
        "icon": "📷",
        "label": "Photography",
        "parameters":[
            {"name": "cloud_cover", "scorer_function": _score_cloud_photography, "scorer_function_inputs": ["total_cloud_cover"]},
            {"name": "rain", "scorer_function": _score_rain_photography, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "stargazing":{
        "id": "stargazing",
        "icon": "📷",
        "label": "Stargazing",
        "parameters":[
            {"name": "cloud_cover", "scorer_function": _score_cloud_stargazing, "scorer_function_inputs": ["total_cloud_cover"]},
            {"name": "humidity", "scorer_function": _score_humidity_stargazing, "scorer_function_inputs": ["humidity_percentage"]},
            {"name": "rain", "scorer_function": _score_rain_stargazing, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "gardening":{
        "id": "gardening",
        "icon": "🌱",
        "label": "Gardening",
        "parameters":[
            {"name": "temperature", "scorer_function": _score_temp_gardening, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "rain", "scorer_function": _score_rain_gardening, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "clothing":{
        "id": "clothing",
        "icon": "🧥",
        "label": "Clothing",
        "parameters":[
            {"name": "temperature", "scorer_function": _score_temp_clothing, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": _score_wind_clothing, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": _score_rain_clothing, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "driving":{
        "id": "driving",
        "icon": "🚗",
        "label": "Driving",
        "parameters":[
            {"name": "snow", "scorer_function": _score_snow_driving, "scorer_function_inputs": ["snow_precipitation_mm"]},
            {"name": "wind", "scorer_function": _score_wind_driving, "scorer_function_inputs": ["wind_gust_m_per_s"]},
            {"name": "rain", "scorer_function": _score_rain_driving, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    "dogwalking":{
        "id": "dogwalking",
        "icon": "🐕",
        "label": "Dogwalking",
        "parameters":[
            {"name": "temperature", "scorer_function": _score_temp_dogwalk, "scorer_function_inputs": ["temperature_celsius"]},
            {"name": "wind", "scorer_function": _score_wind_dogwalk, "scorer_function_inputs": ["wind_speed_m_per_s"]},
            {"name": "rain", "scorer_function": _score_rain_dogwalk, "scorer_function_inputs": ["precipitation_mm"]},
            ]
        },
    }

def _score_hour(entry: dict, activity_config: dict) -> tuple:    
    activity_parameters_list = activity_config["parameters"] # list of dictionary
    params = {}
    tmp_list_os_scores = []
    for parameter in activity_parameters_list:
        parameter_name = parameter["name"]
        parameter_scorer_function = parameter["scorer_function"]
        parameter_scorer_function_inputs = parameter["scorer_function_inputs"]
        
        inputs = [entry.get(inpt) for inpt in parameter_scorer_function_inputs]
        
        score_value, message = parameter_scorer_function(*inputs)
        status = _status(score_value)
        
        params[parameter_name] = _param(score_value, status, message)
        tmp_list_os_scores.append(score_value)
    
    activity_score = _activity_representative_score(tmp_list_os_scores)
    activity_status = _activity_status(activity_score)

    return activity_score, activity_status, params


def _build_activity(current: dict, forecast: list[dict], activity: str) -> dict:
    # import pdb
    # pdb.set_trace()
    activity_config = ACTIVITIES_CFG.get(activity, None)
    if activity_config is None:
        logger.error("The requested activity does not exist; check typos")
        
    idd = activity_config["id"]
    icon = activity_config["icon"]
    label = activity_config["label"]
    score, status, params = _score_hour(current, activity_config)
    return {
        "id": idd, "icon": icon, "label": label,
        "status": status,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": status, "score": score,
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_hour, activity_config),
        "hourly": _build_hourly_scores(forecast, _score_hour, activity_config),
    }


# ── Generic hourly builder ─────────────────────────────────────────────────────

def _build_hourly_scores(forecast: list[dict], scorer_fn, activity_config: dict) -> list[dict]:
    """
    Applies a scorer function to each forecast entry and
    returns a list of hourly dicts shaped for the frontend.
    """
    result = []
    for entry in forecast[:48]:
        score, status, params = scorer_fn(entry, activity_config)
        result.append({
            "time":       str(entry.get("time_step_fr", "")),
            "score":      round(score, 2),
            "status":     status,
            "parameters": params,
        })
    return result


def _find_best_windows(forecast: list[dict], scorer_fn, activity_config) -> list[dict]:
    """
    Finds consecutive green windows in the forecast.
    Returns up to 2 windows where score >= 0.7 for at least 2 hours.
    A new window starts when score drops below 0.7.
    """
    windows = []
    current_window = []
    # import pdb
    # pdb.set_trace()
    for entry in forecast[:48]:
        score, status, _ = scorer_fn(entry, activity_config)
        if score >= 0.7:
            current_window.append(entry)
        else:
            if len(current_window) >= 2:
                windows.append(current_window)
            current_window = []

    if len(current_window) >= 2:
        windows.append(current_window)

    result = []
    for window in windows[:2]:
        from_time = str(window[0].get("time_step_fr", ""))
        to_time   = str(window[-1].get("time_step_fr", ""))
        _, _, params = scorer_fn(window[0], activity_config)
        best_desc = next(
            (p["description"] for p in params.values() if p["score"] >= 0.7),
            "Good conditions"
        )
        result.append({
            "from":   from_time,
            "to":     to_time,
            "reason": best_desc,
        })

    return result