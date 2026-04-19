from src.config.config import Config
from dataclasses import dataclass, field
from typing import Callable, Optional, Type
import logging
from src.data import models as data_models

logger = logging.getLogger(__name__)

@dataclass
class EndpointConfig:
    path: str
    record_class:    Optional[Type[data_models.BaseRecord]] = None      # <-- schema lives here
    required_params: list[str] = field(default_factory=list) # list of required parameters for this endpoint (ensures an empty list if it was not defined)
    optional_params: list[str] = field(default_factory=list) # list of optional parameters for this endpoint
    bronze_table: Optional[str] = None # target table for this endpoint's data
    return_response: Callable = lambda x: x.json() # function to process the raw response (default response.json())
    retry_frequency: Optional[int] = None   # seconds, None = not real-time
    update_frequency: Optional[int] = None   # seconds, None = not real-time
    max_retries: Optional[int] = None         # how many times to retry if no new data (None = infinite) 
    time_step: Optional[int] = None          # seconds between data points
    steps_back: Optional[int] = None         # how many steps back to tolerate

class MeteoFranceBase:
    def __init__(self, 
                 service: str,
                name = 'MétéoFrance',
                base_url = Config.METEOFRANCE_BASE_URL,
                auth_type = 'oauth',
                accept_header = Config.ACCEPT_HEADER,
                token_url = Config.METEOFRANCE_TOKEN_URL,
                token_data = Config.TOKEN_Data,
                token_headers = Config.TOKEN_HEADERS,
                timeout=30
                ):
        
        if service not in self.endpoints:
            available = ', '.join(self.endpoints.keys())
            raise ValueError(f"Unknown service '{service}'. Available: {available}")

        self.name = name
        self.base_url = base_url
        self.auth_type = auth_type
        self.accept_header = accept_header
        self.token_url = token_url
        self.token_data = token_data
        self.token_headers = token_headers
        self.timeout = timeout

        # Endpoint config unpacked from the descriptor for easy access
        self.service = service
        cfg: EndpointConfig = self.endpoints[service]
        self.record_class = cfg.record_class
        self.endpoint_path = cfg.path
        self.bronze_table = cfg.bronze_table
        self.required_params = cfg.required_params
        self.optional_params = cfg.optional_params
        self.return_response = cfg.return_response
        self.retry_frequency_seconds = cfg.retry_frequency
        self.update_frequency_seconds = cfg.update_frequency
        self.max_retries = cfg.max_retries
        self.time_step_seconds = cfg.time_step
        self.steps_back = cfg.steps_back

    @property
    def full_url(self) -> str:
        """
        Get full URL for an API endpoint
        
        Args:
            api_name: API identifier
            endpoint_name: Endpoint name
            
        Returns:
            Full URL
        """
        return f"{self.base_url}/{self.endpoint_path.lstrip('/')}"

    def validate_params(self, provided: dict) -> None:
        """Raise ValueError if any required param is missing."""
        missing = [p for p in self.required_params if p not in provided]
        if missing:
            logger.error(f"Endpoint '{self.service}' is missing required params: {missing}")
            raise ValueError(
                f"Endpoint '{self.service}' is missing required params: {missing}"
            )
        allowed = set(self.required_params) | set(self.optional_params)
        unknown = [p for p in provided if p not in allowed]
        if unknown:
            logger.warning(f"Endpoint '{self.service}' received unknown params: {unknown}")
            raise ValueError(f"Endpoint '{self.service}' received unknown params: {unknown}")

    def parse_response(self, response):
        """Apply the endpoint's return_response callable."""
        return self.return_response(response)

class MeteoFranceObservations(MeteoFranceBase):
    """MétéoFrance Observations API"""
    
    endpoints = {
        "bronze_liste-stations": EndpointConfig(
            path=Config.OBSERVATIONS_LISTESTATION_ENDPOINT,
            return_response=lambda x: x.json(),
            bronze_table=Config.STATIONS_TABLE_NAME,
            record_class = data_models.BronzeObservationListeStationsRecords
        ),
        "stations_infrahoraire-6m": EndpointConfig(
            path=Config.OBSERVATIONS_STATIONS_INFRAHORAIRE6m_ENDPOINT,
            required_params=["date", "format"],
            retry_frequency=60,
            max_retries = 4,
            time_step=360,
            steps_back=3,
            bronze_table=Config.OBSERVATIONS_TABLE_NAME_6m,
            record_class = data_models.ObservationInfrahoraire6mRecord
        ),
        "stations_horaire": EndpointConfig(
            path=Config.OBSERVATIONS_STATIONS_HORAIRE_ENDPOINT,
            required_params=["date", "format"],
            retry_frequency=120,
            max_retries = 20,
            time_step=3600,
            steps_back=3,
            bronze_table=Config.OBSERVATIONS_TABLE_NAME_HOURLY,
            record_class = data_models.ObservationHoraireRecord
        ),
        "infrahoraire-6m": EndpointConfig(
            path=Config.OBSERVATIONS_STATIONS_INFRAHORAIRE6m_ENDPOINT,
            return_response=lambda x: x.json(),
            record_class = None 
        ),
        "horaire": EndpointConfig(
            path=Config.OBSERVATIONS_STATIONS_HORAIRE_ENDPOINT,
            return_response=lambda x: x.json(),
            record_class = None
        ),
    }

    def __init__(self,
                 service,
                 app_id = Config.METEOFRANCE_APP_ID):
        super().__init__(service)
        """Return the endpoint path"""
        self.app_id = app_id

class MeteoFranceForecastArome(MeteoFranceBase):
    """MétéoFrance AROME package API"""
    
    endpoints = {
        "0025SP1": EndpointConfig(
            path=Config.FORECAST_AROME_PACKAGE_0025SP1_ENDPOINT,
            required_params=["referencetime", "time", "format"],
            return_response=lambda x: x.content,
            update_frequency=10800,
            bronze_table=Config.BRONZE_SP1_FORECAST_TABLE_NAME,
            record_class= data_models.SP1ForecastAromeRecord
        ),
        "0025SP1_available_data": EndpointConfig(
            path=Config.FORECAST_AROME_PACKAGE_0025SP1_AVAILABLE_DATA_ENDPOINT,
            update_frequency=10800,
            return_response=lambda x: x.json(),
            record_class= None 
        ),
        "0025SP2": EndpointConfig(
            path=Config.FORECAST_AROME_PACKAGE_0025SP2_ENDPOINT,
            required_params=["referencetime", "time", "format"],
            return_response=lambda x: x.content,
            update_frequency=10800,
            bronze_table=Config.BRONZE_SP2_FORECAST_TABLE_NAME,
            record_class= data_models.SP2ForecastAromeRecord
        ),
        "0025SP2_available_data": EndpointConfig(
            path=Config.FORECAST_AROME_PACKAGE_0025SP2_AVAILABLE_DATA_ENDPOINT,
            update_frequency=10800,
            return_response=lambda x: x.json(),
            record_class= None 
        ),
    }   
    
    def __init__(self,
                 service,
                 app_id = Config.METEOFRANCE_APP_ID):
        super().__init__(service)
        """Return the endpoint path"""
        self.app_id = app_id

class MeteoFranceRadar(MeteoFranceBase):
    """MétéoFrance Observations API"""
    def __init__(self):
        raise NotImplementedError()