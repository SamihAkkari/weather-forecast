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

def _score_temp_cycling(t):
    if t is None: return 0.5, "Temperature unknown"
    if t < 2:    return 0.1, f"{t:.0f}°C — dangerously cold for cycling, risk of ice"
    if t < 7:    return 0.4, f"{t:.0f}°C — cold, dress in thermal layers"
    if t < 10:   return 0.6, f"{t:.0f}°C — cool, arm warmers recommended"
    if t <= 28:  return 1.0, f"{t:.0f}°C — comfortable cycling temperature"
    if t <= 33:  return 0.6, f"{t:.0f}°C — warm, carry extra water"
    return 0.3,              f"{t:.0f}°C — too hot, risk of heat exhaustion"

def _score_wind_cycling(w, g):
    """Uses gusts when available as they are more dangerous than average wind."""
    ref = g if g is not None else w
    if ref is None: return 0.5, "Wind unknown"
    if ref < 5:    return 1.0, f"{ref:.0f} m/s — calm, ideal conditions"
    if ref < 10:   return 0.9, f"{ref:.0f} m/s — light wind, barely noticeable"
    if ref < 15:   return 0.7, f"{ref:.0f} m/s — moderate wind, manageable"
    if ref < 20:   return 0.4, f"{ref:.0f} m/s — strong wind, expect resistance on exposed roads"
    if ref < 25:   return 0.2, f"{ref:.0f} m/s — very strong wind, hazardous cycling"
    return 0.0,                f"{ref:.0f} m/s — dangerous gusts, do not cycle"

