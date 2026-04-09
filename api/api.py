from fastapi import FastAPI
from src.data.getter import DatabaseGetter
from src.ingestion.time_manager import TimeManager

app = FastAPI(title="Weather Forecast API", version="1.0.0")

##TODO: WARNING: I am adding transformation logic in these APIs; this needs to be revised

@app.get("/stations")
def get_stations():
    stations = DatabaseGetter.get_stations()
    return {
        station.station_id: {
            "name": station.name,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude
        }
        for station in stations
    }

@app.get("/station-current-forecast/{station_id}")
def get_frontend_formatted_data_for_basicV(station_id: str):
    time = TimeManager.utc_now_truncated(to="minute")
    data = DatabaseGetter.get_frontend_formatted_data_for_basicV(station_id, time = time)
    return data