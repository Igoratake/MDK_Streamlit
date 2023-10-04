#geo libs
import folium
import xarray as xr
import geojsoncontour
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import Point
from folium.plugins import HeatMap
from streamlit_folium import st_folium,folium_static

#numerical and plotting libs
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.figure_factory as ff

#system libs
import os
import sys
import time
import datetime
import subprocess
import threading
from glob import glob

'''

This script contains several functions that can be used across MEDSLIK-II modeling.

'''

def check_land(lon,lat):

    '''
    This script receives a lon and lat value and  checks if the position is within land or sea
    It uses a shapefile of world boundaries currently based in geopandas database

    In case a position is on land:
        Script returns 0, since it will not be possible to simulate oil spill on land
    
    Otherwise returns 1 

    '''

    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    point = Point(lon, lat)

    is_within_land = world.geometry.contains(point).any()
    
    if is_within_land:
        sea=0
    else:
        sea=1

    return sea

def validate_date(date):

    '''
    Convert a date in string format to datetime, checking if the date provided is valid

    It also checks if date is in the future, blocking the user to procced

    '''

    try: 
        dt=datetime.datetime.strptime(date,'%d/%m/%Y')
        if dt > datetime.datetime.today():
            dt = 'Date provided is in the future. No data will be available'               
        
    except:
        dt = 'Wrong date format'

    return dt

def search_and_replace(file_path, search_word, replace_word):
    with open(file_path, 'r') as file:
        file_contents = file.read()

        updated_contents = file_contents.replace(search_word, replace_word)

    with open(file_path, 'w') as file:
        file.write(updated_contents)

def write_cds(key):

    with open('~.cdsapirc_test') as f:
        f.write('url: https://cds.climate.copernicus.eu/api/v2\n')
        f.write(f'key: {key}\n')
        f.write('verify: 0')
        f.close()

