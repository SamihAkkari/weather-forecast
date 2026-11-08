
import logging
from src.client.base_client import BaseClient

logger = logging.getLogger(__name__)

class ObservationsClient(BaseClient):
    def __init__(self, api):
        super().__init__(api)
    
    def fetch_data(self, params):
        """Returns JSON response as dict"""
        params = dict(params)
        params.setdefault("format", "json")
        if params["format"] != "json":
            raise ValueError("The format requested is not available for get_json method")

        self.api.validate_params(params)
        response = self.request(params)
        response.raise_for_status()
        return self.api.parse_response(response)

class ForecastAromeClient(BaseClient):
    def __init__(self, api):
        super().__init__(api)
    
    def fetch_data(self, params: dict | None = None):
        params = {} if params is None else dict(params)
        self.api.validate_params(params)

        response = self.request(params = params)
        if response.status_code == 200:
            logger.info("Data fetched successfully")
            return self.api.parse_response(response)
        elif response.status_code == 404:
            logger.info("Data not found for the given parameters")
            return None
        else:
            logger.error(f"Error fetching data: {response.status_code}")
            raise Exception(f"Error fetching data: {response.status_code}")
        