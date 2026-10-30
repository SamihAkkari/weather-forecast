import os
import threading
from psycopg2 import pool
from src.config.config import Config

_pool = None
_lock = threading.Lock()


def _get_pool():
    global _pool
    with _lock:
        if _pool is None:
            timeout_ms = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "0"))   # 0 = no limit
            _pool = pool.ThreadedConnectionPool(
                1, int(os.getenv("DB_POOL_MAX", "40")),
                dbname=Config.POSTGRES_DB, user=Config.POSTGRES_USER,
                password=Config.POSTGRES_PASSWORD, host=Config.POSTGRES_HOST,
                port=Config.POSTGRES_PORT,
                options=f"-c timezone=UTC -c statement_timeout={timeout_ms}",
            )
        return _pool


class DatabaseConnection:
    """Borrows a connection from the pool and gives it back afterwards."""

    def __enter__(self):
        self.conn = _get_pool().getconn()
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            # a broken connection is closed instead of being reused
            _get_pool().putconn(self.conn, close=bool(self.conn.closed))