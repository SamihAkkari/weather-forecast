"""
Configuration - ONLY holds configuration values
No business logic, no complex methods
"""

import os
from pathlib import Path
from dotenv import load_dotenv


env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT')
    
    ## API Configuration
    # Meteo France API
    METEOFRANCE_APP_ID = os.getenv('METEOFRANCE_APP_ID')
    METEOFRANCE_BASE_URL = os.getenv('METEOFRANCE_BASE_URL')
    ACCEPT_HEADER = {'Accept': 'application/json'}

    #Token related
    METEOFRANCE_TOKEN_URL = os.getenv('METEOFRANCE_TOKEN_URL')
    TOKEN_Data = {'grant_type': 'client_credentials'}
    TOKEN_HEADERS = {'Authorization': 'Basic ' + METEOFRANCE_APP_ID}
    
    # Endpoints
    OBSERVATIONS_ENDPOINT = 'DPPaquetObs/v1/paquet/infrahoraire-6m'
    FORECAST_ENDPOINT = 'DPPrevision-Decoupage/v1/previsions'
    RADAR_ENDPOINT = 'DPRadar/v1/radars'

    
    
    # Database Configuration
    # DB_HOST = os.getenv('DB_HOST', 'localhost')
    # DB_PORT = int(os.getenv('DB_PORT', '5432'))
    # DB_NAME = os.getenv('DB_NAME')
    # DB_USER = os.getenv('DB_USER')
    # DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    # # Cache Configuration
    # CACHE_TYPE = os.getenv('CACHE_TYPE', 'file')
    # REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    # REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    
    # # Logging
    # LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
