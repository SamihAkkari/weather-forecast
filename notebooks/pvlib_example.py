# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 01:33:21 2026

@author: sakkari
"""


import numpy as np
import pandas as pd
import pvlib


def forecast_pv(
    forecast: pd.DataFrame,
    latitude: float,
    longitude: float,
    timezone: str,
    peak_power_kwp: float,
    tilt_deg: float,
    azimuth_deg: float,
    inverter_ac_kw: float | None = None,
    performance_losses: float = 0.14,
    ssrd_is_hourly_accumulation: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    forecast index: timezone-aware forecast timestamps.
    Required columns:
        ssrd: J/m²
        t2m: K (Kelvin)
        si10: m/s

    Assumptions:
        - ssrd represents energy accumulated during each preceding hour.
        - peak_power_kwp is installed DC capacity in kWp.
        - azimuth_deg follows pvlib: 180=south, 90=east, 270=west.
        - hourly timestamps represent the END of each accumulation interval.
    """

    df = forecast.copy().sort_index()

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("forecast must have a DatetimeIndex")

    if df.index.tz is None:
        raise ValueError(
            "Timestamps must be timezone-aware. Localize them correctly first."
        )

    required = {"ssrd", "t2m", "si10"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    # Convert accumulated solar energy into interval-average GHI.
    if ssrd_is_hourly_accumulation:
        df["ghi"] = df["ssrd"].clip(lower=0) / 3600.0
    else:
        # If ssrd is cumulative since initialization, difference it first.
        # This branch assumes each timestamp is an accumulation endpoint.
        df["ghi"] = (
            df["ssrd"].diff().clip(lower=0)
            / df.index.to_series().diff().dt.total_seconds()
            * 3600
        )

    # AROME t2m is commonly supplied in Kelvin; confirm your data units.
    df["temp_air"] = df["t2m"] - 273.15
    df["wind_speed"] = df["si10"].clip(lower=0)

    site = pvlib.location.Location(
        latitude=latitude,
        longitude=longitude,
        tz=timezone,
    )

    solar = site.get_solarposition(df.index)
    zenith = solar["apparent_zenith"].clip(upper=90)

    # Estimate diffuse horizontal irradiance from GHI.
    erbs = pvlib.irradiance.erbs(
        ghi=df["ghi"],
        zenith=zenith,
        datetime_or_doy=df.index,
    )

    df["dhi"] = erbs["dhi"].clip(lower=0)
    df["dni"] = erbs["dni"].clip(lower=0)

    # Nighttime and physically invalid values.
    night = solar["apparent_zenith"] >= 90
    df.loc[night, ["ghi", "dhi", "dni"]] = 0

    # Calculate irradiance on the tilted PV plane.
    dni_extra = pvlib.irradiance.get_extra_radiation(df.index)

    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt_deg,
        surface_azimuth=azimuth_deg,
        solar_zenith=solar["apparent_zenith"],
        solar_azimuth=solar["azimuth"],
        dni=df["dni"],
        ghi=df["ghi"],
        dhi=df["dhi"],
        dni_extra=dni_extra,
        model="perez",
    )

    df["poa_global"] = poa["poa_global"].clip(lower=0)
    df["poa_direct"] = poa["poa_direct"].clip(lower=0)
    df["poa_diffuse"] = poa["poa_diffuse"].clip(lower=0)

    # PVWatts DC model.
    pdc0_w = peak_power_kwp * 1000
    gamma_pdc = -0.0035  # illustrative temperature coefficient per °C

    cell_temp = pvlib.temperature.faiman(
        poa_global=df["poa_global"],
        temp_air=df["temp_air"],
        wind_speed=df["wind_speed"],
    )

    pdc_w = pvlib.pvsystem.pvwatts_dc(
        effective_irradiance=df["poa_global"],
        temp_cell=cell_temp,
        pdc0=pdc0_w,
        gamma_pdc=gamma_pdc,
    )

    # Simple DC-to-AC conversion; replace with inverter-specific model if known.
    inverter_efficiency = 0.96
    pac_w = (pdc_w * inverter_efficiency).clip(lower=0)

    if inverter_ac_kw is not None:
        pac_w = pac_w.clip(upper=inverter_ac_kw * 1000)

    df["cell_temp_c"] = cell_temp
    df["pv_power_kw"] = pac_w / 1000.0

    # Energy for each interval: power × interval duration.
    # This assumes power represents the average over the preceding interval.
    interval_hours = (
        df.index.to_series().diff().dt.total_seconds() / 3600
    )
    interval_hours.iloc[0] = 1.0  # explicitly assumes first interval is 1 h
    df["interval_hours"] = interval_hours

    df["pv_energy_kwh"] = df["pv_power_kw"] * df["interval_hours"]
    df["date"] = df.index.tz_convert(timezone).date

    daily = df.groupby("date").agg(
        pv_energy_kwh=("pv_energy_kwh", "sum"),
        forecast_hours=("pv_energy_kwh", "count"),
    )

    daily["complete_24h"] = daily["forecast_hours"] == 24

    return df, daily


if __name__ == "__main__":
    # Replace with your actual AROME forecast records.
    times = pd.date_range(
        "2026-10-23 08:00",
        periods=12,
        freq="h",
        tz="Europe/Paris",
    )

    example = pd.DataFrame({
        "ssrd": [
            0, 0, 100_000, 400_000, 800_000, 1_200_000,
            1_600_000, 1_800_000, 1_500_000, 900_000,
            300_000, 50_000,
        ],
        "t2m": [283.15] * 12,
        "si10": [3.0] * 12,
    }, index=times)

    hourly, daily = forecast_pv(
        forecast=example,
        latitude=45.812,
        longitude=8.628,
        timezone="Europe/Paris",
        peak_power_kwp=10,
        tilt_deg=30,
        azimuth_deg=180,  # south-facing
        inverter_ac_kw=8,
    )

    print(hourly[[
        "ghi", "dhi", "dni", "poa_global",
        "cell_temp_c", "pv_power_kw", "pv_energy_kwh",
    ]].round(2))

    print("\nDaily totals:")
    print(daily.round(2))
