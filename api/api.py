from fastapi import FastAPI
from src.data.getter import DatabaseGetter
from src.ingestion.time_manager import TimeManager
from fastapi.middleware.cors import CORSMiddleware
from src.processing import spatial

from src.processing.viewer_service import get_viewer_data
from src.data.getter import DatabaseGetter
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Weather Forecast API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

@app.get("/station-current-forecast")
def get_viewer_page_data(lat: float, lng: float):
    try:
        return get_viewer_data(lat, lng)
    except Exception as e:
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