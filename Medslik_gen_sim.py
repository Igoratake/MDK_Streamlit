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

# Functions outside this script
from functions.medslik_utils import *
import functions.download_mercator_parser
import functions.download_era5_parser
from scripts import *


# ================= MEDSLIK MODEL INPUTS ================= #
simname        = 'test2'      ### Simulation name - format (string)
sim_date       = '15/07/2023' ### Simulation start day  - format DD/MM/YYYY (string)
sim_hour       = '07:00'      ### Simulation start hour - format HH:mm (string)
longitude      = 18.00        ### Longitude of Simulation spill location - format Decimal degrees (float)
latitude       = 41.00        ### Latitude of Simulation spill  - format Decimal degrees (float)
delta          = 0.5          ### Standard delta to collect an area around lat and discharge point - format degrees (float)
sim_lenght     = 48           ### Length of the simulation - format hours (int)
spill_duration = 0            ### Duration of the spill - format hours (int)
oil_api        = 28           ### Oil API - format (float)
oil_volume     = 5            ### Volume of oil in tons - format (float) 
use_satellite  = False        ### Usage of Satellite imagery to model multiple slicks - True/False

# Obtaining spill rate from oil volume and spill duration
if spill_duration != 0:
    spill_rate = oil_volume/spill_duration
else:
    spill_duration = oil_volume    

# ================= DOWNLOAD OPTIONS ================= #
down = 'global'               ### Download data from global copernicus or local models - format(string) global/local
cop_username = None           ### Username to access copernicus datasets. Can be replaced here for practicity. - format None or string
cop_password = None           ### Password to access copernicus datasets. Can be replaced here for practicity. - format None or string
era_api_key  = None           ### API key to access era5 datasets. Can be replaced here for practicity. - format None or string



'''
These options are used for choosing which datasets to use when downloading data from external sources

'''

if __name__ == '__main__':

    # Check if coordinates are on sea
    sea =  check_land(longitude,latitude)    

    if sea==0:
        raise ValueError('Coordinates values are on land. Try another location')
    
    if 30.37 < float(latitude) < 45.7 and -17.25 < float(longitude) < 35.9 and down=='global':
        print('Coordinates lie within Mediterranean Sea\n Your data is set to global.\n'
                'Press y to continue with global or n to change to Med Sea Data')     
        
        while True:
            check = input().lower()
            if check == 'n':
                down = 'local'
                break
            elif check =='y':
                break
            else:
                print('wrong input. Try again')
    
    # Download area
    print (f'Download coordinates are:'
           f'Min lat = {(latitude-delta):.2f} Max lat = {(latitude+delta):.2f}'
           f'Min lon = {(longitude+delta):.2f} Max lon = {(longitude+delta):.2f}')
    
    # Simulation dates
    dt = validate_date(sim_date)

    if isinstance(dt,str):
        raise ValueError('Wrong date format.')

    dtini = dt - datetime.timedelta(days=1)
    if (datetime.datetime.today()-dt).days <10:
        print('ERA5 data might not be available in the selected date')
        
    inidate = f'{dtini.year}-{str(dtini.month).zfill(2)}-{str(dtini.day).zfill(2)}'
    inidate2 = inidate + 'T00:00:00Z'         

    dtend = dt + datetime.timedelta(days= (sim_lenght/24) + 2) 

    enddate = f'{dtend.year}-{str(dtend.month).zfill(2)}-{str(dtend.day).zfill(2)}'
    enddate2 = enddate + 'T00:00:00Z'

    if cop_username == None:
        print('Please input your copernicus user name')
        cop_username = input()
    
    if cop_password == None:
        print('Please input your copernicus password')
        cop_password = input()
    

    ### Mercator download ###
    output_path = 'data/MERCATOR/'                            
    # Create a thread to run the external script in the background
    script_thread = subprocess.run([sys.executable, 'functions/download_mercator_parser.py',
                                    inidate2,enddate2,'0','130',
                                    str(latitude),str(longitude),str(delta),
                                    down,output_path,
                                    cop_username,cop_password],shell=True,check=True) 
    
    ### ERA5 download ###
    #Met Data
    # output_path = 'data/ERA5/'

    # # Create a thread to run the external script in the background
    # script_thread = threading.Thread(target=run_download_era5(latitude,longitude,delta,inidate,enddate,output_path=output_path))
    

    
    


        

    


    