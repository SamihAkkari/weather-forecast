# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 00:27:59 2026

@author: sakkari
"""

from src.config.config import Config
from src.data.db import DatabaseConnection
with DatabaseConnection() as conn:
    with conn.cursor() as cur:
        cur.execute(f"""
                        SELECT * 
                        FROM {Config.SILVER_SCHEMA}.{Config.OBSERVATIONS_TABLE_NAME_6m}
                        WHERE
                            station_id = %s 
                        """, ("01014002",))
        data = cur.fetchall()

{
        "station_id": "01014002",
        "data": [
            {"timestamp": r.timestamp.isoformat(), "value": r.value}
            for r in data
        ]
    }

columns = [desc[0] for desc in cur.description]
result = []
for row in data:
    record = dict(zip(columns, row))

    for key, value in record.items():
        if hasattr(value, "isoformat"):  # datetime
            record[key] = value.isoformat()

    result.append(record)