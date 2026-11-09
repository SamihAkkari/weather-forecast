"""Estimate hourly solar production from forecast irradiance with pvlib.

The forecast provides global horizontal irradiance (GHI). Erbs estimates its
direct and diffuse components, Hay-Davies transposes them to the panel plane,
and PVWatts estimates DC and AC output.
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

def build_time_index(forecast: list[dict]) -> pd.DatetimeIndex:
    """Timestamps are real UTC instants; pvlib needs tz-aware times."""
    times = pd.DatetimeIndex(pd.to_datetime([e["time_step_fr"] for e in forecast], utc=True))
    return times.tz_convert("Europe/Paris")

# Assumptions used in the production comparison message.
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
    """Estimate hourly PV output and aggregate energy for the forecast period.

    ``forecast`` must contain hourly timestamps, irradiance, temperature, and
    wind speed. Coordinates and altitude define solar position; the remaining
    parameters describe the PV system. The result includes hourly estimates,
    total energy, peak output, inverter clipping, and a summary message.
    """
    if not forecast:
        raise ValueError("Empty forecast   cannot compute PV production")

    logger.info(
        f"Computing PV production: {system_capacity_kw}kWp, "
        f"tilt={tilt}°, azimuth={azimuth}°, losses={losses_pct}%"
    )
    ghi_wm2 = convert_ghi_to_wm2(forecast)

    times = build_time_index(forecast)

    solar_position = get_solarposition(times, lat, lng, altitude)

    dni_extra = get_extra_radiation(times)

    ghi_series = pd.Series(ghi_wm2, index=times)
    erbs_result = erbs(
        ghi=ghi_series,
        zenith=solar_position["apparent_zenith"],
        datetime_or_doy=times,
    )
    dni = erbs_result["dni"]
    dhi = erbs_result["dhi"]

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
    
    poa_global  = poa_result ["poa_global"].fillna(0).clip(lower=0)

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

    # Typical silicon temperature coefficient relative to the 25°C reference.
    temp_coeff = -0.004

    dc_power_w = pvlib.pvsystem.pvwatts_dc(
        effective_irradiance=poa_global,
        temp_cell=cell_temp,
        pdc0=system_capacity_w,
        gamma_pdc=temp_coeff,
    )

    # Apply aggregate system losses before converting DC to AC power.
    derate_factor = 1.0 - (losses_pct / 100.0)
    dc_power_w_after_losses_w= (dc_power_w * derate_factor).clip(lower=0)

    inverter_pac0_w = inverter_capacity_kw * 1000
    inverter_pdc0_w = inverter_pac0_w / inverter_efficiency
    ac_power_w = pvlib.inverter.pvwatts(
        pdc=dc_power_w_after_losses_w,
        pdc0=inverter_pdc0_w,
        eta_inv_nom=inverter_efficiency,
    )

    # Estimate AC output without the inverter clipping limit.
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
    
    clipping_perc = (
        1 - ac_power_w / unclipped_ac_power_w.where(
            unclipped_ac_power_w > 0
        )
    ).mul(100).clip(lower=0).fillna(0)
    

    hourly = []
    for i, (entry, power, clip_perc) in enumerate(zip(forecast, ac_power_w, clipping_perc)):
        hourly.append({
            "time":      str(entry.get("time_step_fr", "")),
            "power_w":   round(float(power), 1),
            "energy_wh": round(float(power), 1),
            "clipping_percentage": round(float(clip_perc)),
            "ghi_wm2":   round(ghi_wm2[i], 1),
            "poa_wm2":   round(float(poa_global.iloc[i]), 1),
        })



    total_energy_wh = sum(h["energy_wh"] for h in hourly)
    total_energy_kwh = total_energy_wh / 1000.0
 
    unclipped_energy_kwh = unclipped_ac_power_w.sum() / 1000

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