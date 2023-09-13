import streamlit as st
import mlflow

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

#Page code
    
prev_simname = st.session_state.get("Insert Simulation name", "")
simname = st.text_input("Insert Simulation name", prev_simname)

#Experiments directory
simdir = 'cases/'
rawdata = 'data/'  

if simname:

    os.system(f'mkdir {simdir}{simname}')

    mlflow.set_experiment(f'{simname}')
    mlflow.start_run()

    tags = {"teste1":"deu certo"}
    
    mlflow.set_tags(tags)
    
    mlflow.end_run()

    st.text('Passou')                            



