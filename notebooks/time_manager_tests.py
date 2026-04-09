# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 19:23:47 2026

@author: sakkari
"""

import os
os.chdir('c:\\Users\\sakkari\\Code\\weather-forecast')
from src.ingestion.time_manager import TimeManager


TimeManager.last_interval_iso(time_step=  3600, steps_back =2)
