from fastapi import FastAPI
from src.data.getter import DatabaseGetter
from src.ingestion.time_manager import TimeManager
from fastapi.middleware.cors import CORSMiddleware
from src.processing import spatial
from src.processing.analysis_processor import compute_analysis

from src.processing.viewer_service import get_viewer_data
from src.data.getter import DatabaseGetter
from fastapi import FastAPI, HTTPException

from src.processing.spatial import find_nearest_station
from src.config.config import Config
from src.processing.pv_processor import compute_pv_production

from src.processing import utils 

from src.processing.spatial import GeoUtils

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("api")

app = FastAPI(title="Weather Forecast API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

##TODO: WARNING: I am adding transformation logic in these APIs; this needs to be revised

# @app.get("/stations")
# def get_stations():
#     stations = DatabaseGetter.get_stations_to_show_on_map_in_basicV()
#     data = []
#     for station in stations:
#         data.append({
#             "id": station["station_id"],
#             "name": station["name"],
#             "latitude": station["latitude"],
#             "longitude": station["longitude"],
#             "altitude": station["altitude"]
#         }
#         )
#     return data
def ensure_in_france(lat: float, lng: float):
    if not GeoUtils.is_inside_france(lat, lng):
        raise HTTPException(
            status_code=422,
            detail="Only metropolitan France is currently supported. Please select a location in France.",
        )
    # b = Config.FRANCE_BOUNDS
    # if not (b["min_lat"] <= lat <= b["max_lat"] and b["min_lon"] <= lng <= b["max_lon"]):
    #     raise HTTPException(
    #         status_code=422,
    #         detail="Only metropolitan France is currently supported. Please select a location in France.",
    #     )

@app.get("/station-current-forecast")
def get_viewer_page_data(lat: float, lng: float):
    ensure_in_france(lat, lng)
    try:
        return get_viewer_data(lat, lng)
    except LookupError as e:                
        raise HTTPException(status_code=503, detail=str(e))    
    except Exception as e:
        logger.exception("station-current-forecast failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/pv-production")
def get_pv_production(
    lat: float,
    lng: float,
    system_capacity_kw: float,
    inverter_capacity_kw: float,
    tilt: float,
    azimuth: float,
    losses_pct: float = 14.0,
    inverter_efficiency:float = 0.96

):
    ensure_in_france(lat, lng)
    try:
        stations = DatabaseGetter.get_stations()
        nearest = find_nearest_station(stations, lat, lng)

        # current_time = TimeManager.current_france_time_iso(time_truncation="hour")
        current_time = TimeManager.current_utc_iso("hour")

        forecast_raw, cur = DatabaseGetter.get_forecasts_at_time_step(
            station_id=nearest.station_id,
            fromm=Config.SILVER_FORECAST_AROME_TABLE_NAME,
            time=current_time,
            exactly_at_time=False,
        )
        forecast = DatabaseGetter.transform_data_to_list_of_dict(forecast_raw, cur)

        if not forecast:
            raise LookupError("No forecast data is available yet for this location. Please try again later.")

        # forecast = utils.unaccumulate(forecast, "global_radiation_j_m2", nearest.station_id)

        # # Get the run_time of this forecast so we can find the previous entry
        # # run_time comes from the first forecast entry
        # run_time = forecast[0].get("run_time")

        # # Fetch the cumulative radiation value just before our slice starts
        # # so the first entry in our slice is correctly de-accumulated
        # previous_cumulative = DatabaseGetter.get_previous_cumulative(
        #     station_id=nearest.station_id,
        #     run_time=run_time,
        #     current_time=forecast[0].get("time_step_fr"),
        #     variable_name = "global_radiation_j_m2"
        # )

        altitude = float(nearest.altitude or 0)

        result = compute_pv_production(
            forecast=forecast,
            lat=lat,
            lng=lng,
            altitude=altitude,
            system_capacity_kw=system_capacity_kw,
            inverter_capacity_kw = inverter_capacity_kw,
            tilt=tilt,
            azimuth=azimuth,
            losses_pct=losses_pct,
            inverter_efficiency = inverter_efficiency
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"PV production error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/analysis")
# def get_analysis(lat: float, lng: float, days: str):
#     """
#     lat, lng: coordinates the user clicked or searched
#     run_time: ISO string like "2026-04-21T00:00" from the datetime picker
#     """

#     # Step 1 - Get nearest station of the selected location
#     stations = DatabaseGetter.get_stations()
#     nearest_station = spatial.find_nearest_station(stations, lat, lng)

#     # Step 2 — Get data for the nearest station and the current time  
#     data = DatabaseGetter.get_frontend_formatted_data_for_analysis(nearest_station, int(days))
#     return data


@app.get("/analysis")
def get_analysis(
    lat: float | None = None,
    lng: float | None = None,
    days: int = 7,
):
    """
    lat, lng : optional — if provided, finds nearest station.
               if omitted, aggregates over all stations.
    days     : how many past days to include in the analysis.
    """
    if lat is not None and lng is not None:
        ensure_in_france(lat, lng)      # <-- new
    try:
        station_id = None

        if lat is not None and lng is not None:
            stations = DatabaseGetter.get_stations()
            nearest  = find_nearest_station(stations, lat, lng)
            station_id = nearest.station_id
            # logger.info(f"Analysis for station {station_id}")
        else:
            pass
            # logger.info("Analysis for all stations")

        result = compute_analysis(
            days=days,
            station_id=station_id,
            forecast_table=f"{Config.SILVER_SCHEMA}.{Config.SILVER_FORECAST_AROME_TABLE_NAME}",
            obs_table=f"{Config.SILVER_SCHEMA}.{Config.OBSERVATIONS_TABLE_NAME_HOURLY}",
        )
        return result

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500)