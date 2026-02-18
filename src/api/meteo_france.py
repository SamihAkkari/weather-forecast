from src.config.config import Config

class MeteoFranceBase:
    def __init__(self, 
                name = 'MétéoFrance',
                base_url = Config.METEOFRANCE_BASE_URL,
                auth_type = 'oauth',
                accept_header = Config.ACCEPT_HEADER,
                token_url = Config.METEOFRANCE_TOKEN_URL,
                token_data = Config.TOKEN_Data,
                token_headers = Config.TOKEN_HEADERS,
                timeout=30
                ):
        self.name = name
        self.base_url = base_url
        self.auth_type = auth_type
        self.accept_header = accept_header
        self.token_url = token_url
        self.token_data = token_data
        self.token_headers = token_headers
        self.timeout = timeout

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

class MeteoFranceObservations(MeteoFranceBase):
    """MétéoFrance Observations API"""
    endpoints = {
        "liste-stations": Config.OBSERVATIONS_LISTESTATION_ENDPOINT,
        "infrahoraire-6m": Config.OBSERVATIONS_INFRAHORAIRE6m_ENDPOINT,
        "horaire": Config.OBSERVATIONS_HORAIRE_ENDPOINT,
        "stations_infrahoraire-6m": Config.OBSERVATIONS_STATIONS_INFRAHORAIRE6m_ENDPOINT
    }

    def __init__(self,
                 service,
                 app_id = Config.METEOFRANCE_APP_ID):
        super().__init__()
        """Return the endpoint path"""
        self.app_id = app_id
        self.service = service
        if service not in self.endpoints:
            available = ', '.join(self.endpoints.keys())
            raise ValueError(
                f"Unknown service '{service}'. Available: {available}"
            )
        self.endpoint_path = self.endpoints[service]

class MeteoFranceForecast(MeteoFranceBase):
    def __init__(self):
        raise NotImplementedError()

class MeteoFranceRadar(MeteoFranceBase):
    """MétéoFrance Observations API"""
    def __init__(self):
        raise NotImplementedError()