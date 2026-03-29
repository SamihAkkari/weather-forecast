from fastapi import FastAPI
from src.data.getter import DatabaseGetter

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

@app.get("/observations/{station_id}")
def get_observations(station_id: str):
    data, cur = DatabaseGetter.get_observations(station_id)
    columns = [desc[0] for desc in cur.description]
    result = []
    for row in data:
        record = dict(zip(columns, row))
        for key, value in record.items():
            if hasattr(value, "isoformat"):  # datetime
                record[key] = value.isoformat()
        result.append(record)
    return result