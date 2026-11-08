import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.processing.analysis_service import get_analysis_data
from src.processing.geography import is_inside_metropolitan_france
from src.processing.pv_service import get_pv_production_data
from src.processing.viewer_service import get_viewer_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("api")

app = FastAPI(title="Weather Forecast API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    # allow_origins=["http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


def ensure_in_france(lat: float, lng: float):
    if not is_inside_metropolitan_france(lat, lng):
        raise HTTPException(
            status_code=422,
            detail="Only metropolitan France is currently supported. Please select a location in France.",
        )


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
        return get_pv_production_data(
            lat=lat,
            lng=lng,
            system_capacity_kw=system_capacity_kw,
            inverter_capacity_kw=inverter_capacity_kw,
            tilt=tilt,
            azimuth=azimuth,
            losses_pct=losses_pct,
            inverter_efficiency=inverter_efficiency,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis")
def get_analysis(
    lat: float | None = None,
    lng: float | None = None,
    days: int = 7,
):
    """
    lat, lng : optional   if provided, finds nearest station.
               if omitted, aggregates over all stations.
    days     : how many past days to include in the analysis.
    """
    if lat is not None and lng is not None:
        ensure_in_france(lat, lng)
    try:
        return get_analysis_data(days=days, lat=lat, lng=lng)
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500)