def _score_rain_cycling(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:    return 1.0, "Dry — good grip on roads"
    if p < 0.5:   return 0.8, f"{p:.1f} mm — light drizzle, roads slightly wet"
    if p < 2.0:   return 0.5, f"{p:.1f} mm — moderate rain, reduced grip"
    if p < 5.0:   return 0.2, f"{p:.1f} mm — heavy rain, poor visibility and grip"
    return 0.0,                f"{p:.1f} mm — very heavy rain, unsafe to cycle"

def _score_snow_cycling(s):
    if s is None or s == 0: return 1.0, "No snowfall"
    if s < 0.2:  return 0.3, f"{s:.1f} mm snow — slippery roads, extreme caution"
    return 0.0,               f"{s:.1f} mm snow — do not cycle, roads dangerous"

def _score_temp_running(t):
    if t is None: return 0.5, "Temperature unknown"
    if t < -5:   return 0.1, f"{t:.0f}°C — extreme cold, risk of hypothermia"
    if t < 0:    return 0.3, f"{t:.0f}°C — freezing, icy paths likely"
    if t < 5:    return 0.6, f"{t:.0f}°C — cold, warm up thoroughly before running"
    if t <= 18:  return 1.0, f"{t:.0f}°C — ideal running temperature"
    if t <= 24:  return 0.7, f"{t:.0f}°C — warm, hydrate well"
    if t <= 30:  return 0.4, f"{t:.0f}°C — hot, reduce pace and carry water"
    return 0.1,               f"{t:.0f}°C — dangerous heat, avoid running outdoors"

def _score_wind_running(w):
    if w is None: return 0.5, "Wind unknown"
    if w < 5:    return 1.0, f"{w:.0f} m/s — calm, no wind resistance"
    if w < 10:   return 0.9, f"{w:.0f} m/s — light wind, minimal impact"
    if w < 15:   return 0.7, f"{w:.0f} m/s — moderate wind, expect slower pace"
    if w < 20:   return 0.5, f"{w:.0f} m/s — strong wind, challenging run"
    return 0.2,               f"{w:.0f} m/s — very strong wind, not recommended"

def _score_rain_running(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 1.0, "Dry conditions"
    if p < 1.0:  return 0.8, f"{p:.1f} mm — light rain, manageable with waterproof"
    if p < 3.0:  return 0.5, f"{p:.1f} mm — moderate rain, paths may be slippery"
    if p < 7.0:  return 0.3, f"{p:.1f} mm — heavy rain, poor visibility"
    return 0.1,               f"{p:.1f} mm — very heavy rain, unsafe"

def _score_temp_hiking(t):
    if t is None: return 0.5, "Temperature unknown"
    if t < -10:  return 0.1, f"{t:.0f}°C — extreme cold at altitude, dangerous"
    if t < 0:    return 0.4, f"{t:.0f}°C — freezing, pack crampons and warm layers"
    if t < 5:    return 0.6, f"{t:.0f}°C — cold, thermal layers essential"
    if t <= 22:  return 1.0, f"{t:.0f}°C — ideal hiking temperature"
    if t <= 28:  return 0.6, f"{t:.0f}°C — warm, carry at least 2L of water"
    return 0.2,               f"{t:.0f}°C — too hot for strenuous hiking"

def _score_wind_hiking(w, g):
    ref = g if g is not None else w
    if ref is None: return 0.5, "Wind unknown"
    if ref < 8:    return 1.0, f"{ref:.0f} m/s — calm, ideal"
    if ref < 14:   return 0.8, f"{ref:.0f} m/s — light breeze, pleasant"
    if ref < 20:   return 0.5, f"{ref:.0f} m/s — moderate wind, take care on ridges"
    if ref < 25:   return 0.2, f"{ref:.0f} m/s — strong wind, dangerous on exposed terrain"
    return 0.0,                 f"{ref:.0f} m/s — dangerous gusts, do not hike on ridges"

def _score_rain_hiking(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 1.0, "Dry — good trail conditions"
    if p < 1.0:  return 0.7, f"{p:.1f} mm — light rain, trails manageable with waterproof"
    if p < 3.0:  return 0.4, f"{p:.1f} mm — moderate rain, trails slippery"
    if p < 7.0:  return 0.2, f"{p:.1f} mm — heavy rain, risk of trail erosion and slips"
    return 0.0,               f"{p:.1f} mm — dangerous rainfall, stay off trails"

def _score_snow_hiking(s):
    if s is None or s == 0: return 1.0, "No snowfall"
    if s < 0.5:  return 0.5, f"{s:.1f} mm snow — light snow, paths may be icy"
    if s < 2.0:  return 0.2, f"{s:.1f} mm snow — significant snowfall, paths treacherous"
    return 0.0,               f"{s:.1f} mm snow — heavy snowfall, do not hike"

def _score_wind_picnic(w):
    if w is None: return 0.5, "Wind unknown"
    if w < 5:    return 1.0, f"{w:.0f} m/s — calm, perfect for a picnic"
    if w < 10:   return 0.8, f"{w:.0f} m/s — light breeze, pleasant"
    if w < 15:   return 0.5, f"{w:.0f} m/s — moderate wind, weigh down napkins and items"
    if w < 20:   return 0.2, f"{w:.0f} m/s — strong wind, not comfortable outdoors"
    return 0.0,               f"{w:.0f} m/s — too windy for a picnic"

def _score_temp_picnic(t):
    if t is None: return 0.5, "Temperature unknown"
    if t < 8:    return 0.2, f"{t:.0f}°C — too cold for a comfortable picnic"
    if t < 13:   return 0.5, f"{t:.0f}°C — cool, bring a blanket"
    if t <= 26:  return 1.0, f"{t:.0f}°C — pleasant temperature for a picnic"
    if t <= 32:  return 0.6, f"{t:.0f}°C — warm, find shade if possible"
    return 0.2,               f"{t:.0f}°C — too hot, seek shade"

def _score_rain_picnic(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 1.0, "No rain — dry conditions"
    if p < 0.3:  return 0.6, f"{p:.1f} mm — light drizzle, might be acceptable"
    if p < 2.0:  return 0.2, f"{p:.1f} mm — rain expected, not ideal for picnic"
    return 0.0,               f"{p:.1f} mm — heavy rain, cancel the picnic"

def _score_wind_fishing(w):
    if w is None: return 0.5, "Wind unknown"
    if w < 5:    return 1.0, f"{w:.0f} m/s — calm — excellent fishing conditions"
    if w < 10:   return 0.8, f"{w:.0f} m/s — light wind, good casting conditions"
    if w < 15:   return 0.5, f"{w:.0f} m/s — moderate wind, casting more difficult"
    if w < 20:   return 0.2, f"{w:.0f} m/s — strong wind, difficult to fish"
    return 0.0,               f"{w:.0f} m/s — too windy for fishing"

def _score_rain_fishing(p):
    """Light rain is actually good for fishing — fish feed near surface."""
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 0.8, "Dry — fish may be less active near surface"
    if p < 1.0:  return 1.0, f"{p:.1f} mm — light rain — fish actively feeding"
    if p < 4.0:  return 0.6, f"{p:.1f} mm — moderate rain — acceptable conditions"
    if p < 8.0:  return 0.3, f"{p:.1f} mm — heavy rain — murky water, poor fishing"
    return 0.1,               f"{p:.1f} mm — very heavy rain — dangerous, seek shelter"

def _score_cloud_photography(c):
    if c is None: return 0.5, "Cloud cover unknown"
    if c < 15:   return 0.7, f"{c:.0f}% cloud — clear sky, harsh direct light midday"
    if c < 40:   return 0.9, f"{c:.0f}% cloud — light cloud, soft and even light"
    if c < 70:   return 1.0, f"{c:.0f}% cloud — overcast, ideal diffused light for portraits"
    if c < 90:   return 0.6, f"{c:.0f}% cloud — heavy cloud, may be too dark"
    return 0.3,               f"{c:.0f}% cloud — dense overcast, very flat light"

def _score_rain_photography(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 1.0, "No rain — equipment safe"
    if p < 0.3:  return 0.7, f"{p:.1f} mm — light drizzle, protect equipment"
    if p < 2.0:  return 0.3, f"{p:.1f} mm — rain — risk to camera equipment"
    return 0.0,               f"{p:.1f} mm — heavy rain — do not expose camera"

def _score_cloud_stargazing(c):
    if c is None: return 0.5, "Cloud cover unknown"
    if c < 10:   return 1.0, f"{c:.0f}% cloud — near clear sky, excellent visibility"
    if c < 25:   return 0.8, f"{c:.0f}% cloud — mostly clear, good stargazing"
    if c < 50:   return 0.5, f"{c:.0f}% cloud — partial cloud, interrupted views"
    if c < 75:   return 0.2, f"{c:.0f}% cloud — heavy cloud cover, poor visibility"
    return 0.0,               f"{c:.0f}% cloud — overcast, no stargazing possible"

def _score_humidity_stargazing(h):
    if h is None: return 0.5, "Humidity unknown"
    if h < 50:   return 1.0, f"{h:.0f}% humidity — dry air, sharp sky visibility"
    if h < 70:   return 0.8, f"{h:.0f}% humidity — good transparency"
    if h < 85:   return 0.5, f"{h:.0f}% humidity — some atmospheric blurring"
    return 0.2,               f"{h:.0f}% humidity — very humid, hazy sky"

def _score_rain_stargazing(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 1.0, "No precipitation"
    if p < 0.1:  return 0.3, f"{p:.1f} mm — light drizzle, clouds likely forming"
    return 0.0,               f"{p:.1f} mm — raining, no stargazing possible"

def _score_temp_gardening(t):
    if t is None: return 0.5, "Temperature unknown"
    if t < 0:    return 0.1, f"{t:.0f}°C — frozen ground, do not garden"
    if t < 5:    return 0.3, f"{t:.0f}°C — very cold, only essential tasks"
    if t < 10:   return 0.6, f"{t:.0f}°C — cool, suitable for light gardening"
    if t <= 25:  return 1.0, f"{t:.0f}°C — ideal gardening temperature"
    if t <= 32:  return 0.6, f"{t:.0f}°C — warm, garden early morning or evening"
    return 0.2,               f"{t:.0f}°C — too hot, risk of heat stress"

def _score_rain_gardening(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 0.9, "Dry — good for most gardening tasks"
    if p < 1.0:  return 1.0, f"{p:.1f} mm — light rain — natural watering, great for planting"
    if p < 4.0:  return 0.6, f"{p:.1f} mm — moderate rain — soil waterlogged, avoid digging"
    if p < 8.0:  return 0.2, f"{p:.1f} mm — heavy rain — stay indoors"
    return 0.0,               f"{p:.1f} mm — very heavy rain — dangerous outdoors"

def _score_temp_clothing(t):
    """Clothing is about what to wear, not a binary good/poor."""
    if t is None: return 0.5, "Temperature unknown"
    if t < 0:    return 0.2, f"{t:.0f}°C — heavy winter coat essential"
    if t < 5:    return 0.3, f"{t:.0f}°C — warm coat and layers needed"
    if t < 10:   return 0.5, f"{t:.0f}°C — jacket required"
    if t < 15:   return 0.6, f"{t:.0f}°C — light jacket recommended"
    if t < 20:   return 0.8, f"{t:.0f}°C — comfortable, light layers sufficient"
    if t < 26:   return 1.0, f"{t:.0f}°C — warm, t-shirt weather"
    return 0.7,               f"{t:.0f}°C — hot, light breathable clothing"

def _score_rain_clothing(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 1.0, "No rain"
    if p < 0.5:  return 0.7, f"{p:.1f} mm — light drizzle, umbrella useful"
    if p < 3.0:  return 0.4, f"{p:.1f} mm — rain, waterproof jacket needed"
    return 0.2,               f"{p:.1f} mm — heavy rain, full waterproofs essential"

def _score_wind_clothing(w):
    if w is None: return 0.5, "Wind unknown"
    if w < 5:    return 1.0, f"{w:.0f} m/s — calm"
    if w < 10:   return 0.9, f"{w:.0f} m/s — light breeze, adds slight chill"
    if w < 15:   return 0.7, f"{w:.0f} m/s — moderate wind, windbreaker useful"
    if w < 20:   return 0.5, f"{w:.0f} m/s — strong wind, feels significantly colder"
    return 0.3,               f"{w:.0f} m/s — very strong wind, warm windproof essential"

def _score_rain_driving(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 1.0, "Dry roads"
    if p < 1.0:  return 0.8, f"{p:.1f} mm — light rain, roads slightly wet"
    if p < 4.0:  return 0.6, f"{p:.1f} mm — moderate rain, reduce speed"
    if p < 8.0:  return 0.3, f"{p:.1f} mm — heavy rain, aquaplaning risk"
    return 0.1,               f"{p:.1f} mm — very heavy rain, consider not driving"

def _score_snow_driving(s):
    if s is None or s == 0: return 1.0, "No snow"
    if s < 0.5:  return 0.4, f"{s:.1f} mm snow — snow on roads, winter tyres needed"
    if s < 2.0:  return 0.2, f"{s:.1f} mm snow — significant snow, hazardous driving"
    return 0.0,               f"{s:.1f} mm snow — heavy snowfall, avoid driving"

def _score_wind_driving(g):
    if g is None: return 0.5, "Gust data unknown"
    if g < 15:   return 1.0, f"{g:.0f} m/s gusts — calm, normal driving"
    if g < 20:   return 0.8, f"{g:.0f} m/s gusts — light gusts, take care on bridges"
    if g < 25:   return 0.5, f"{g:.0f} m/s gusts — strong gusts, high vehicles at risk"
    if g < 30:   return 0.2, f"{g:.0f} m/s gusts — very strong gusts, dangerous for trucks"
    return 0.0,               f"{g:.0f} m/s gusts — extreme gusts, avoid driving if possible"

def _score_temp_dogwalk(t):
    if t is None: return 0.5, "Temperature unknown"
    if t < -5:   return 0.2, f"{t:.0f}°C — very cold, limit walk time for small breeds"
    if t < 2:    return 0.5, f"{t:.0f}°C — cold, boots recommended for sensitive paws"
    if t <= 22:  return 1.0, f"{t:.0f}°C — comfortable for dogs"
    if t <= 28:  return 0.6, f"{t:.0f}°C — warm, carry water for your dog"
    if t <= 32:  return 0.3, f"{t:.0f}°C — hot, walk early morning or late evening"
    return 0.1,               f"{t:.0f}°C — dangerous heat, risk of paw burns on pavement"

def _score_rain_dogwalk(p):
    if p is None: return 0.5, "Precipitation unknown"
    if p == 0:   return 1.0, "Dry — great for a walk"
    if p < 1.0:  return 0.8, f"{p:.1f} mm — light rain, most dogs don't mind"
    if p < 4.0:  return 0.5, f"{p:.1f} mm — moderate rain, keep walk short"
    return 0.2,               f"{p:.1f} mm — heavy rain, quick toilet break only"

def _score_wind_dogwalk(w):
    if w is None: return 0.5, "Wind unknown"
    if w < 10:   return 1.0, f"{w:.0f} m/s — calm, good walk conditions"
    if w < 15:   return 0.8, f"{w:.0f} m/s — breezy, fine for most dogs"
    if w < 20:   return 0.5, f"{w:.0f} m/s — strong wind, small dogs may struggle"
    return 0.2,               f"{w:.0f} m/s — very strong wind, keep dogs on lead"


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
    t = current.get("temperature_celsius")
    w = current.get("wind_speed_m_per_s")
    g = current.get("wind_gust_m_per_s")
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