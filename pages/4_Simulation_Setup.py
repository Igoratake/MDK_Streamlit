import streamlit as st
import mlflow

#geo libs
import folium
import xarray as xr
import geojsoncontour
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import Point
from folium.plugins import HeatMap, Draw
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
import json
import datetime
import subprocess
import threading
from glob import glob

# Functions outside this script
from functions.medslik_utils import *
from scripts import *

#Page code
prev_simname = st.session_state.get("Insert Simulation name", "")
simname = st.text_input("Insert Simulation name", prev_simname)

#Experiments directory
simdir = 'cases/'
raw_oce = 'data/MERCATOR/'
raw_met = 'data/ERA5/'

if simname:

    safety_check = False

    #Creating all directories    
    subprocess.run(f'mkdir {simdir}{simname}/',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/oce_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/met_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/bnc_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/xp_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/out_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/detections',shell=True)   


    # Use the glob module to get a list of files in the current directory
    file_list = glob(f"{raw_oce}*_mdk.nc")

    # Use st.sidebar.selectbox to create a selectbox in the sidebar
    selected_file = st.selectbox("Select a file", file_list)

    if selected_file:



        ds = xr.open_dataset(selected_file)  

        min_lat,max_lat = (ds.lat.values.min(),ds.lat.values.max())
        min_lon,max_lon = (ds.lon.values.min(),ds.lon.values.max())

        start_day = str(ds.isel(time=25).time.values.max())[0:10]
        st.text(start_day)

        st.text('Coordinates are:\n'
                f'Mininum Latitude: {min_lat:.2f} Maximum Latitude: {max_lat:.2f}\n'
                f'Mininum Longitude: {min_lon:.2f} Maximum Longitude: {max_lon:.2f}\n'
                'Discharge Point must be inside this geo box'
                '\n\n'
                'The Simulation needs to start at:\n'
                f'{start_day}'
                )
        
        coord_type = st.radio("Select from Lat and Lon values or from map",
        ["Fixed values ", 'map'])

        if coord_type == 'map':

            st.text('Only the last coordinate will be considered for model setup')
            m = folium.Map(location=[min_lat,min_lon], zoom_start=6)
            Draw(export=True,
            draw_options={"polyline": False,"polygon": False,"circle": False
                          ,"circlemarker": False,"rectangle":False},
            edit_options=False,
                ).add_to(m)
            
            #adding the boundalies limit to the map
            #Define custom coordinates for your polygon
            polygon_coordinates = [
                (min_lat, min_lon),
                (min_lat, max_lon),
                (max_lat, max_lon),
                (max_lat, min_lon)
            ]

            #Polygon object with the custom coordinates
            polygon = folium.Polygon(polygon_coordinates, color='blue', fill= False)

            #Add the polygon to the Folium map
            polygon.add_to(m)
            
            output = st_folium(m, width=700, height=500,returned_objects=["last_active_drawing"])

            if output["last_active_drawing"] != None:
            
                marker = output["last_active_drawing"]["geometry"]
                px = marker['coordinates'][0]
                py = marker['coordinates'][1]

                sea =  check_land(px,py)    

                if sea==0:
                    st.text('Your coordinates lie within land. Please check your values again')
                    safety_check = False

                elif px < min_lon or px > max_lon or py < min_lat or py > max_lat:
                    st.text('Your coordinates are outside the data provided')
                    safety_check = False

                else:
                    point=True

                    lon_col,lat_col = st.columns(2)

                    lon_col.metric('Longitude',f'{px:.2f} degrees')
                    lat_col.metric('latitude',f'{py:.2f} degrees')

                    longitude = px
                    latitude = py
                    safety_check = True

        else:
            safety_check = False
            latitude = st.text_input("Latitude (decimal degrees)")
            longitude = st.text_input("Longitude (decimal degrees)")
            
            if longitude and latitude:

                sea =  check_land(float(longitude),float(latitude))    

                if sea==0:
                    st.text('Your coordinates lie within land. Please check your values again')
                    safety_check = False
                else:
                    safety_check=True
        
        if safety_check == True:

            # Input fields for latitude, longitude, date of event, and simulation duration
            spill_hour = st.text_input(f"Spill initial time eg. (12:00)",'12:00')
            oil_api = st.text_input("Insert Oil API", '28')
            oil_volume = st.text_input("Insert Oil Volume in Tonnes", '')
            spill_duration = st.text_input('Set the duration of the spill:\n'
                                        '(0 for instanteous spill or the number' 
                                        'of hours of continuous release):' ,0)

            sim_date = datetime.datetime.strptime(start_day + ' ' + spill_hour,'%Y-%m-%d %H:%M')
            last_date = pd.to_datetime(ds.time.values[-1])

            delta = (last_date - sim_date)

            hours = int((delta.days)*24 + (delta.seconds)/3600)

            st.text('According to current files and input,\n'
                    f'max simulation length is: {hours}')

            
            spill_length = st.number_input("Insert simulation length", 24, max_value=hours)

            if (spill_length and spill_duration and spill_hour 
                and latitude and longitude and oil_volume):

                # Obtaining spill rate from oil volume and spill duration
                if float(spill_duration) != 0:
                    spill_rate = float(oil_volume)/float(spill_duration)
                else:
                    spill_rate = float(oil_volume)

                st.session_state.latitude = latitude
                st.session_state.longitude = longitude
                st.session_state.spill_hour = spill_hour
                st.session_state.spill_duration = int(spill_duration)
                st.session_state.spill_length = int(spill_length)
                st.session_state.spill_rate = spill_rate
                st.session_state.oil_api = oil_api
                st.session_state.oil_volume = float(oil_volume)

                if st.button("Start File Transfer"):

                    subprocess.run([f'cp {selected_file} cases/{simname}/oce_files/'],shell=True)
                    subprocess.run([f'cp data/ERA5/*{selected_file.split("_")[-2]}* cases/{simname}/met_files/'],shell=True)
                    
                    # Simulation dates
                    dt_sim = sim_date
                    # print(sim_date)
                    # dt_sim = validate_date(sim_date)

                    # if isinstance(dt_sim,str):
                    #     raise ValueError('Wrong date format.')
                    
                    #Initial date is always one day prior due to Medslik-II interpolation
                    dtini = dt_sim - datetime.timedelta(days=1)
                        
                    #End date, by safety margin is two days after the sim start + sim length
                    dtend = dt_sim + datetime.timedelta(days= (st.session_state.spill_length/24) + 2) 

                    #List of dates between initial and end date
                    date_list = pd.date_range(dtini, dtend, freq='D')

                    #dictionary to write configuration files

                    spill_dictionary = {'simname':simname,'dt_sim':dt_sim,'sim_length':st.session_state.spill_length,
                                        'longitude':st.session_state.longitude,
                                        'latitude':st.session_state.latitude,
                                        'spill_duration':st.session_state.spill_duration,
                                        'spill_rate':st.session_state.spill_rate,
                                        'oil_api':st.session_state.oil_api,
                                        'number_slick':1
                                    }
                    
                    ##### SEA / OCEAN ##### 

                    #opening all files in the directory and concatenating them automatically through open_mfdataset
                    concat = xr.open_mfdataset(f'cases/{simname}/oce_files/*mdk.nc',combine='nested')
                    concat = concat.drop_duplicates(dim="time", keep="last")

                    #Interpolating the values in time, transforming it from daily to hourly values
                    concat = concat.resample(time="1H").interpolate("linear")

                    if 'relocatable' in glob(f'cases/{simname}/oce_files/*mdk.nc')[0]:
                        concat = concat.sel(time=slice(date_list[0],date_list[-1]),
                                            lat=slice(latitude-0.5,latitude+0.5),
                                            lon=slice(longitude-0.5,longitude+0.5))

                    #Call write mrc function located in medslik.utils file
                    write_mrc(concat,simname=simname)

                    ##### WINDS ##### 

                    concat = xr.open_mfdataset(f'cases/{simname}/met_files/*mdk.nc',combine='nested')
                    concat = concat.drop_duplicates(dim="time", keep="first")
                    concat = concat.resample(time="1H").interpolate("linear")

                    #iterating at each hour to generate the .eri files
                    for date in date_list:

                        if 'relocatable' in glob(f'cases/{simname}/oce_files/*mdk.nc')[0]:
                            concat = concat.sel(time=slice(date_list[0],date_list[-1]),
                                                lat=slice(latitude-0.5,latitude+0.5),
                                                lon=slice(longitude-0.5,longitude+0.5))            
                        
                        #Call write eri function located in medslik.utils file
                        write_eri(concat,date,simname=simname)
                    
                    print('Met State variables written')

                    # Process for Bathymetry and Coastline Files
                    grid_string = glob(f'{simdir}{simname}/oce_files/*.nc')[0] 

                    # Bathymetry for gebco 2023
                    run_process_gebco('/Users/iatake/Dropbox (CMCC)/Work/MEDSLIK-II and Pyslick/Medslik-II/data/gebco/GEBCO_2023.nc', 
                                    grid_string, f'{simdir}{simname}/bnc_files/')
                    # gshhs in full resolution
                    run_process_gshhs('/Users/iatake/Dropbox (CMCC)/Work/MEDSLIK-II and Pyslick/Medslik-II/data/gshhs/GSHHS_shp/f/GSHHS_f_L1.shp', 
                                    grid_string, f'{simdir}{simname}/bnc_files/')

                    ##### CONFIG FILES ##### 

                    # prepare medslik_II.for and config1.txt
                    print('Preparing configuration files... ')

                    # get dimensions from ncfiles
                    #currents
                    my_o = xr.open_dataset(glob(f'cases/{simname}/oce_files/*nc')[0])

                    my_o = rename_netcdf_variables_mdk2(my_o)

                    for var in ['uo','vo','thetao']:
                        try:
                            my_o = my_o.isel(time=0,depth=0)[var].values.shape
                            found_variable = True
                        except:
                            continue
                        if not found_variable:
                            raise ValueError("Check the current state variables available in your dataset")

                    #wind
                    for var in ['U10M','u10']:
                        try:
                            my_w = xr.open_dataset(glob(f'cases/{simname}/met_files/*nc')[0]).isel(time=0)[var].values.shape
                            found_variable = True
                        except:
                            continue
                        if not found_variable:
                            raise ValueError("Check the air state variables available in your dataset")

                    nmax = np.max([np.max(my_o),np.max(my_w)])
                    imx_o = my_o[1]
                    jmx_o = my_o[0]
                    imx_w = my_w[1]
                    jmx_w = my_w[0]
                    
                    # modify medslik_ii
                    print('...medslik_ii.for...')

                    med_for = f'cases/{simname}/xp_files/medslik_II.for'

                    subprocess.run([f'cp scripts/templates/medslik_II_template.for {med_for}'],shell=True)

                    # Replacing NMAX in medslik fortran with a python function
                    search_and_replace(med_for, 'NMAX', str(nmax))

                    #not necessary at this moment
                    separate_slicks = False
                    s_volume=None
                    s_rate=None
                    if separate_slicks:
                        for i, (vol, dur) in enumerate(zip(s_volume,s_rate)):
                            write_config_files(separate_slicks=True,s_volume=vol,s_rate=dur,s_num=i)

                    else:
                        write_config_files(spill_dictionary=spill_dictionary)

                    # tags for MLFlow
                    tagss = {'Simulation_Date':sim_date.isoformat(),
                            'Discharge_Latitude':latitude,
                            'Discharge_Longitude':longitude,
                            'Simulation_Length':st.session_state['spill_length'],
                            'Oil_Spill_Duration':st.session_state['spill_duration'],
                            'Oil_Spill_Volume':st.session_state['oil_volume'],
                            'Oil_Spill_API':st.session_state['oil_api'],
                            }                

                    tfile = f'cases/{simname}/xp_files/tags.json'
                    with open(tfile, 'w') as outfile:
                        json.dump(tagss, outfile)            

                    st.text('Pre-processing for ' + simname + ' done. Proceeding.')      
