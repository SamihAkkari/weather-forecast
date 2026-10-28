
import os
import sys
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.clients import ObservationsClient
from src.ingestion.ingestor import ObservationsIngestor
import logging

# handler = RotatingFileHandler(
#     "logs/app.log",
#     maxBytes=5 * 1024 * 1024,  # 5 MB
#     backupCount=5,
# )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout
    # handlers=[
    #     logging.StreamHandler(),
    #     handler,
    # ],
    # force = True
)

if __name__ == "__main__":
    try:
        api = APIFactory.create("meteofrance_observations", "stations_horaire")
        ObservationsIngestor(ObservationsClient(api)).run()
    except Exception:
        logging.getLogger("run_observations").exception("Observation run failed")
        sys.exit(1)

# api = APIFactory.create("meteofrance_observations", "stations_horaire")
# client = ObservationsClient(api)

# ingestor = ObservationsIngestor(client)
# ingestor.run_loop()
# ingestor.run_once()

