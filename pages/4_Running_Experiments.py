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
import json
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

try:
    mlflow.end_run()
except:
    pass

if simname:

    if os.path.isdir(f'{simdir}{simname}') == False:
        st.text('No setup available for this experiment name\nTry another one')

    else: 

        if st.button(f"Start Simulation for {simname}"):               

            subprocess.run(f'mkdir {simdir}{simname}',shell=True)
            print('\n\n\n ===== MED Streamlit Run ===== \n\n\n')

            st.text('Creating or using MLFlow Experimet')
            mlflow.set_experiment(f'{simname}')
            mlflow.start_run()

            st.text('Linking directories')
            # copy METOCEAN files to MEDSLIK-II installation
            subprocess.run([f'cp {simdir}{simname}/oce_files/* MEDSLIK_II_2.02/METOCE_INP/PREPROC/OCE/'],shell=True)
            subprocess.run([f'cp {simdir}{simname}/oce_files/* MEDSLIK_II_2.02/RUN/TEMP/OCE/'],shell=True)

            subprocess.run([f'cp {simdir}{simname}/met_files/* MEDSLIK_II_2.02/METOCE_INP/PREPROC/MET/'],shell=True)
            subprocess.run([f'cp {simdir}{simname}/met_files/* MEDSLIK_II_2.02/RUN/TEMP/MET/'],shell=True)
            # copy bnc files
            subprocess.run([f'cp {simdir}{simname}/bnc_files/* MEDSLIK_II_2.02/DTM_INP/'],shell=True)
            # copy Extract and config files
            subprocess.run([f'cp {simdir}{simname}/xp_files/Extract_II.for MEDSLIK_II_2.02/RUN/MODEL_SRC/'],shell=True)
            subprocess.run([f'cp {simdir}{simname}/xp_files/medslik_II.for MEDSLIK_II_2.02/RUN/MODEL_SRC/'],shell=True)
            subprocess.run([f'cp {simdir}{simname}/xp_files/config1.txt MEDSLIK_II_2.02/RUN/'],shell=True)

            st.text('Compiling Medslik')
            # Compile and start running
            subprocess.run([f'cd MEDSLIK_II_2.02/RUN/; sh MODEL_SRC/compile.sh; ./RUN.sh'],shell=True,check=True)

            f = open(f'cases/{simname}/xp_files/tags.json',)
            tagss = json.load(f)
            
            mlflow.set_tags(tagss)
            
            mlflow.end_run()
                            