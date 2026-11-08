import sys
from src.api.api_factory import APIFactory
from src.client.clients import ObservationsClient
from src.ingestion.ingestor import ObservationsIngestor
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
    force=True,
)

if __name__ == "__main__":
    try:
        api = APIFactory.create("meteofrance_observations", "stations_horaire")
        ObservationsIngestor(ObservationsClient(api)).run()
    except Exception:
        logging.getLogger("run_observations").exception("Observation run failed")
        sys.exit(1)
