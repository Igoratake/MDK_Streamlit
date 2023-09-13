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
raw_oce = 'data/MERCATOR/'
raw_met = 'data/ERA5/'   

if simname:
    
    #Creating all directories    
    subprocess.run(f'mkdir {simdir}{simname}/',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/oce_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/met_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/bnc_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/xp_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/out_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/detections',shell=True)   


    # Use the glob module to get a list of files in the current directory
    file_list = glob(f"{raw_oce}*_raw.nc")

    # Use st.sidebar.selectbox to create a selectbox in the sidebar
    selected_file = st.selectbox("Select a file", file_list)

    if '_med_' in selected_file:
        lon = 'lon'
        lat = 'lat'

    else:
        lon = 'longitude'
        lat = 'latitude'

    dsname = f'{simdir}{simname}/oce_files/temp.nc'
    dsname2 = f'{simdir}{simname}/oce_files/temp2.nc'

    if selected_file:
        subprocess.run([f'ncrename -O -d {lon},nav_lon -d {lat},nav_lat'
                       f' -v {lon},nav_lon -v {lat},nav_lat' \
                       f' -v time,time_counter -d time,time_counter' \
                       f' -v thetao,votemper -v uo,vozocrtx -v vo,vomecrty' \
                       f' {selected_file} {dsname}'],shell=True,check=True)

        # Display the selected file
        st.write(f"Selected File: {selected_file}")
        
        time.sleep(3)
        ds = xr.open_dataset(dsname)

        rec = ds.sel(depth=[0,10,30,120], method='nearest')
        rec = rec.fillna(9999)       
        
        rec.to_netcdf(dsname)        

        if st.button("Process data"):
            
            rec = xr.open_dataset(dsname)          

            inidate = rec.time_counter[0].values.astype('datetime64[D]').item()
            enddate = rec.time_counter[-1].values.astype('datetime64[D]').item()
            
            # Display the selected file
            st.write(f"Date range is from {inidate.day}/{inidate.month}/{inidate.year} to {enddate.day}/{enddate.month}/{enddate.year}")

            subprocess.run(f'cdo -inttime,{inidate.year}-{inidate.month}-{inidate.day},12:00:00,1hour {dsname} {dsname2}',shell=True,check=True)

            for var in ['U','V','T']:
                for t in rec.time_counter:
                    
                    tt = t.values.astype('datetime64[D]').item()
                    day = str(tt.day).zfill(2)
                    month = str(tt.month).zfill(2)
                    year = str(tt.year)[2:]
                    subprocess.run(f'cdo seldate,{tt.year}-{tt.month}-{tt.day},{tt.year}-{tt.month}-{tt.day} {dsname2} {simdir}{simname}/oce_files/MDK_ocean_{year}{month}{day}_{var}.nc',shell=True,check=True)

            subprocess.run(f'rm {dsname}',shell=True,check=True)
            subprocess.run(f'rm {dsname2}',shell=True,check=True)

            grid_string = glob(f'{simdir}{simname}/oce_files/*_T.nc')[0] 
            bath_string = f'--gebco data/gebco/gebco_08.nc ' + grid_string + f'--output-dir {simdir}{simname}/bnc_files/'
            coast_string = f'--gshhs data/gshhs/gshhs_f.b '  + grid_string + f'--output-dir {simdir}{simname}/bnc_files/'

            subprocess.run('eval "$(conda shell.bash hook)";mdk2',shell=True,check=True)
            subprocess.run('python preproc_gebco_mdk2.py ' + bath_string, shell=True,check=True)
            subprocess.run('python preproc_gshhs_mdk2.py ' + coast_string, shell=True,check=True)


            
                           



