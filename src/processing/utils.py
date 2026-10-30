from src.data.getter import DatabaseGetter

# def unaccumulate(forecast, variable_name, station_id):
#     """
#     The objective of this function is to return the list of dicitonary of forecast with instant values and not cumulative ones.
#     It is dedicated only for the variables that are recorded cumulatively in the database
#     This is temporary solution; in teh future we will direclty convert cumulative to intant in silver layers
#     """
    
#     # Get the run_time of this forecast so we can find the previous entry
#     # run_time comes from the first forecast entry
#     run_time = forecast[0].get("run_time")

#     # Fetch the cumulative radiation value just before our slice starts
#     # so the first entry in our slice is correctly de-accumulated
#     previous = DatabaseGetter.get_previous_cumulative(
#         station_id=station_id,
#         run_time=run_time,
#         current_time=forecast[0].get("time_step_fr"),
#         variable_name = variable_name
#     )

#     cumulative = [
#         float(entry.get(variable_name) or 0)
#         for entry in forecast
#     ]

#     unaccum = []
#     prev = previous

#     for cum in cumulative:
#         instant = (cum - prev)
#         unaccum.append(max(0.0, instant))
#         prev = cum    

#     for entry, value in zip (forecast, unaccum):
#         entry[variable_name] = value
#     return forecast


# ── Activity helpers ───────────────────────────────────────────────────────────

def _activity_status(scores: list[float]) -> str:
    """
    Combines multiple parameter scores into one overall status.
    The weakest parameter drives the overall status — a chain is only
    as strong as its weakest link. This matches how real conditions work:
    perfect temperature doesn't help if it's pouring rain.
    """
    worst = min(scores)
    if worst >= 0.7:  return "green"
    if worst >= 0.4:  return "yellow"
    return "red"

def _param(score: float, status: str, description: str) -> dict:
    return {"score": score, "status": status, "description": description}

