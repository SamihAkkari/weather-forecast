from fastapi import FastAPI
from src.data.getter import DatabaseGetter
from src.ingestion.time_manager import TimeManager
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/station-current-forecast/{station_id}")
def get_frontend_formatted_data_for_basicV(station_id: str):
    time = TimeManager.utc_now_truncated(to="hour")
    time = TimeManager.utc_to_france(time)
    time = TimeManager.convert_to_iso(time)
    data = DatabaseGetter.get_frontend_formatted_data_for_basicV(station_id, time = time)
    return data