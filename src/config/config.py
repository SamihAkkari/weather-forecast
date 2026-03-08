import os
from pathlib import Path
from dotenv import load_dotenv


env_path = Path.cwd() / '.env'

# env_path = Path(__file__).parent.parent / '.env'
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
    OBSERVATIONS_LISTESTATION_ENDPOINT = 'public/DPPaquetObs/v1/liste-stations'
    OBSERVATIONS_INFRAHORAIRE6m_ENDPOINT = 'public/DPPaquetObs/v1/paquet/infrahoraire-6m'
    OBSERVATIONS_HORAIRE_ENDPOINT = 'public/DPPaquetObs/v1/paquet/horaire'
    OBSERVATIONS_STATIONS_INFRAHORAIRE6m_ENDPOINT = 'public/DPPaquetObs/v1/paquet/stations/infrahoraire-6m'
    
    API_INFRAHORAIRE6m_TIME_STEPS = 6 # in minutes (time steps of the observations )
    
    FORECAST_AROME_PACKAGE_0025SP1_ENDPOINT = 'previnum/DPPaquetAROME/v1/models/AROME/grids/0.025/packages/SP1/productARO' #SP1 data with 0.025° resolution (2.5km resolution)
    # RADAR_ENDPOINT = 'DPRadar/v1/radars'

    
    # Database Configuration
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

    BRONZE_SCHEMA = 'bronze'
    SILVER_SCHEMA = 'silver'
    
    STATIONS_TABLE_NAME = 'stations'
    Data_TABLE_NAME = 'observations'
    FORECAST_TABLE_NAME = 'forecast'

    API_FORMAT = 'json' 

    TEMPORARY_GRIB_PATH = 'data/temp/file.grib2'

    AROME_FORECAST_UPDATE_TIMES = ["00:00:00", "03:00:00", "06:00:00", "09:00:00", "12:00:00", "15:00:00", "18:00:00", "21:00:00"]
    AROME_FORECAST_UPDATE_FREQUENCY_HOURS = 5 # hours