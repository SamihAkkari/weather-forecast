"""
PV Production Estimator using pvlib PVWatts model.

Pipeline:
    1. De-accumulate GHI from cumulative J/m² → instantaneous W/m²
    2. Build a pvlib Location object from lat/lng/altitude
    3. Compute solar position for each timestep
    4. Decompose GHI into DNI and DHI using the Erbs model
    5. Compute Plane of Array (POA) irradiance using the Haydavies model
    6. Run PVWatts DC and AC power model
    7. Return hourly production (Wh) and total energy (kWh)

Why de-accumulate?
    AROME stores global_radiation_j_m2 as cumulative energy since run_time.
    pvlib expects instantaneous GHI in W/m² (power, not energy).
    Since our timestep is 1 hour:
        GHI_wm2[i] = (cumulative[i] - cumulative[i-1]) / 3600
    The first timestep has no previous value so we use cumulative[0] / 3600
    which assumes the accumulation started cleanly at run_time.

Why Erbs decomposition?
    We only have GHI (global horizontal irradiance) from AROME.
    pvlib needs DNI (direct normal) and DHI (diffuse horizontal) separately.
    Erbs is the standard decomposition model when only GHI is available.
    It uses the clearness index (GHI vs extraterrestrial radiation) to split.

Why Haydavies transposition?
    We need POA irradiance — irradiance hitting the tilted panel surface.
    Haydavies (also called Hay-Davies) is reliable for tilted surfaces
    and only requires DNI, DHI and GHI which we have after Erbs.
"""

import logging
import pandas as pd
import pvlib
from pvlib.location import Location
from pvlib.irradiance import erbs, haydavies, get_extra_radiation
from pvlib.solarposition import get_solarposition

logger = logging.getLogger(__name__)


def convert_ghi_from_to_instant(forecast: list[dict]) -> list[float]:
    """
    Converts GHI (J/m²) to
    instantaneous GHI (W/m²) for each hourly timestep.
    """
    ghi_wm2 = [
        float(entry.get("global_radiation_j_m2") / 3600)
        for entry in forecast
    ]
    return ghi_wm2

# ── Step 2 — Build time index ──────────────────────────────────────────────────

def build_time_index(forecast: list[dict]) -> pd.DatetimeIndex:
    """Timestamps are real UTC instants; pvlib needs tz-aware times."""
    times = pd.DatetimeIndex(pd.to_datetime([e["time_step_fr"] for e in forecast], utc=True))
    return times.tz_convert("Europe/Paris")
    
    # """
    # Extracts timestamps from forecast entries and builds a
    # timezone-aware DatetimeIndex that pvlib requires.

    # time_step_fr is in French local time (Europe/Paris).
    # We convert to UTC for pvlib solar position calculations
    # since pvlib expects UTC or timezone-aware times.
    # """  
    
    # times = pd.DatetimeIndex(
    # pd.to_datetime([entry["time_step_fr"] for entry in forecast])
    # ).tz_localize(None)
    
    # ambiguous = [True] * len(times)
    
    # times = times.tz_localize(
    #     "Europe/Paris",
    #     ambiguous=ambiguous
    # )
    
    # # times = pd.to_datetime([
    # #     entry["time_step_fr"] for entry in forecast
    # # ]).tz_localize(None)

    # # # If timestamps are naive (no timezone), localize to Paris time
    # # if times.tz is None:
    # #     times = times.tz_localize("Europe/Paris")
    # # else:
    # #     times = times.tz_convert("Europe/Paris")

    # return times

def buildInsight():
    return ""



# ── Step 3 — Core PV computation ──────────────────────────────────────────────

