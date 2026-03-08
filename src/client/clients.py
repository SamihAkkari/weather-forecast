
import logging
from src.config.config import Config
from src.client.base_client import BaseClient

logger = logging.getLogger(__name__)

class ObservationsClient(BaseClient):
    def __init__(self, api):
        super().__init__(api)
    
    def fetch_data(self, params):
        """Returns JSON response as dict"""
        if 'format' not in params.keys():
            params['format'] = 'json'
        elif params['format'] != 'json':
            raise ValueError ("The format requested is not available for get_json method")
        response = self.request(params)
        response.raise_for_status()
        return response.json()

class ForecastAromeClient(BaseClient):
    def __init__(self, api):
        super().__init__(api)
    
    def fetch_data(self, params):
        
        if 'format' not in params.keys():
            params['format'] = 'grib2'
        elif params['format'] != 'grib2':
            logger.error(f"Invalid format requested: {params['format']}")
            raise ValueError ("The format requested is not available for get_grib method")
        
        if 'referencetime' not in params.keys():
            logger.error("Missing required parameter: referencetime")
            raise ValueError ("The referencetime parameter is required for get_grib method")
        
        if 'time' not in params.keys():
            logger.error("Missing required parameter: time")
            raise ValueError ("The time parameter is required for get_grib method")

        response = self.request(params = params)
        if response.status_code == 200:
            logger.info("GRIB data fetched successfully")
            return response.content
        elif response.status_code == 404:
            logger.info("GRIB data not found for the given parameters")
            return None
        else:
            logger.error(f"Error fetching GRIB data: {response.status_code}")
            raise Exception(f"Error fetching GRIB data: {response.status_code}")
        