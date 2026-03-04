from src.api.meteo_france import MeteoFranceObservations
from src.api.meteo_france import MeteoFranceForecastArome

# Factory pattern for creating API instances
class APIFactory:
    """Factory for creating API instances by name"""
    
    _registry = {
        'meteofrance_observations': MeteoFranceObservations,
        'meteofrance_forecast_arome': MeteoFranceForecastArome,
        # 'meteofrance_radar': MeteoFranceRadar,
    }
    
    @classmethod
    def register(cls, name: str, api_class) -> None:
        """Register a new API class"""
        cls._registry[name] = api_class
    
    @classmethod
    def create(cls, name: str, service:str, **kwargs):
        """Create an API instance by name"""
        if name not in cls._registry:
            available = ', '.join(cls._registry.keys())
            raise ValueError(
                f"Unknown API '{name}'. Available: {available}"
            )
        
        api_class = cls._registry[name]
        return api_class(service, **kwargs)
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List all available API names"""
        return list(cls._registry.keys())