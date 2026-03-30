import os
from src.navigation import takeoff
from src.navigation import fly_to_target
from src.navigation import land

def mission(vehicle):
    T_LAT = float(os.getenv("TARGET_LAT"))
    T_LON = float(os.getenv("TARGET_LON"))
    T_ALT = float(os.getenv("TARGET_ALT"))
    takeoff(vehicle, T_ALT)
    fly_to_target(vehicle, T_LAT, T_LON, T_ALT)
    land(vehicle, T_LAT, T_LON)