import sys
from src.api.api_factory import APIFactory
from src.client.clients import ForecastAromeClient
from src.ingestion.ingestor import ForecastIngestor
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
    force=True,
)

def make_client(service):
    return ForecastAromeClient(APIFactory.create("meteofrance_forecast_arome", service))

if __name__ == "__main__":
    try:
        description_client = make_client("0025SP1_available_data")
        data_clients = [make_client("0025SP1"), make_client("0025SP2")]
        ForecastIngestor(data_clients, description_client).run()
    except Exception:
        logging.getLogger("run_forecast").exception("Forecast run failed")
        sys.exit(1)