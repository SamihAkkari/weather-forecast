# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 03:25:48 2026

@author: sakkari
"""

import logging
import sys

from src.data.maintenance import thin_forecast_runs, purge_old_bronze

dry_run = "--dry-run" in sys.argv
try:
    thin_forecast_runs(dry_run=dry_run)   # 1) thin first
    if not dry_run:
        purge_old_bronze(keep_days=3)     # 2) then purge bronze
except Exception:
    logging.getLogger("maintenance").exception("Maintenance failed")
    sys.exit(1)