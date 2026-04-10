# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 19:23:47 2026

@author: sakkari
"""

import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.ingestion.time_manager import TimeManager

from datetime import timedelta

TimeManager.last_interval_iso(time_step=  3600, steps_back =2)

T_now = TimeManager.utc_now_truncated(to="hour")

TimeManager.utc_to_france(T_now)


def sleep_until_next_hour():
    now = TimeManager.utc_now()
    next_hour = TimeManager.utc_truncated(now + timedelta(hours=1), to='hour')
    sleep_seconds = (next_hour - now).total_seconds()