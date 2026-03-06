import psycopg2
from src.config.config import Config

class DatabaseConnection: 
    
    """Handles opening and closing DB connections."""
    def __init__(self):
        pass
    
    def __enter__(self):
        self.conn = psycopg2.connect(
            dbname=Config.POSTGRES_DB,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT
        )
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.conn.commit()   # success
        else:
            self.conn.rollback() # error
        self.conn.close()