def compute_pv_production(
    forecast: list[dict],
    lat: float,
    lng: float,
    altitude: float,
    system_capacity_kw: float,
    inverter_capacity_kw: float, # AC power limit
    tilt: float,
    azimuth: float,
    losses_pct: float = 14.0,
    inverter_efficiency:float = 0.96,
    albedo: float = 0.25
) -> dict:
    """
    Main entry point. Computes hourly PV production from forecast data.

    Parameters
    ----------
    forecast : list of forecast dicts from DatabaseGetter
    lat, lng : location coordinates (from map click)
    altitude : station altitude in metres
    system_capacity_kw : installed PV capacity in kW (e.g. 3.0 for a 3kWp system)
    tilt : panel tilt angle in degrees (0=flat, 90=vertical)
    azimuth : panel azimuth in degrees (180=south, 90=east, 270=west)
    losses_pct : total system losses in percent (default 14% per PVWatts standard)

    Returns
    -------
    dict shaped for the frontend:
    {
        "hourly": [{"time": ..., "power_w": ..., "ghi_wm2": ...}, ...],
        "total_energy_kwh": float,
        "peak_power_w": float,
        "peak_hour": str,
    }
    """
    if not forecast:
        raise ValueError("Empty forecast — cannot compute PV production")

    logger.info(
        f"Computing PV production: {system_capacity_kw}kWp, "
        f"tilt={tilt}°, azimuth={azimuth}°, losses={losses_pct}%"
    )
    # import pdb
    # pdb.set_trace()
    # ── 1. De-accumulate GHI ──────────────────────────────────────────────
    # ghi_wm2 = deaccumulate_ghi(forecast, previous_cumulative)
    ghi_wm2 = convert_ghi_from_to_instant(forecast)

    # ── 2. Build time index ───────────────────────────────────────────────
    times = build_time_index(forecast)

    # ── 3. Build pvlib Location ───────────────────────────────────────────
    location = Location(
        latitude=lat,
        longitude=lng,
        tz="Europe/Paris",
        altitude=altitude,
        name="forecast_location",
    )

    # ── 4. Compute solar position ─────────────────────────────────────────
    # Returns: apparent_zenith, azimuth, elevation etc. for each timestep
    solar_position = get_solarposition(times, lat, lng, altitude)

    # ── 5. Extraterrestrial radiation ─────────────────────────────────────
    # Radiation that would reach Earth's surface with no atmosphere.
    # Used by Erbs decomposition as a reference.
    dni_extra = get_extra_radiation(times)

    # ── 6. Erbs decomposition: GHI → DNI + DHI ───────────────────────────
    # erbs() takes GHI, solar zenith, and extraterrestrial radiation
    # Returns a DataFrame with 'dni' and 'dhi' columns
    ghi_series = pd.Series(ghi_wm2, index=times)
    erbs_result = erbs(
        ghi=ghi_series,
        zenith=solar_position["apparent_zenith"],
        datetime_or_doy=times,
    )
    dni = erbs_result["dni"]
    dhi = erbs_result["dhi"]

    # ── 7. POA irradiance using Haydavies transposition ───────────────────
    # Converts horizontal irradiance to irradiance on the tilted panel surface
    poa_result = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
        dni=dni,
        ghi=ghi_series,
        dhi=dhi,
        dni_extra=dni_extra,
        albedo=0.25,
        model="haydavies",
    )
    
    # poa_result = haydavies(
    #     surface_tilt=tilt,
    #     surface_azimuth=azimuth,
    #     dhi=dhi,
    #     dni=dni,
    #     dni_extra=dni_extra,
    #     solar_zenith=solar_position["apparent_zenith"],
    #     solar_azimuth=solar_position["azimuth"],
    # )
    
    # poa_result is a Series of total POA irradiance in W/m²
    poa_global  = poa_result ["poa_global"].fillna(0).clip(lower=0)
    # poa_direct = poa_result ["poa_direct"].fillna(0).clip(lower=0)
    # poa_diffuse = poa_result ["poa_diffuse"].fillna(0).clip(lower=0)
    
    # poa_global = poa_result.fillna(0).clip(lower=0)

    # ── 8. PVWatts DC power model ─────────────────────────────────────────
    # PVWatts DC model: P_dc = capacity * (POA / 1000) * temp_correction
    # Temperature correction uses the Sandia cell temperature model.
    # We use the simplified approach: assume cell temp = air temp + 25°C
    # at 1000 W/m² irradiance (NOCT-based linear approximation).
    # This avoids needing wind speed in the cell temperature model,
    # keeping the computation robust when wind data is missing.

    system_capacity_w = system_capacity_kw * 1000.0

    air_temp = pd.Series(
        [float(e.get("temperature_celsius") or 25.0) for e in forecast],
        index=times
    )
    wind_speed = pd.Series(
        [float(e.get("wind_speed_m_per_s")) for e in forecast],
        index=times
    )

    cell_temp = pvlib.temperature.faiman(
        poa_global=poa_global,
        temp_air=air_temp,
        wind_speed=wind_speed ,
    )

    # NOCT-based cell temperature approximation
    # T_cell = T_air + (NOCT - 20) / 800 * POA
    # Standard NOCT = 45°C
    # noct = 45.0
    # cell_temp = air_temp + (noct - 20.0) / 800.0 * poa_global

    # Temperature coefficient for power (typical silicon: -0.004 per °C)
    # Reference temperature is 25°C (STC)
    temp_coeff = -0.004

    # DC power in watts
    # temp_factor = 1 + temp_coeff * (cell_temp - 25.0)
    # dc_power_w = system_capacity_w * (poa_global / 1000.0) * temp_factor
    # dc_power_w = dc_power_w.clip(lower=0)

    dc_power_w = pvlib.pvsystem.pvwatts_dc(
        effective_irradiance=poa_global,
        temp_cell=cell_temp,
        pdc0=system_capacity_w,
        gamma_pdc=temp_coeff,
    )

    # ── 9. PVWatts AC power (apply losses) ───────────────────────────────
    # losses_pct covers: soiling, shading, wiring, mismatch, inverter etc.
    # PVWatts applies them as a single derate factor
    derate_factor = 1.0 - (losses_pct / 100.0)
    dc_power_w_after_losses_w= (dc_power_w * derate_factor).clip(lower=0)

    inverter_pac0_w = inverter_capacity_kw * 1000
    inverter_pdc0_w = inverter_pac0_w / inverter_efficiency
    ac_power_w = pvlib.inverter.pvwatts(
        pdc=dc_power_w_after_losses_w,
        pdc0=inverter_pdc0_w,
        eta_inv_nom=inverter_efficiency,
    )

    # import pdb
    # pdb.set_trace()
    # Hypothetical AC power without the AC clipping limit
    zeta = dc_power_w_after_losses_w / inverter_pdc0_w
    
    eta = (
        inverter_efficiency / 0.9637
        * (
            -0.0162 * zeta
            - 0.0059 / zeta.where(zeta > 0, 1)
            + 0.9858
        )
    ).clip(lower=0, upper=1)
    unclipped_ac_power_w = (eta * dc_power_w_after_losses_w).clip(lower=0)
    
    # Instantaneous power lost to clipping (W)
    clipping_perc = (
        1 - ac_power_w / unclipped_ac_power_w.where(
            unclipped_ac_power_w > 0
        )
    ).mul(100).clip(lower=0).fillna(0)
    

    # ── 10. Build response ────────────────────────────────────────────────
    # Since timestep = 1 hour, power in W == energy in Wh for that hour
    hourly = []
    for i, (entry, power, clip_perc) in enumerate(zip(forecast, ac_power_w, clipping_perc)):
        hourly.append({
            "time":      str(entry.get("time_step_fr", "")),
            "power_w":   round(float(power), 1),
            "energy_wh": round(float(power), 1),  # 1h timestep: W == Wh
            "clipping_percentage": round(float(clip_perc)),
            "ghi_wm2":   round(ghi_wm2[i], 1),
            "poa_wm2":   round(float(poa_global.iloc[i]), 1),
        })



    total_energy_wh = sum(h["energy_wh"] for h in hourly)
    total_energy_kwh = total_energy_wh / 1000.0
 
    # Potential AC energy without clipping (kWh)
    unclipped_energy_kwh = unclipped_ac_power_w.sum() / 1000

    # Percentage of potential AC energy lost
    clipping_percentage_energy = (
        100 - round(100 * total_energy_kwh / unclipped_energy_kwh)
        if unclipped_energy_kwh > 0 else 0
    )    
    if clipping_percentage_energy == 0:
        clipping_message = "✓ No clipping detected"
    else:
        clipping_message = "⚠️ Clipping is likely"

    peak_entry = max(hourly, key=lambda h: h["power_w"])

    insight = buildInsight()

    return {
        "system": {
            "capacity_kw": system_capacity_kw,
            "tilt":        tilt,
            "azimuth":     azimuth,
            "losses_pct":  losses_pct,
        },
        "hourly":            hourly,
        "total_energy_kwh":  round(total_energy_kwh, 3),
        "energy_period_message": f"over {len(hourly)} forecast period",
        "peak_power_w":      round(peak_entry["power_w"], 1),
        "peak_hour":         peak_entry["time"],
        "energy_clipping_percent": round(clipping_percentage_energy),
        "clipping_message": clipping_message ,
        "insight_message": insight
    }