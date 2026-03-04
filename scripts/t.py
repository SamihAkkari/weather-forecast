import requests
import xarray as xr

url = "https://public-api.meteofrance.fr/previnum/DPPaquetAROME/v1/models/AROME/grids/0.025/packages/SP1/productARO"

params = {
    "referencetime": "2026-03-04T15:00:00Z",
    "time": "07H12H",
    "format": "grib2"
}

headers = {
    "Authorization": "Bearer eyJ4NXQiOiJOelU0WTJJME9XRXhZVGt6WkdJM1kySTFaakZqWVRJeE4yUTNNalEyTkRRM09HRmtZalkzTURkbE9UZ3paakUxTURRNFltSTVPR1kyTURjMVkyWTBNdyIsImtpZCI6Ik56VTRZMkkwT1dFeFlUa3paR0kzWTJJMVpqRmpZVEl4TjJRM01qUTJORFEzT0dGa1lqWTNNRGRsT1RnelpqRTFNRFE0WW1JNU9HWTJNRGMxWTJZME13X1JTMjU2IiwidHlwIjoiYXQrand0IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIwMjkwYjA1Ni0wODI5LTQ4OWQtOTYzZS01MGZjY2EyZmQ1ZTciLCJhdXQiOiJBUFBMSUNBVElPTiIsImF1ZCI6Im1kbXpQSU0zcEF6NmZxcVBiTmxCbEwwODRwa2EiLCJuYmYiOjE3NzI2NjY1MDUsImF6cCI6Im1kbXpQSU0zcEF6NmZxcVBiTmxCbEwwODRwa2EiLCJzY29wZSI6ImRlZmF1bHQiLCJpc3MiOiJodHRwczpcL1wvcG9ydGFpbC1hcGkubWV0ZW9mcmFuY2UuZnJcL29hdXRoMlwvdG9rZW4iLCJleHAiOjE3NzI2NzAxMDUsImlhdCI6MTc3MjY2NjUwNSwianRpIjoiMjg3Y2JhZmItN2YzOS00ZDllLWEzMDEtMTk2OGE0NzY3ZDMxIiwiY2xpZW50X2lkIjoibWRtelBJTTNwQXo2ZnFxUGJObEJsTDA4NHBrYSJ9.N8K9QugryWVVW36fT-a1f4le6NElkmQ-hElZPYyaTR9zueQ5oGyiqS9b5rZIADQEIm4DHsFojHKlscHwzE13wP8Sg_oiKmCoshM8DCdgkg3brE2Dke-Pjmr0dzNq_EzY3hbTywkmWgFzqSeUhBiRixFTibz94IWus0x1iskYImWs4h5PhNfcaO1HstZx4MqSLNrtRyzVu3slVPDOMkZMI1rDdAGQ8tJxERR3OGX1irFBEIiUUc0kunlNh6ehiWCxul5ffJWmOeF_YhnJqi47b3RTFCzP7d_c6B8upYahOBTTVALIO71vOYft2tnsgaKiLPV1Ph0buXCTCJXBAzs2Vg"
}

r = requests.get(url, params=params, headers=headers, allow_redirects=True)

open("file.grib2", "wb").write(r.content)





import cfgrib
import xarray as xr

def load_arome_forecast(filepath: str) -> dict[str, xr.Dataset]:
    """
    Load AROME GRIB2 file into logically grouped datasets.
    Industry practice: split by physical meaning, not by cfgrib internals.
    """
    datasets = cfgrib.open_datasets(filepath)
    
    grouped = {
        'surface_instant': [],
        'surface_accum': [],
        '2m': [],
        '10m': [],
        'pressure_levels': [],
        'other': []
    }
    
    for ds in datasets:
        vars_ = set(ds.data_vars)
        
        if any(v in vars_ for v in ['u10', 'v10', 'fg10', 'efg10']):
            grouped['10m'].append(ds)
        elif any(v in vars_ for v in ['t2m', 'r2', 'd2m']):
            grouped['2m'].append(ds)
        elif any(v in vars_ for v in ['tp', 'ssrd', 'tsnowp']):
            grouped['surface_accum'].append(ds)
        elif 'isobaricInhPa' in ds.coords:
            grouped['pressure_levels'].append(ds)
        else:
            grouped['surface_instant'].append(ds)
    
    # Merge within each group
    result = {}
    for group, ds_list in grouped.items():
        if ds_list:
            try:
                result[group] = xr.merge(ds_list)
            except Exception:
                # If merge fails, keep as list — don't force incompatible data
                result[group] = ds_list
    
    return result


# Usage
forecast = load_arome_forecast('file.grib2')

t2m   = forecast['2m']['t2m']        # 2m temperature
tp    = forecast['surface_accum']['tp']  # total precip
u10   = forecast['10m']['u10']        # 10m wind u-component


# Nearest point to a specific location (most common in practice)
lat, lon = 48.85, 2.35  # Paris

u10_point = u10.sel(
    latitude=lat,
    longitude=lon,
    method='nearest'
)
# Shape: (step: 7) — all forecast steps for that point

# Get as numpy array
u10_point.values  # array in m/s



