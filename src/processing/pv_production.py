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
    We need POA irradiance   irradiance hitting the tilted panel surface.
    Haydavies (also called Hay-Davies) is reliable for tilted surfaces
    and only requires DNI, DHI and GHI which we have after Erbs.
"""

import logging
import pandas as pd
import pvlib
from pvlib.irradiance import erbs, get_extra_radiation
from pvlib.solarposition import get_solarposition

logger = logging.getLogger(__name__)


def convert_ghi_to_wm2(forecast: list[dict]) -> list[float]:
    """
    Convert hourly GHI energy (J/m²) to average irradiance (W/m²).
    """
    return [
        float(entry.get("global_radiation_j_m2") / 3600)
        for entry in forecast
    ]

# ── Step 2   Build time index ──────────────────────────────────────────────────

def build_time_index(forecast: list[dict]) -> pd.DatetimeIndex:
    """Timestamps are real UTC instants; pvlib needs tz-aware times."""
    times = pd.DatetimeIndex(pd.to_datetime([e["time_step_fr"] for e in forecast], utc=True))
    return times.tz_convert("Europe/Paris")

# Rounded, editable assumptions used only for the comparison sentence
HOUSEHOLD_KWH_PER_DAY = 13.0   # roughly 4,700 kWh per year for an average French household
EV_KM_PER_KWH = 6.0            # about 16-17 kWh per 100 km, mixed driving

def build_insight(total_kwh, capacity_kw, n_hours, clipping_pct):
    if total_kwh < 0.05:
        return "Almost no production is expected over this period (night-time or very cloudy weather)."
    per_kwp = total_kwh / capacity_kw
    per_day = total_kwh / max(n_hours, 1) * 24
    household_pct = per_day / HOUSEHOLD_KWH_PER_DAY * 100
    km = total_kwh * EV_KM_PER_KWH
    text = (
        f"Over the next {n_hours} hours your {capacity_kw:g} kWp system is forecast to produce about "
        f"{total_kwh:.1f} kWh ({per_kwp:.1f} kWh per kWp). That is on average {per_day:.1f} kWh per day, "
        f"about {household_pct:.0f}% of the daily electricity use of an average French household, "
        f"or roughly {km:.0f} km in an electric car."
    )
    if clipping_pct >= 1:
        text += (f" About {clipping_pct}% of the potential energy is lost to inverter clipping; "
                 "a larger inverter would capture more.")
    return text + " This is an estimate from the AROME forecast; real output also depends on shading and soiling."



# ── Step 3   Core PV computation ──────────────────────────────────────────────

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
        raise ValueError("Empty forecast   cannot compute PV production")

    logger.info(
        f"Computing PV production: {system_capacity_kw}kWp, "
        f"tilt={tilt}°, azimuth={azimuth}°, losses={losses_pct}%"
    )
    # ── 1. Convert GHI energy to average irradiance ────────────────────────
    ghi_wm2 = convert_ghi_to_wm2(forecast)

    # ── 2. Build time index ───────────────────────────────────────────────
    times = build_time_index(forecast)

    # ── 3. Compute solar position ─────────────────────────────────────────
    # Returns: apparent_zenith, azimuth, elevation etc. for each timestep
    solar_position = get_solarposition(times, lat, lng, altitude)

    # ── 4. Extraterrestrial radiation ─────────────────────────────────────
    # Radiation that would reach Earth's surface with no atmosphere.
    # Used by Erbs decomposition as a reference.
    dni_extra = get_extra_radiation(times)

    # ── 5. Erbs decomposition: GHI → DNI + DHI ───────────────────────────
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

    # ── 6. POA irradiance using Haydavies transposition ───────────────────
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
        albedo=albedo,
        model="haydavies",
    )
    
    # poa_result is a Series of total POA irradiance in W/m²
    poa_global  = poa_result ["poa_global"].fillna(0).clip(lower=0)

    # ── 7. PVWatts DC power model ─────────────────────────────────────────
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

    # Temperature coefficient for power (typical silicon: -0.004 per °C)
    # Reference temperature is 25°C (STC)
    temp_coeff = -0.004

    dc_power_w = pvlib.pvsystem.pvwatts_dc(
        effective_irradiance=poa_global,
        temp_cell=cell_temp,
        pdc0=system_capacity_w,
        gamma_pdc=temp_coeff,
    )

    # ── 8. PVWatts AC power (apply losses) ───────────────────────────────
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
    

    # ── 9. Build response ────────────────────────────────────────────────
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
    if clipping_percentage_energy < 1:
        clipping_message = "✓ No significant clipping detected"
    elif clipping_percentage_energy < 5:
        clipping_message = "Minor clipping"
    else:
        clipping_message = "⚠️ Clipping: consider a larger inverter"

    peak_entry = max(hourly, key=lambda h: h["power_w"])

    insight = build_insight(total_energy_kwh, system_capacity_kw, len(hourly), clipping_percentage_energy)

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