def _score_and_status(score: float) -> str:
    if score >= 0.7: return "green"
    if score >= 0.4: return "yellow"
    return "red"

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
    points = [(2, 0.1), (7, 0.4), (10, 0.6), (28, 1.0), (33, 0.6), (40, 0.3)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < 2:         msg = f"{t:.0f}°C — dangerously cold for cycling, risk of ice"
    elif t < 7:         msg = f"{t:.0f}°C — cold, dress in thermal layers"
    elif t < 10:        msg = f"{t:.0f}°C — cool, arm warmers recommended"
    elif t <= 28:       msg = f"{t:.0f}°C — comfortable cycling temperature"
    elif t <= 33:       msg = f"{t:.0f}°C — warm, carry extra water"
    else:               msg = f"{t:.0f}°C — too hot, risk of heat exhaustion"

    return score, msg


def _score_wind_cycling(w, g):
    ref = g if g is not None else w
    points = [(5, 1.0), (10, 0.9), (15, 0.7), (20, 0.4), (25, 0.2), (30, 0.0)]
    score = _interpolate_score(ref, points)

    if ref is None:     msg = "Wind unknown"
    elif ref < 5:       msg = f"{ref:.0f} m/s — calm, ideal conditions"
    elif ref < 10:      msg = f"{ref:.0f} m/s — light wind, barely noticeable"
    elif ref < 15:      msg = f"{ref:.0f} m/s — moderate wind, manageable"
    elif ref < 20:      msg = f"{ref:.0f} m/s — strong wind, expect resistance on exposed roads"
    elif ref < 25:      msg = f"{ref:.0f} m/s — very strong wind, hazardous cycling"
    else:               msg = f"{ref:.0f} m/s — dangerous gusts, do not cycle"

    return score, msg


def _score_rain_cycling(p):
    points = [(0, 1.0), (0.5, 0.8), (2.0, 0.5), (5.0, 0.2), (10.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "Dry — good grip on roads"
    elif p < 0.5:       msg = f"{p:.1f} mm — light drizzle, roads slightly wet"
    elif p < 2.0:       msg = f"{p:.1f} mm — moderate rain, reduced grip"
    elif p < 5.0:       msg = f"{p:.1f} mm — heavy rain, poor visibility and grip"
    else:               msg = f"{p:.1f} mm — very heavy rain, unsafe to cycle"

    return score, msg


def _score_snow_cycling(s):
    points = [(0, 1.0), (0.2, 0.3), (2.0, 0.0)]
    score = _interpolate_score(s, points)

    if s is None or s == 0: msg = "No snowfall"
    elif s < 0.2:            msg = f"{s:.1f} mm snow — slippery roads, extreme caution"
    else:                    msg = f"{s:.1f} mm snow — do not cycle, roads dangerous"

    return score, msg


# ============================================================
# RUNNING
# ============================================================

def _score_temp_running(t):
    points = [(-5, 0.1), (0, 0.3), (5, 0.6), (18, 1.0), (24, 0.7), (30, 0.4), (35, 0.1)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < -5:        msg = f"{t:.0f}°C — extreme cold, risk of hypothermia"
    elif t < 0:         msg = f"{t:.0f}°C — freezing, icy paths likely"
    elif t < 5:         msg = f"{t:.0f}°C — cold, warm up thoroughly before running"
    elif t <= 18:       msg = f"{t:.0f}°C — ideal running temperature"
    elif t <= 24:       msg = f"{t:.0f}°C — warm, hydrate well"
    elif t <= 30:       msg = f"{t:.0f}°C — hot, reduce pace and carry water"
    else:               msg = f"{t:.0f}°C — dangerous heat, avoid running outdoors"

    return score, msg


def _score_wind_running(w):
    points = [(5, 1.0), (10, 0.9), (15, 0.7), (20, 0.5), (25, 0.2)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 5:         msg = f"{w:.0f} m/s — calm, no wind resistance"
    elif w < 10:        msg = f"{w:.0f} m/s — light wind, minimal impact"
    elif w < 15:        msg = f"{w:.0f} m/s — moderate wind, expect slower pace"
    elif w < 20:        msg = f"{w:.0f} m/s — strong wind, challenging run"
    else:               msg = f"{w:.0f} m/s — very strong wind, not recommended"

    return score, msg


def _score_rain_running(p):
    points = [(0, 1.0), (1, 0.8), (3, 0.5), (7, 0.3), (10, 0.1)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "Dry conditions"
    elif p < 1.0:       msg = f"{p:.1f} mm — light rain, manageable with waterproof"
    elif p < 3.0:       msg = f"{p:.1f} mm — moderate rain, paths may be slippery"
    elif p < 7.0:       msg = f"{p:.1f} mm — heavy rain, poor visibility"
    else:               msg = f"{p:.1f} mm — very heavy rain, unsafe"

    return score, msg


# ============================================================
# HIKING
# ============================================================

def _score_temp_hiking(t):
    points = [(-10, 0.1), (0, 0.4), (5, 0.6), (22, 1.0), (28, 0.6), (35, 0.2)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < -10:       msg = f"{t:.0f}°C — extreme cold at altitude, dangerous"
    elif t < 0:         msg = f"{t:.0f}°C — freezing, pack crampons and warm layers"
    elif t < 5:         msg = f"{t:.0f}°C — cold, thermal layers essential"
    elif t <= 22:       msg = f"{t:.0f}°C — ideal hiking temperature"
    elif t <= 28:       msg = f"{t:.0f}°C — warm, carry at least 2L of water"
    else:               msg = f"{t:.0f}°C — too hot for strenuous hiking"

    return score, msg


def _score_wind_hiking(w, g):
    ref = g if g is not None else w
    points = [(8, 1.0), (14, 0.8), (20, 0.5), (25, 0.2), (30, 0.0)]
    score = _interpolate_score(ref, points)

    if ref is None:     msg = "Wind unknown"
    elif ref < 8:       msg = f"{ref:.0f} m/s — calm, ideal"
    elif ref < 14:      msg = f"{ref:.0f} m/s — light breeze, pleasant"
    elif ref < 20:      msg = f"{ref:.0f} m/s — moderate wind, take care on ridges"
    elif ref < 25:      msg = f"{ref:.0f} m/s — strong wind, dangerous on exposed terrain"
    else:               msg = f"{ref:.0f} m/s — dangerous gusts, do not hike on ridges"

    return score, msg


def _score_rain_hiking(p):
    points = [(0, 1.0), (1, 0.7), (3, 0.4), (7, 0.2), (10, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "Dry — good trail conditions"
    elif p < 1.0:       msg = f"{p:.1f} mm — light rain, trails manageable with waterproof"
    elif p < 3.0:       msg = f"{p:.1f} mm — moderate rain, trails slippery"
    elif p < 7.0:       msg = f"{p:.1f} mm — heavy rain, risk of trail erosion and slips"
    else:               msg = f"{p:.1f} mm — dangerous rainfall, stay off trails"

    return score, msg


def _score_snow_hiking(s):
    points = [(0, 1.0), (0.5, 0.5), (2.0, 0.2), (4.0, 0.0)]
    score = _interpolate_score(s, points)

    if s is None or s == 0: msg = "No snowfall"
    elif s < 0.5:            msg = f"{s:.1f} mm snow — light snow, paths may be icy"
    elif s < 2.0:            msg = f"{s:.1f} mm snow — significant snowfall, paths treacherous"
    else:                    msg = f"{s:.1f} mm snow — heavy snowfall, do not hike"

    return score, msg


# ============================================================
# PICNIC
# ============================================================

def _score_wind_picnic(w):
    points = [(5, 1.0), (10, 0.8), (15, 0.5), (20, 0.2), (25, 0.0)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 5:         msg = f"{w:.0f} m/s — calm, perfect for a picnic"
    elif w < 10:        msg = f"{w:.0f} m/s — light breeze, pleasant"
    elif w < 15:        msg = f"{w:.0f} m/s — moderate wind, weigh down napkins and items"
    elif w < 20:        msg = f"{w:.0f} m/s — strong wind, not comfortable outdoors"
    else:               msg = f"{w:.0f} m/s — too windy for a picnic"

    return score, msg


def _score_temp_picnic(t):
    points = [(8, 0.2), (13, 0.5), (26, 1.0), (32, 0.6), (38, 0.2)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < 8:         msg = f"{t:.0f}°C — too cold for a comfortable picnic"
    elif t < 13:        msg = f"{t:.0f}°C — cool, bring a blanket"
    elif t <= 26:       msg = f"{t:.0f}°C — pleasant temperature for a picnic"
    elif t <= 32:       msg = f"{t:.0f}°C — warm, find shade if possible"
    else:               msg = f"{t:.0f}°C — too hot, seek shade"

    return score, msg


def _score_rain_picnic(p):
    points = [(0, 1.0), (0.3, 0.6), (2.0, 0.2), (4.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "No rain — dry conditions"
    elif p < 0.3:       msg = f"{p:.1f} mm — light drizzle, might be acceptable"
    elif p < 2.0:       msg = f"{p:.1f} mm — rain expected, not ideal for picnic"
    else:               msg = f"{p:.1f} mm — heavy rain, cancel the picnic"

    return score, msg


# ============================================================
# FISHING
# ============================================================

def _score_wind_fishing(w):
    points = [(5, 1.0), (10, 0.8), (15, 0.5), (20, 0.2), (25, 0.0)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 5:         msg = f"{w:.0f} m/s — calm — excellent fishing conditions"
    elif w < 10:        msg = f"{w:.0f} m/s — light wind, good casting conditions"
    elif w < 15:        msg = f"{w:.0f} m/s — moderate wind, casting more difficult"
    elif w < 20:        msg = f"{w:.0f} m/s — strong wind, difficult to fish"
    else:               msg = f"{w:.0f} m/s — too windy for fishing"

    return score, msg


def _score_rain_fishing(p):
    points = [(0, 0.8), (1, 1.0), (4, 0.6), (8, 0.3), (12, 0.1)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "Dry — fish may be less active near surface"
    elif p < 1.0:       msg = f"{p:.1f} mm — light rain — fish actively feeding"
    elif p < 4.0:       msg = f"{p:.1f} mm — moderate rain — acceptable conditions"
    elif p < 8.0:       msg = f"{p:.1f} mm — heavy rain — murky water, poor fishing"
    else:               msg = f"{p:.1f} mm — very heavy rain — dangerous, seek shelter"

    return score, msg


# ============================================================
# PHOTOGRAPHY
# ============================================================

def _score_cloud_photography(c):
    points = [(15, 0.7), (40, 0.9), (70, 1.0), (90, 0.6), (100, 0.3)]
    score = _interpolate_score(c, points)

    if c is None:       msg = "Cloud cover unknown"
    elif c < 15:        msg = f"{c:.0f}% cloud — clear sky, harsh direct light midday"
    elif c < 40:        msg = f"{c:.0f}% cloud — light cloud, soft and even light"
    elif c < 70:        msg = f"{c:.0f}% cloud — overcast, ideal diffused light for portraits"
    elif c < 90:        msg = f"{c:.0f}% cloud — heavy cloud, may be too dark"
    else:               msg = f"{c:.0f}% cloud — dense overcast, very flat light"

    return score, msg


def _score_rain_photography(p):
    points = [(0, 1.0), (0.3, 0.7), (2.0, 0.3), (5.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "No rain — equipment safe"
    elif p < 0.3:       msg = f"{p:.1f} mm — light drizzle, protect equipment"
    elif p < 2.0:       msg = f"{p:.1f} mm — rain — risk to camera equipment"
    else:               msg = f"{p:.1f} mm — heavy rain — do not expose camera"

    return score, msg


# ============================================================
# STARGAZING
# ============================================================

def _score_cloud_stargazing(c):
    points = [(10, 1.0), (25, 0.8), (50, 0.5), (75, 0.2), (100, 0.0)]
    score = _interpolate_score(c, points)

    if c is None:       msg = "Cloud cover unknown"
    elif c < 10:        msg = f"{c:.0f}% cloud — near clear sky, excellent visibility"
    elif c < 25:        msg = f"{c:.0f}% cloud — mostly clear, good stargazing"
    elif c < 50:        msg = f"{c:.0f}% cloud — partial cloud, interrupted views"
    elif c < 75:        msg = f"{c:.0f}% cloud — heavy cloud cover, poor visibility"
    else:               msg = f"{c:.0f}% cloud — overcast, no stargazing possible"

    return score, msg


def _score_humidity_stargazing(h):
    points = [(50, 1.0), (70, 0.8), (85, 0.5), (100, 0.2)]
    score = _interpolate_score(h, points)

    if h is None:       msg = "Humidity unknown"
    elif h < 50:        msg = f"{h:.0f}% humidity — dry air, sharp sky visibility"
    elif h < 70:        msg = f"{h:.0f}% humidity — good transparency"
    elif h < 85:        msg = f"{h:.0f}% humidity — some atmospheric blurring"
    else:               msg = f"{h:.0f}% humidity — very humid, hazy sky"

    return score, msg


def _score_rain_stargazing(p):
    points = [(0, 1.0), (0.1, 0.3), (1.0, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "No precipitation"
    elif p < 0.1:       msg = f"{p:.1f} mm — light drizzle, clouds likely forming"
    else:               msg = f"{p:.1f} mm — raining, no stargazing possible"

    return score, msg


# ============================================================
# GARDENING
# ============================================================

def _score_temp_gardening(t):
    points = [(0, 0.1), (5, 0.3), (10, 0.6), (25, 1.0), (32, 0.6), (38, 0.2)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < 0:         msg = f"{t:.0f}°C — frozen ground, do not garden"
    elif t < 5:         msg = f"{t:.0f}°C — very cold, only essential tasks"
    elif t < 10:        msg = f"{t:.0f}°C — cool, suitable for light gardening"
    elif t <= 25:       msg = f"{t:.0f}°C — ideal gardening temperature"
    elif t <= 32:       msg = f"{t:.0f}°C — warm, garden early morning or evening"
    else:               msg = f"{t:.0f}°C — too hot, risk of heat stress"

    return score, msg


def _score_rain_gardening(p):
    points = [(0, 0.9), (1, 1.0), (4, 0.6), (8, 0.2), (12, 0.0)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "Dry — good for most gardening tasks"
    elif p < 1.0:       msg = f"{p:.1f} mm — light rain — natural watering, great for planting"
    elif p < 4.0:       msg = f"{p:.1f} mm — moderate rain — soil waterlogged, avoid digging"
    elif p < 8.0:       msg = f"{p:.1f} mm — heavy rain — stay indoors"
    else:               msg = f"{p:.1f} mm — very heavy rain — dangerous outdoors"

    return score, msg


# ============================================================
# CLOTHING
# ============================================================

def _score_temp_clothing(t):
    points = [(0, 0.2), (5, 0.3), (10, 0.5), (15, 0.6), (20, 0.8), (26, 1.0), (32, 0.7)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < 0:         msg = f"{t:.0f}°C — heavy winter coat essential"
    elif t < 5:         msg = f"{t:.0f}°C — warm coat and layers needed"
    elif t < 10:        msg = f"{t:.0f}°C — jacket required"
    elif t < 15:        msg = f"{t:.0f}°C — light jacket recommended"
    elif t < 20:        msg = f"{t:.0f}°C — comfortable, light layers sufficient"
    elif t < 26:        msg = f"{t:.0f}°C — warm, t-shirt weather"
    else:               msg = f"{t:.0f}°C — hot, light breathable clothing"

    return score, msg


def _score_rain_clothing(p):
    points = [(0, 1.0), (0.5, 0.7), (3.0, 0.4), (6.0, 0.2)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "No rain"
    elif p < 0.5:       msg = f"{p:.1f} mm — light drizzle, umbrella useful"
    elif p < 3.0:       msg = f"{p:.1f} mm — rain, waterproof jacket needed"
    else:               msg = f"{p:.1f} mm — heavy rain, full waterproofs essential"

    return score, msg


def _score_wind_clothing(w):
    points = [(5, 1.0), (10, 0.9), (15, 0.7), (20, 0.5), (25, 0.3)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 5:         msg = f"{w:.0f} m/s — calm"
    elif w < 10:        msg = f"{w:.0f} m/s — light breeze, adds slight chill"
    elif w < 15:        msg = f"{w:.0f} m/s — moderate wind, windbreaker useful"
    elif w < 20:        msg = f"{w:.0f} m/s — strong wind, feels significantly colder"
    else:               msg = f"{w:.0f} m/s — very strong wind, warm windproof essential"

    return score, msg


# ============================================================
# DRIVING
# ============================================================

def _score_rain_driving(p):
    points = [(0, 1.0), (1, 0.8), (4, 0.6), (8, 0.3), (12, 0.1)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "Dry roads"
    elif p < 1.0:       msg = f"{p:.1f} mm — light rain, roads slightly wet"
    elif p < 4.0:       msg = f"{p:.1f} mm — moderate rain, reduce speed"
    elif p < 8.0:       msg = f"{p:.1f} mm — heavy rain, aquaplaning risk"
    else:               msg = f"{p:.1f} mm — very heavy rain, consider not driving"

    return score, msg


def _score_snow_driving(s):
    points = [(0, 1.0), (0.5, 0.4), (2.0, 0.2), (4.0, 0.0)]
    score = _interpolate_score(s, points)

    if s is None or s == 0: msg = "No snow"
    elif s < 0.5:            msg = f"{s:.1f} mm snow — snow on roads, winter tyres needed"
    elif s < 2.0:            msg = f"{s:.1f} mm snow — significant snow, hazardous driving"
    else:                    msg = f"{s:.1f} mm snow — heavy snowfall, avoid driving"

    return score, msg


def _score_wind_driving(g):
    points = [(15, 1.0), (20, 0.8), (25, 0.5), (30, 0.2), (35, 0.0)]
    score = _interpolate_score(g, points)

    if g is None:       msg = "Gust data unknown"
    elif g < 15:        msg = f"{g:.0f} m/s gusts — calm, normal driving"
    elif g < 20:        msg = f"{g:.0f} m/s gusts — light gusts, take care on bridges"
    elif g < 25:        msg = f"{g:.0f} m/s gusts — strong gusts, high vehicles at risk"
    elif g < 30:        msg = f"{g:.0f} m/s gusts — very strong gusts, dangerous for trucks"
    else:               msg = f"{g:.0f} m/s gusts — extreme gusts, avoid driving if possible"

    return score, msg


# ============================================================
# DOG WALKING
# ============================================================

def _score_temp_dogwalk(t):
    points = [(-5, 0.2), (2, 0.5), (22, 1.0), (28, 0.6), (32, 0.3), (38, 0.1)]
    score = _interpolate_score(t, points)

    if t is None:       msg = "Temperature unknown"
    elif t < -5:        msg = f"{t:.0f}°C — very cold, limit walk time for small breeds"
    elif t < 2:         msg = f"{t:.0f}°C — cold, boots recommended for sensitive paws"
    elif t <= 22:       msg = f"{t:.0f}°C — comfortable for dogs"
    elif t <= 28:       msg = f"{t:.0f}°C — warm, carry water for your dog"
    elif t <= 32:       msg = f"{t:.0f}°C — hot, walk early morning or late evening"
    else:               msg = f"{t:.0f}°C — dangerous heat, risk of paw burns on pavement"

    return score, msg


def _score_rain_dogwalk(p):
    points = [(0, 1.0), (1, 0.8), (4, 0.5), (7, 0.2)]
    score = _interpolate_score(p, points)

    if p is None:       msg = "Precipitation unknown"
    elif p == 0:        msg = "Dry — great for a walk"
    elif p < 1.0:       msg = f"{p:.1f} mm — light rain, most dogs don't mind"
    elif p < 4.0:       msg = f"{p:.1f} mm — moderate rain, keep walk short"
    else:               msg = f"{p:.1f} mm — heavy rain, quick toilet break only"

    return score, msg


def _score_wind_dogwalk(w):
    points = [(10, 1.0), (15, 0.8), (20, 0.5), (25, 0.2)]
    score = _interpolate_score(w, points)

    if w is None:       msg = "Wind unknown"
    elif w < 10:        msg = f"{w:.0f} m/s — calm, good walk conditions"
    elif w < 15:        msg = f"{w:.0f} m/s — breezy, fine for most dogs"
    elif w < 20:        msg = f"{w:.0f} m/s — strong wind, small dogs may struggle"
    else:               msg = f"{w:.0f} m/s — very strong wind, keep dogs on lead"

    return score, msg


# ── Summary message builder ────────────────────────────────────────────────────

def _summary_message(params: dict) -> str:
    """
    Builds the one-line summary shown in the LifestyleWidget card.
    Shows the worst parameter description if status is not all green,
    otherwise shows the best positive message.
    """
    values = list(params.values())
    non_green = [p for p in values if p["status"] != "green"]
    if non_green:
        worst = min(non_green, key=lambda p: p["score"])
        return worst["description"]
    return values[0]["description"] if values else ""


# ── Activity builders ──────────────────────────────────────────────────────────

def _build_cycling(current: dict, forecast: list[dict]) -> dict:
    t = round(current.get("temperature_celsius"))
    w = round(current.get("wind_speed_m_per_s"))
    g = round(current.get("wind_gust_m_per_s"))
    p = current.get("precipitation_mm")
    s = current.get("snow_precipitation_mm")

    ts, td = _score_temp_cycling(t)
    ws, wd = _score_wind_cycling(w, g)
    rs, rd = _score_rain_cycling(p)
    ss, sd = _score_snow_cycling(s)

    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "wind":        _param(ws, _score_and_status(ws), wd),
        "rain":        _param(rs, _score_and_status(rs), rd),
        "snow":        _param(ss, _score_and_status(ss), sd),
    }
    overall = _activity_status([ts, ws, rs, ss])

    return {
        "id": "cycling", "icon": "🚴", "label": "Cycling",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(ts, ws, rs, ss),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_cycling_hour),
        "hourly": _build_hourly_scores(forecast, _score_cycling_hour),
    }

def _build_running(current: dict, forecast: list[dict]) -> dict:
    t = current.get("temperature_celsius")
    w = current.get("wind_speed_m_per_s")
    p = current.get("precipitation_mm")

    ts, td = _score_temp_running(t)
    ws, wd = _score_wind_running(w)
    rs, rd = _score_rain_running(p)

    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "wind":        _param(ws, _score_and_status(ws), wd),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    overall = _activity_status([ts, ws, rs])

    return {
        "id": "running", "icon": "🏃", "label": "Running",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(ts, ws, rs),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_running_hour),
        "hourly": _build_hourly_scores(forecast, _score_running_hour),
    }

def _build_hiking(current: dict, forecast: list[dict]) -> dict:
    t = current.get("temperature_celsius")
    w = current.get("wind_speed_m_per_s")
    g = current.get("wind_gust_m_per_s")
    p = current.get("precipitation_mm")
    s = current.get("snow_precipitation_mm")

    ts, td = _score_temp_hiking(t)
    ws, wd = _score_wind_hiking(w, g)
    rs, rd = _score_rain_hiking(p)
    ss, sd = _score_snow_hiking(s)

    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "wind":        _param(ws, _score_and_status(ws), wd),
        "rain":        _param(rs, _score_and_status(rs), rd),
        "snow":        _param(ss, _score_and_status(ss), sd),
    }
    overall = _activity_status([ts, ws, rs, ss])

    return {
        "id": "hiking", "icon": "🥾", "label": "Hiking",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(ts, ws, rs, ss),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_hiking_hour),
        "hourly": _build_hourly_scores(forecast, _score_hiking_hour),
    }

def _build_picnic(current: dict, forecast: list[dict]) -> dict:
    t = current.get("temperature_celsius")
    w = current.get("wind_speed_m_per_s")
    p = current.get("precipitation_mm")

    ts, td = _score_temp_picnic(t)
    ws, wd = _score_wind_picnic(w)
    rs, rd = _score_rain_picnic(p)

    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "wind":        _param(ws, _score_and_status(ws), wd),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    overall = _activity_status([ts, ws, rs])

    return {
        "id": "picnic", "icon": "🧺", "label": "Picnic",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(ts, ws, rs),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_picnic_hour),
        "hourly": _build_hourly_scores(forecast, _score_picnic_hour),
    }

def _build_fishing(current: dict, forecast: list[dict]) -> dict:
    w = current.get("wind_speed_m_per_s")
    p = current.get("precipitation_mm")

    ws, wd = _score_wind_fishing(w)
    rs, rd = _score_rain_fishing(p)

    params = {
        "wind": _param(ws, _score_and_status(ws), wd),
        "rain": _param(rs, _score_and_status(rs), rd),
    }
    overall = _activity_status([ws, rs])

    return {
        "id": "fishing", "icon": "🎣", "label": "Fishing",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(ws, rs),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_fishing_hour),
        "hourly": _build_hourly_scores(forecast, _score_fishing_hour),
    }

def _build_photography(current: dict, forecast: list[dict]) -> dict:
    c = current.get("total_cloud_cover")
    p = current.get("precipitation_mm")

    cs, cd = _score_cloud_photography(c)
    rs, rd = _score_rain_photography(p)

    params = {
        "cloud_cover": _param(cs, _score_and_status(cs), cd),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    overall = _activity_status([cs, rs])

    return {
        "id": "photography", "icon": "📷", "label": "Photography",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(cs, rs),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_photography_hour),
        "hourly": _build_hourly_scores(forecast, _score_photography_hour),
    }

def _build_stargazing(current: dict, forecast: list[dict]) -> dict:
    c = current.get("total_cloud_cover")
    h = current.get("humidity_percentage")
    p = current.get("precipitation_mm")

    cs, cd = _score_cloud_stargazing(c)
    hs, hd = _score_humidity_stargazing(h)
    rs, rd = _score_rain_stargazing(p)

    params = {
        "cloud_cover": _param(cs, _score_and_status(cs), cd),
        "humidity":    _param(hs, _score_and_status(hs), hd),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    overall = _activity_status([cs, hs, rs])

    return {
        "id": "stargazing", "icon": "🔭", "label": "Stargazing",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(cs, hs, rs),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_stargazing_hour),
        "hourly": _build_hourly_scores(forecast, _score_stargazing_hour),
    }

def _build_gardening(current: dict, forecast: list[dict]) -> dict:
    t = current.get("temperature_celsius")
    p = current.get("precipitation_mm")

    ts, td = _score_temp_gardening(t)
    rs, rd = _score_rain_gardening(p)

    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    overall = _activity_status([ts, rs])

    return {
        "id": "gardening", "icon": "🌱", "label": "Gardening",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(ts, rs),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_gardening_hour),
        "hourly": _build_hourly_scores(forecast, _score_gardening_hour),
    }

def _build_clothing(current: dict, forecast: list[dict]) -> dict:
    t = current.get("temperature_celsius")
    p = current.get("precipitation_mm")
    w = current.get("wind_speed_m_per_s")

    ts, td = _score_temp_clothing(t)
    rs, rd = _score_rain_clothing(p)
    ws, wd = _score_wind_clothing(w)

    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "rain":        _param(rs, _score_and_status(rs), rd),
        "wind":        _param(ws, _score_and_status(ws), wd),
    }
    overall = _activity_status([ts, rs, ws])

    return {
        "id": "clothing", "icon": "🧥", "label": "Clothing",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(ts, rs, ws),
            "parameters": params
        },
        "best_window": [],
        "hourly": _build_hourly_scores(forecast, _score_clothing_hour),
    }

def _build_driving(current: dict, forecast: list[dict]) -> dict:
    p = current.get("precipitation_mm")
    s = current.get("snow_precipitation_mm")
    g = current.get("wind_gust_m_per_s")

    rs, rd = _score_rain_driving(p)
    ss, sd = _score_snow_driving(s)
    gs, gd = _score_wind_driving(g)

    params = {
        "rain":  _param(rs, _score_and_status(rs), rd),
        "snow":  _param(ss, _score_and_status(ss), sd),
        "gusts": _param(gs, _score_and_status(gs), gd),
    }
    overall = _activity_status([rs, ss, gs])

    return {
        "id": "driving", "icon": "🚗", "label": "Driving",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(rs, ss, gs),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_driving_hour),
        "hourly": _build_hourly_scores(forecast, _score_driving_hour),
    }

def _build_dog_walking(current: dict, forecast: list[dict]) -> dict:
    t = current.get("temperature_celsius")
    p = current.get("precipitation_mm")
    w = current.get("wind_speed_m_per_s")

    ts, td = _score_temp_dogwalk(t)
    rs, rd = _score_rain_dogwalk(p)
    ws, wd = _score_wind_dogwalk(w)

    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "rain":        _param(rs, _score_and_status(rs), rd),
        "wind":        _param(ws, _score_and_status(ws), wd),
    }
    overall = _activity_status([ts, rs, ws])

    return {
        "id": "dog_walking", "icon": "🐕", "label": "Dog walking",
        "status": overall,
        "message": _summary_message(params),
        "current_status": {
            "time": str(current.get("time_step_fr", "")),
            "status": overall, "score": min(ts, rs, ws),
            "parameters": params
        },
        "best_window": _find_best_windows(forecast, _score_dog_walking_hour),
        "hourly": _build_hourly_scores(forecast, _score_dog_walking_hour),
    }


# ── Hourly scorers ─────────────────────────────────────────────────────────────
# One function per activity — scores a single forecast entry.
# Returns (overall_score, overall_status, parameters_dict)

def _score_cycling_hour(entry: dict) -> tuple:
    t = entry.get("temperature_celsius")
    w = entry.get("wind_speed_m_per_s")
    g = entry.get("wind_gust_m_per_s")
    p = entry.get("precipitation_mm")
    s = entry.get("snow_precipitation_mm")
    ts, td = _score_temp_cycling(t)
    ws, wd = _score_wind_cycling(w, g)
    rs, rd = _score_rain_cycling(p)
    ss, sd = _score_snow_cycling(s)
    score = min(ts, ws, rs, ss)
    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "wind":        _param(ws, _score_and_status(ws), wd),
        "rain":        _param(rs, _score_and_status(rs), rd),
        "snow":        _param(ss, _score_and_status(ss), sd),
    }
    return score, _score_and_status(score), params

def _score_running_hour(entry: dict) -> tuple:
    t = entry.get("temperature_celsius")
    w = entry.get("wind_speed_m_per_s")
    p = entry.get("precipitation_mm")
    ts, td = _score_temp_running(t)
    ws, wd = _score_wind_running(w)
    rs, rd = _score_rain_running(p)
    score = min(ts, ws, rs)
    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "wind":        _param(ws, _score_and_status(ws), wd),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    return score, _score_and_status(score), params

def _score_hiking_hour(entry: dict) -> tuple:
    t = entry.get("temperature_celsius")
    w = entry.get("wind_speed_m_per_s")
    g = entry.get("wind_gust_m_per_s")
    p = entry.get("precipitation_mm")
    s = entry.get("snow_precipitation_mm")
    ts, td = _score_temp_hiking(t)
    ws, wd = _score_wind_hiking(w, g)
    rs, rd = _score_rain_hiking(p)
    ss, sd = _score_snow_hiking(s)
    score = min(ts, ws, rs, ss)
    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "wind":        _param(ws, _score_and_status(ws), wd),
        "rain":        _param(rs, _score_and_status(rs), rd),
        "snow":        _param(ss, _score_and_status(ss), sd),
    }
    return score, _score_and_status(score), params

def _score_picnic_hour(entry: dict) -> tuple:
    t = entry.get("temperature_celsius")
    w = entry.get("wind_speed_m_per_s")
    p = entry.get("precipitation_mm")
    ts, td = _score_temp_picnic(t)
    ws, wd = _score_wind_picnic(w)
    rs, rd = _score_rain_picnic(p)
    score = min(ts, ws, rs)
    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "wind":        _param(ws, _score_and_status(ws), wd),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    return score, _score_and_status(score), params

def _score_fishing_hour(entry: dict) -> tuple:
    w = entry.get("wind_speed_m_per_s")
    p = entry.get("precipitation_mm")
    ws, wd = _score_wind_fishing(w)
    rs, rd = _score_rain_fishing(p)
    score = min(ws, rs)
    params = {
        "wind": _param(ws, _score_and_status(ws), wd),
        "rain": _param(rs, _score_and_status(rs), rd),
    }
    return score, _score_and_status(score), params

def _score_photography_hour(entry: dict) -> tuple:
    c = entry.get("total_cloud_cover")
    p = entry.get("precipitation_mm")
    cs, cd = _score_cloud_photography(c)
    rs, rd = _score_rain_photography(p)
    score = min(cs, rs)
    params = {
        "cloud_cover": _param(cs, _score_and_status(cs), cd),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    return score, _score_and_status(score), params

def _score_stargazing_hour(entry: dict) -> tuple:
    c = entry.get("total_cloud_cover")
    h = entry.get("humidity_percentage")
    p = entry.get("precipitation_mm")
    cs, cd = _score_cloud_stargazing(c)
    hs, hd = _score_humidity_stargazing(h)
    rs, rd = _score_rain_stargazing(p)
    score = min(cs, hs, rs)
    params = {
        "cloud_cover": _param(cs, _score_and_status(cs), cd),
        "humidity":    _param(hs, _score_and_status(hs), hd),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    return score, _score_and_status(score), params

def _score_gardening_hour(entry: dict) -> tuple:
    t = entry.get("temperature_celsius")
    p = entry.get("precipitation_mm")
    ts, td = _score_temp_gardening(t)
    rs, rd = _score_rain_gardening(p)
    score = min(ts, rs)
    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "rain":        _param(rs, _score_and_status(rs), rd),
    }
    return score, _score_and_status(score), params

def _score_clothing_hour(entry: dict) -> tuple:
    t = entry.get("temperature_celsius")
    p = entry.get("precipitation_mm")
    w = entry.get("wind_speed_m_per_s")
    ts, td = _score_temp_clothing(t)
    rs, rd = _score_rain_clothing(p)
    ws, wd = _score_wind_clothing(w)
    score = min(ts, rs, ws)
    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "rain":        _param(rs, _score_and_status(rs), rd),
        "wind":        _param(ws, _score_and_status(ws), wd),
    }
    return score, _score_and_status(score), params

def _score_driving_hour(entry: dict) -> tuple:
    p = entry.get("precipitation_mm")
    s = entry.get("snow_precipitation_mm")
    g = entry.get("wind_gust_m_per_s")
    rs, rd = _score_rain_driving(p)
    ss, sd = _score_snow_driving(s)
    gs, gd = _score_wind_driving(g)
    score = min(rs, ss, gs)
    params = {
        "rain":  _param(rs, _score_and_status(rs), rd),
        "snow":  _param(ss, _score_and_status(ss), sd),
        "gusts": _param(gs, _score_and_status(gs), gd),
    }
    return score, _score_and_status(score), params

def _score_dog_walking_hour(entry: dict) -> tuple:
    t = entry.get("temperature_celsius")
    p = entry.get("precipitation_mm")
    w = entry.get("wind_speed_m_per_s")
    ts, td = _score_temp_dogwalk(t)
    rs, rd = _score_rain_dogwalk(p)
    ws, wd = _score_wind_dogwalk(w)
    score = min(ts, rs, ws)
    params = {
        "temperature": _param(ts, _score_and_status(ts), td),
        "rain":        _param(rs, _score_and_status(rs), rd),
        "wind":        _param(ws, _score_and_status(ws), wd),
    }
    return score, _score_and_status(score), params


# ── Generic hourly builder ─────────────────────────────────────────────────────

def _build_hourly_scores(forecast: list[dict], scorer_fn) -> list[dict]:
    """
    Applies a scorer function to each forecast entry and
    returns a list of hourly dicts shaped for the frontend.
    """
    result = []
    for entry in forecast[:48]:
        score, status, params = scorer_fn(entry)
        result.append({
            "time":       str(entry.get("time_step_fr", "")),
            "score":      round(score, 2),
            "status":     status,
            "parameters": params,
        })
    return result


def _find_best_windows(forecast: list[dict], scorer_fn) -> list[dict]:
    """
    Finds consecutive green windows in the forecast.
    Returns up to 2 windows where score >= 0.7 for at least 2 hours.
    A new window starts when score drops below 0.7.
    """
    windows = []
    current_window = []

    for entry in forecast[:48]:
        score, status, _ = scorer_fn(entry)
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
        _, _, params = scorer_fn(window[0])
        best_desc = next(
            (p["description"] for p in params.values() if p["status"] == "green"),
            "Good conditions"
        )
        result.append({
            "from":   from_time,
            "to":     to_time,
            "reason": best_desc,
        })

    return result