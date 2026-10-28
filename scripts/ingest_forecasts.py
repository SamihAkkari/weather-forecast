import os
import sys
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.api.api_factory import APIFactory
from src.client.clients import ForecastAromeClient
from src.ingestion.ingestor import ForecastIngestor
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




# description_api= APIFactory.create("meteofrance_forecast_arome", "0025SP1_available_data")
# description_client = ForecastAromeClient(description_api)

# data_api_SP1 = APIFactory.create("meteofrance_forecast_arome", "0025SP1")
# data_client_SP1 = ForecastAromeClient(data_api_SP1)

# data_api_SP2 = APIFactory.create("meteofrance_forecast_arome", "0025SP2")
# data_client_SP2 = ForecastAromeClient(data_api_SP2)

# data_clients = [data_client_SP1, data_client_SP2]

# # description_api= APIFactory.create("meteofrance_forecast_arome", "0025SP2_available_data")
# # description_client = ForecastAromeClient(description_api)

# ingestor = ForecastIngestor(data_clients, description_client)
# # ingestor.run_once()
# ingestor.run_loop()