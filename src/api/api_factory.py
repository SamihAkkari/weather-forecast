from src.api.meteo_france import MeteoFranceObservations
from src.api.meteo_france import MeteoFranceForecastArome

class APIFactory:
    """Create API clients from registered names."""
    
    _registry = {
        'meteofrance_observations': MeteoFranceObservations,
        'meteofrance_forecast_arome': MeteoFranceForecastArome,
    }
    
    @classmethod
    def register(cls, name: str, api_class) -> None:
        """Register an API client class under a name."""
        cls._registry[name] = api_class
    
    @classmethod
    def create(cls, name: str, service:str, **kwargs):
        """Instantiate the client registered under ``name``."""
        if name not in cls._registry:
            available = ', '.join(cls._registry.keys())
            raise ValueError(
                f"Unknown API '{name}'. Available: {available}"
            )
        
        api_class = cls._registry[name]
        return api_class(service, **kwargs)
    
    @classmethod
    def list_available(cls) -> list[str]:
        """Return the registered API names."""
        return list(cls._registry.keys())