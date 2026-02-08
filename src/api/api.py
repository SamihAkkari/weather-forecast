"""
API Catalog - Maps API names to their configurations
Separate from Config because this is API metadata, not environment config
"""

from typing import Dict, NamedTuple
from src.config.config import Config

class API:
    """Generic API base class"""
    def __init__(
        self,
        name: str,
        base_url: str,
        auth_type: str,
        selected_endpoint_name: str,  # ← active endpoint for THIS instance
        endpoints: Dict[str, str],
        app_id: str = '',
        accept_header: Dict[str, str] = None,
        token_url: str = '',
        token_data: Dict[str, str] = None,
        token_headers: Dict[str, str] = None,
        timeout: int = 30
    ):
        self.name = name
        self.base_url = base_url
        self.auth_type = auth_type
        self.selected_endpoint_name = selected_endpoint_name
        self.endpoints = endpoints
        self.app_id = app_id
        self.accept_header = accept_header
        self.token_url = token_url
        self.token_data = token_data or {}
        self.token_headers = token_headers or {}
        self.timeout = timeout

    def __post_init__(self):
        if self.selected_endpoint_name not in self.endpoints:
            raise ValueError(
                f"Unknown endpoint '{self.selected_endpoint_name}' for API '{self.name}'. "
                f"Available: {', '.join(self.endpoints.keys())}"
            )

    def get_endpoint_url(self) -> str:
        """
        Get endpoint path for an API
        
        Args:
            api_name: API identifier
            endpoint_name: Endpoint name ('observations', 'forecast', etc.)
            
        Returns:
            Endpoint path
        """
        return self.endpoints[self.selected_endpoint_name]

    def get_full_url(self) -> str:
        """
        Get full URL for an API endpoint
        
        Args:
            api_name: API identifier
            endpoint_name: Endpoint name
            
        Returns:
            Full URL
        """
        endpoint_url = self.get_endpoint_url()
        return f"{self.base_url}/{endpoint_url.lstrip('/')}"

class MeteoFranceAPI(API):
    """Specific configuration for MétéoFrance API"""
    def __init__(self, selected_endpoint_name: str = 'observations'):
        super().__init__(
            name='MétéoFrance',
            base_url=Config.METEOFRANCE_BASE_URL,
            auth_type='oauth',
            app_id=Config.METEOFRANCE_APP_ID,
            accept_header=Config.ACCEPT_HEADER,
            token_url=Config.METEOFRANCE_TOKEN_URL,
            token_data=Config.TOKEN_Data,
            token_headers=Config.TOKEN_HEADERS,
            endpoints={
                'observations': Config.OBSERVATIONS_ENDPOINT,
                'forecast': Config.FORECAST_ENDPOINT,
                'radar': Config.RADAR_ENDPOINT
            },
            selected_endpoint_name=selected_endpoint_name,
            timeout=30
        )

    
    @classmethod
    def observations(cls):
        return cls(selected_endpoint_name="observations")

    @classmethod
    def forecast(cls):
        return cls(selected_endpoint_name="forecast")

    @classmethod
    def radar(cls):
        return cls(selected_endpoint_name="radar")