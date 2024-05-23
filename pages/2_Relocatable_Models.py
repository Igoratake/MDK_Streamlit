import streamlit as st

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
import pandas as pd

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

# Functions outside this script
from functions.medslik_utils import *
from scripts import *

def run_download_era5(lat_min,lon_min,lat_max,lon_max,inidate,enddate,output_path):
    
    script_name = 'functions/download_era5_parser.py'

    # Run the external Python script as a subprocess
    subprocess.run([f'{sys.executable}', script_name, lat_min,lon_min,lat_max,lon_max,inidate,enddate,output_path])

#Page code
    
st.title("Data available from Relocatable Models")

# Use the glob module to get a list of files in the current directory
file_list = glob("/Users/iatake/Dropbox (CMCC)/Work/#Projects/EDITO/data/*.nc")

# Use st.sidebar.selectbox to create a selectbox in the sidebar
selected_file = st.selectbox("Select a file", file_list)

# Display the selected file
st.write(f"Selected File: {selected_file}")

if selected_file:

    ds = xr.open_dataset(selected_file)

    #adjusting to medslik-II variable names
    ds = rename_netcdf_variables_mdk2(ds)

    time_min = pd.to_datetime(ds.time.values.min()).date()
    time_max = pd.to_datetime(ds.time.values.max()).date()

    lat_min = ds.lat.values.min()
    lat_max = ds.lat.values.max()

    lon_min = ds.lon.values.min()
    lon_max = ds.lon.values.max()

    st.text('Time')
    st.text(f'The selected file starts at date {time_min} and ends at {time_max}')

    st.text('Coordinates')
    st.text(f'Latitude varies from {lat_min} to {lat_max}')
    st.text(f'Longitude varies from {lon_min} to {lon_max}')

    st.text('Select a date.')
    st.text('10 days ahead will be selected from the given date')

    # Calculate max value 10 days less than the maximum value
    max_value = time_max - pd.Timedelta(days=10)

# Slider to select date range
    dt_min = st.date_input(label='Available Dates',min_value=time_min,max_value=max_value,value=time_min)
    dt_max = dt_min + pd.Timedelta(days=10)

    st.text(f'Data will be cropped from {dt_min} to {dt_max}')

    #cropping data
    ds = ds.drop_vars(['mesh2d_face_x','mesh2d_face_y','mesh2d_layer_sigma','mesh2d_nFaces'])
    ds_rec = ds.sel(time=slice(dt_min,dt_max))

    ds_rec_sea =  ds_rec[['time','uo','vo','thetao']]
    ds_rec_wind =  ds_rec[['time','U10M','V10M']]

    viz = st.radio("Do you want to check the data?",
    ["no", 'yes'],)

    if viz == 'yes':

        st.text('Properties of the selected file. Please select a timestep')

        dt = st.slider(label='Available timesteps',min_value=0,max_value=len(ds_rec.time),value=(0,len(ds_rec.time)))

        dt = dt[1]

        st.text(ds_rec_sea)

        plot_sea = ds_rec_sea.isel(time=dt-1)
        plot_wind = ds_rec_wind.isel(time=dt-1)

        #sea velocity figure
        fig1, ax1 = plt.subplots()

        xxs,yys = np.meshgrid(ds_rec_sea.lon.values,ds_rec_sea.lat.values)

        # Calculate magnitude of the vectors
        magnitude = (plot_sea.uo.values**2 + plot_sea.vo.values**2)**0.5

        q = ax1.quiver(xxs,yys,plot_sea.uo.values,plot_sea.vo.values,magnitude, cmap='viridis')
        plt.colorbar(q, ax=ax1)
        # st.pyplot(fig1)

        st.title('Sea Surface velocity (m/s)')
        fig_html = mpld3.fig_to_html(fig1)
        components.html(fig_html, height=600)

        fig2, ax2 = plt.subplots()

        xxw,yyw = np.meshgrid(plot_wind.lon.values,plot_wind.lat.values)

        # # Calculate magnitude of the vectors
        magnitude = (plot_wind.U10M.values**2 + plot_wind.V10M.values**2)**0.5

        q = ax2.quiver(xxw,yyw,plot_wind.U10M.values,plot_wind.V10M.values,magnitude, cmap='viridis')
        plt.colorbar(q, ax=ax2)
        # st.pyplot(fig2)

        st.title('10 m Wind velocity (m/s)')
        fig_html2 = mpld3.fig_to_html(fig2)
        components.html(fig_html2, height=600)

        fig3, ax3 = plt.subplots()

        ax3.pcolormesh(xxs,yys,plot_sea.thetao.values,cmap='viridis')
        # plt.colorbar(ax=ax3)
        # st.pyplot(fig2)

        st.title('Sea Surface Temperature (C)')
        fig_html3 = mpld3.fig_to_html(fig3)
        components.html(fig_html3, height=600)

    #save processed netcdf

    st.text('The file is not on hourly format. By pressing the button below, \ndata will be interpolated and stored on the correct directories \nto launch medslik-II simulations')

    if st.button('Confirm Processing'):
        st.text('The netcdf file will be put onto data available for the Relocatable System')

        ds_rec_sea = ds_rec_sea.resample(time="1H").interpolate("linear")
        ds_rec_sea = ds_rec_sea.expand_dims({'depth':[0,10,30,120]})
        ds_rec_sea.to_netcdf(f'/Users/iatake/Dropbox (CMCC)/Work/MEDSLIK-II and Pyslick/MDK_Streamlit/data/MERCATOR/Deltares_relocatable_sea_{dt_min.year}{dt_min.month:02d}{dt_min.day:02d}_mdk.nc')

        ds_rec_wind = ds_rec_wind.resample(time="1H").interpolate("linear")
        ds_rec_wind.to_netcdf(f'/Users/iatake/Dropbox (CMCC)/Work/MEDSLIK-II and Pyslick/MDK_Streamlit/data/ERA5/Deltares_relocatable_winds10_{dt_min.year}{dt_min.month:02d}{dt_min.day:02d}_mdk.nc')

