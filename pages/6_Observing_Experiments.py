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

#interactive plotting
import mpld3
import streamlit.components.v1 as components

#Page code

@st.cache_data
def read_coastline():

    gdf = gpd.read_file('/Users/iatake/Dropbox (CMCC)/Work/MEDSLIK-II and Pyslick/Medslik-II/data/gshhs/GSHHS_shp/f/GSHHS_f_L1.shp')

    return gdf

@st.cache_data
def read_output(filename):

    ds = xr.open_dataset(filename)

    return ds


# Use the glob module to get a list of files in the current directory
file_list = glob("cases/*")

# Use st.sidebar.selectbox to create a selectbox in the sidebar
selected_file = st.selectbox("List of Possible Experiments", file_list)

if selected_file:

    short = selected_file.split('/')[-1]    

#     df = mlflow.search_runs(experiment_names=[short])

#     if df.empty:

#         st.text('This experiment does not yet have an Mlflow experiment linked to it \n \
# Try another one')

#     else:

#         exp_id = df.iloc[0].experiment_id

#         st.dataframe(data=df)        

#         if st.button("Go to MLFlow"):

#             try:
#                 subprocess.run(f'mlflow ui',shell=True,check=True)
#             except:
#                 pass          
            
#             webbrowser.open_new_tab(f'http://localhost:5000/#/experiments/{exp_id}')

    gdf = read_coastline()

    ds = read_output(filename='/Users/iatake/Dropbox (CMCC)/Work/MEDSLIK-II and Pyslick/MDK_Streamlit/cases/relocatable/out_files/MDK_SIM_2017_01_01_1200_relocatable/spill_properties.nc')

    lon_min, lon_max = ds.longitude.values.min()-1,ds.longitude.values.max()+1
    lat_min, lat_max = ds.latitude.values.min()-1,ds.latitude.values.max()+1

    rec = gdf.cx[lon_min:lon_max, lat_min:lat_max]

    rec = rec.clip_by_rect(lon_min,lat_min,lon_max,lat_max)

    dt = st.slider(label='Available timesteps',min_value=0,max_value=len(ds.time),value=(0,len(ds)))

    dt = dt[1]

    plot_sea = ds.isel(time = dt-1)

    fig, ax = plt.subplots()

    rec.plot(ax=ax,color="#FFFDD0", edgecolor='black', zorder = 1000,aspect=1)
    q = ax.scatter(plot_sea.longitude,plot_sea.latitude,s=0.1,c = plot_sea.non_evaporative_volume,cmap='viridis')
    
    plt.colorbar(q, ax =ax)

    plt.xlim(lon_min,lon_max)
    plt.ylim(lat_min,lat_max)

    plt.title(f'Oil particles volumes (tonnes) at timestep {dt}')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

    st.title('Sea Surface Temperature (C)')
    fig_html = mpld3.fig_to_html(fig)
    components.html(fig_html, height=600)


                            



