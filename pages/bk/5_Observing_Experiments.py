import streamlit as st
import mlflow
import webbrowser

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

# Use the glob module to get a list of files in the current directory
file_list = glob("cases/*")

# Use st.sidebar.selectbox to create a selectbox in the sidebar
selected_file = st.selectbox("List of Possible Experiments", file_list)

if selected_file:

    short = selected_file.split('/')[-1]    

    df = mlflow.search_runs(experiment_names=[short])

    if df.empty:

        st.text('This experiment does not yet have an Mlflow experiment linked to it \n \
Try another one')

    else:

        exp_id = df.iloc[0].experiment_id

        st.dataframe(data=df)        

        if st.button("Go to MLFlow"):

            try:
                subprocess.run(f'mlflow ui',shell=True,check=True)
            except:
                pass          
            
            webbrowser.open_new_tab(f'http://localhost:5000/#/experiments/{exp_id}')

    
    


                            



