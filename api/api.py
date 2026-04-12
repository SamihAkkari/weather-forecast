from fastapi import FastAPI
from src.data.getter import DatabaseGetter
from src.ingestion.time_manager import TimeManager
from fastapi.middleware.cors import CORSMiddleware
from src.processing import spatial

app = FastAPI(title="Weather Forecast API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

##TODO: WARNING: I am adding transformation logic in these APIs; this needs to be revised

@app.get("/stations")
def get_stations():
    stations = DatabaseGetter.get_stations_to_show_on_map_in_basicV()
    data = []
    for station in stations:
        data.append({
            "id": station["station_id"],
            "name": station["name"],
            "latitude": station["latitude"],
            "longitude": station["longitude"],
            "altitude": station["altitude"]
        }
        )
    return data

@app.get("/station-current-forecast")
def get_frontend_formatted_data_for_basicV(lat: float, lng: float):
    # Get current time 
    time = TimeManager.current_france_time_iso(time_truncation="hour")
    
    # Get longitude and latitude of selected location
    # ...

    # Get elevatino of the selected location
    # ...

    # Get nearest station of the selected location
    stations = DatabaseGetter.get_stations()
    nearest_station = spatial.find_nearest_station(stations, lat, lng)

    # Get data for the nearest station and the current time    
    data = DatabaseGetter.get_frontend_formatted_data_for_basicV(nearest_station, time = time)
    return data