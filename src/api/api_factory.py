"""
API Catalog - Maps API names to their configurations
Separate from Config because this is API metadata, not environment config
"""

from src.api.meteo_france import MeteoFranceObservations, MeteoFranceForecast, MeteoFranceRadar 

# Factory pattern for creating API instances
class APIFactory:
    """Factory for creating API instances by name"""
    
    _registry = {
        'meteofrance_observations': MeteoFranceObservations,
        'meteofrance_forecast': MeteoFranceForecast,
        'meteofrance_radar': MeteoFranceRadar,
    }
    
    @classmethod
    def register(cls, name: str, api_class) -> None:
        """Register a new API class"""
        cls._registry[name] = api_class
    
    @classmethod
    def create(cls, name: str, **kwargs):
        """Create an API instance by name"""
        if name not in cls._registry:
            available = ', '.join(cls._registry.keys())
            raise ValueError(
                f"Unknown API '{name}'. Available: {available}"
            )
        
        api_class = cls._registry[name]
        return api_class(**kwargs)
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List all available API names"""
        return list(cls._registry.keys())