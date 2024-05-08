import streamlit as st

#copernicus library
import copernicusmarine

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
from scripts import *

def collect_down():
    
    st.write(st.session_state.down)

def collect_user():
    
    st.write(st.session_state.user)

def collect_psd():
    
    st.write(st.session_state.psd)

def check_land(lon,lat):

    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    point = Point(lon, lat)

    is_within_land = world.geometry.contains(point).any()
    
    if is_within_land:
        sea=0
    else:
        sea=1

    return sea

# def run_download_mercator(inidate,enddate,inidep,enddep,lat_min,lat_max,lon_min,lon_max,down,output_path,user,psd):
  
#     script_name = 'functions/download_mercator_parser.py'

#     # Run the external Python script as a subprocess
#     subprocess.run([f'{sys.executable}', script_name, inidate,enddate,inidep,enddep,lat_min,lat_max,lon_min,lon_max,down,output_path,user,psd])

def download_mercator(min_lat,max_lat,min_lon,max_lon,min_depth,max_depth,
                      start_time,end_time,
                      region,output_path,output_name,
                      user,password):  

    if region == 'global':
        dataset_id_curr = "cmems_mod_med_phy-cur_anfc_4.2km-3D_PT1H-m"
        dataset_id_temp = "cmems_mod_med_phy-tem_anfc_4.2km-3D_PT1H-m"

    else:
        dataset_id_curr = "cmems_mod_med_phy-cur_anfc_4.2km-3D_PT1H-m"
        dataset_id_temp = "cmems_mod_med_phy-tem_anfc_4.2km-2D_PT1H-m"

    files = []
    for dataset in [dataset_id_curr,dataset_id_temp]:
    
        if 'cur' in dataset:
            copernicusmarine.subset(
                dataset_id=dataset_id_curr,
                variables=["uo", "vo"],
                minimum_longitude=min_lon,
                maximum_longitude=max_lon,
                minimum_latitude=min_lat,
                maximum_latitude=max_lat,
                start_datetime=start_time,
                end_datetime=end_time,
                minimum_depth=min_depth,
                maximum_depth=max_depth,
                output_filename = "curr.nc",
                output_directory = output_path,
                username=user,
                password=password,
                force_download=True
                )
            
            files.append(output_path+'curr.nc')
        else:
            copernicusmarine.subset(
                dataset_id=dataset_id_temp,
                variables=["thetao"],
                minimum_longitude=min_lon,
                maximum_longitude=max_lon,
                minimum_latitude=min_lat,
                maximum_latitude=max_lat,
                start_datetime=start_time,
                end_datetime=end_time,
                output_filename = "temp.nc",
                output_directory = output_path,
                username=user,
                password=password,
                force_download=True
                )
            
            files.append(output_path+'temp.nc')
        
    #Transform to medslik standards
    ds = xr.open_mfdataset(files)

    # Rename variables only if they exist in the dataset
    ds = rename_netcdf_variables_mdk2(ds)

    #Selecting only 4 layers
    ds = ds.sel(depth=[0,10,30,120],method='nearest')
    #Modifying labels to simplfy drop in temperature columns
    ds['depth'] = [0,10,30,120]

    #Selecting only the relavent variables
    ds = ds[['uo','vo','thetao']]

    #saves the daily current or temperature netcdf in the case dir
    ds.to_netcdf(output_name)

    #remove the temporary files
    subprocess.run([f'rm -rf {output_path}/curr.nc {output_path}/temp.nc'],shell=True)


def run_download_era5(lat_min,lon_min,lat_max,lon_max,inidate,enddate,output_path):
    
    script_name = 'functions/download_era5_parser.py'

    # Run the external Python script as a subprocess
    subprocess.run([f'{sys.executable}', script_name, lat_min,lon_min,lat_max,lon_max,inidate,enddate,output_path])

def validate_date(date):
    
    try: 
        dt=datetime.datetime.strptime(date,'%d/%m/%Y')
        if dt > datetime.datetime.today():
            dt = 'Date provided is in the future. No data will be available'               
        
    except:
        dt = 'Wrong date format'

    return dt


#Page code

safety_check=False

st.set_page_config(page_title="Downloading Data", page_icon="⬇️")


# Initialize the previous input values
prev_down = st.session_state.get("Download values", 'global')
st.session_state['down'] = prev_down

prev_latitude = st.session_state.get("latitude (decimal degrees)", '')
prev_longitude = st.session_state.get("longitude (decimal degrees)", '')
prev_delta = st.session_state.get("Max and Min around Discharge (decimal degrees)", "0.5")
prev_inidep = st.session_state.get("Initial depth (meters)", 0)
prev_enddep = st.session_state.get("Final depth (meters)", 120)
prev_inidate = st.session_state.get("Initial Date", "")
prev_enddate = st.session_state.get("End Date", "")
prev_simulation_duration = st.session_state.get("Simulation Lengh (hours)", 48)
prev_simulation_data = st.session_state.get("Data Source", 'glo')

st.header('Area of interest')

coord_type = st.radio("Select from Lat and Lon values or from map",
    ["Fixed values ", 'map'])

if coord_type == 'map':

    st.text('Only the last drawing will be considered for download')

    m = folium.Map(location=[0, 0], zoom_start=3)
    Draw(export=True,
         draw_options={"polyline": False,"polygon": False,"circle": False,"circlemarker": False},
         edit_options=False,
         ).add_to(m)
    # st_folium(m, width=700, height=500)

    output = st_folium(m, width=700, height=500,returned_objects=["last_active_drawing"])

    if output["last_active_drawing"] == None:
        st.text('Select a location')
      
    elif output["last_active_drawing"]["geometry"]["type"] == 'Polygon':
        point = False
        #obtaining the last polygon
        marker = output["last_active_drawing"]["geometry"]['coordinates'][0]
        #left bottom coordinates
        plbx = marker[0][0]
        plby = marker[0][1]
        #left upper coordinates
        plux = marker[1][0]
        pluy = marker[1][1]
        #right upper coordinates
        prux = marker[2][0]
        pruy = marker[2][1]
        #right bottom coordinates
        prbx = marker[3][0]
        prby = marker[3][1]

        #check if sizes are less than 2 degrees
        if abs(plbx - prbx) > 2 or abs(plby - pruy) >2:
            st.text('The area selected is too big, please draw a smaller one')
            safety_check=False

        #check for each vertex if they lie on land
        sea =  check_land(plbx,plby)
        if sea==0:
            st.text('One of your vertex lie within land, please draw only on water')
            safety_check = False
        sea =  check_land(plux,pluy)
        if sea==0:
            st.text('One of your vertex lie within land, please draw only on water')
            safety_check = False
        sea =  check_land(prbx,prby)
        if sea==0:
            st.text('One of your vertex lie within land, please draw only on water')
            safety_check = False
        sea =  check_land(prux,pruy)
        if sea==0:
            st.text('One of your vertex lie within land, please draw only on water')
            safety_check = False

        lat_min = float(plby)
        lat_max = float(pluy)
        lon_min = float(plbx)
        lon_max = float(prbx)

        latitude = np.mean([lat_min,lat_max])
        longitude = np.mean([lon_min, lon_max])

        lonmin_col,latmin_col,lonmax_col,latmax_col = st.columns(4)

        lonmin_col.metric('Minimum Longitude',f'{lon_min:.2f} degrees')
        latmin_col.metric('Minimum latitude',f'{lat_min:.2f} degrees')
        lonmax_col.metric('Maximum Longitude',f'{lon_max:.2f} degrees')
        latmax_col.metric('Maximum latitude',f'{lat_max:.2f} degrees')

        safety_check = True

    elif output["last_active_drawing"]["geometry"]["type"] == 'Point':
        point=True
        marker = output["last_active_drawing"]["geometry"]
        px = marker['coordinates'][0]
        py = marker['coordinates'][1]

        sea =  check_land(px,py)    

        if sea==0:
            st.text('Your coordinates lie within land. Please check your values again')
            safety_check = False
        
        else:
            point=True
            st.text("A 0.5 degree box will be obtained around this point provided")

            lon_col,lat_col = st.columns(2)

            lon_col.metric('Longitude',f'{px:.2f} degrees')
            lat_col.metric('latitude',f'{py:.2f} degrees')

            longitude = px
            latitude = py
            safety_check = True
            

else:
    st.text('Please input the coordinates of the oil spill or area you wish to download data from')
    # Input fields for latitude, longitude, date of event, and simulation duration
    latitude = st.text_input("Latitude (decimal degrees)", prev_latitude)
    longitude = st.text_input("Longitude (decimal degrees)", prev_longitude)

    if longitude and latitude:
        sea =  check_land(longitude,latitude)    

        if sea==0:
            st.text('Your coordinates lie within land. Please check your values again')
            safety_check = False 
        else:
            st.text('your download area will approximately 0.5 degrees around the discharge location')
            st.text(f'Latitude: {float(latitude)-0.5:.2f}-{float(latitude)+0.5:.2f}')
            st.text(f'Longitude: {float(longitude)-0.5:.2f}-{float(longitude)+0.5:.2f}')
            st.text('\n')
            st.text('\n')
            st.text(f'Change box below only if necessary')        
            
            safety_check = True 

if safety_check == True:

    if 30.37 < float(latitude) < 45.7 and -17.25 < float(longitude) < 35.9:
        st.text('Coordinates lie within Mediterranean Sea')
        
        seadata = st.radio(
            "Use Local or global data?",
            ['Med Sea Data', "Global Forecast Data"],
            captions = ["More Refined", "Coarser"], on_change = collect_down)

        if seadata == 'Med Sea Data':
            st.session_state['down'] = 'local'
        else:
            st.session_state['down'] = 'global'

    st.text(st.session_state['down'])

    if point == True:
        delta = st.text_input("Delta latitude and longitude (degrees). Only used if select from point", prev_delta)
        lat_min = latitude - float(delta)
        lat_max = latitude + float(delta)
        lon_min = longitude - float(delta)
        lon_max = longitude + float(delta)

    inidep = st.number_input("Initial depth (meters)", min_value=0,value=prev_inidep)
    enddep = st.number_input("Final depth (meters)", max_value=120,value=prev_enddep)
    
    st.text('By default, files download start as 12:00 os selected day')
    st.text('To ensure Medslik-II interpolation, files will be downloaded from one day prior to the selected date')
    st.text('Please insert simulaton date: DD/MM/YYYY format')
    inidate = st.text_input("Starting date", prev_inidate)

    if inidate:

        dt = validate_date(inidate)

        if isinstance(dt,str):
            st.text(dt)

        else:
            #starting one day prior to informed date
            dtini = dt - datetime.timedelta(days=1)
            if (datetime.datetime.today()-dt).days <10:
                st.text('ERA5 data might not be available in the selected date')
            
            inidate = f'{dtini.year}-{str(dtini.month).zfill(2)}-{str(dtini.day).zfill(2)}'
            inidate2 = inidate + 'T00:00:00Z'              

            st.text('Please insert simulaton duration in hours. Max value is 96 hours')
            simulation_duration = st.number_input("Simulation Lengh (hours)", min_value=1, max_value = 96, 
                                                value=prev_simulation_duration)                                
            
            duration  = np.ceil(simulation_duration/24)
            dtend = dt + datetime.timedelta(days=duration +1) 

            enddate = f'{dtend.year}-{str(dtend.month).zfill(2)}-{str(dtend.day).zfill(2)}'
            enddate2 = enddate + 'T00:00:00Z'         

            # Store the current input values in session_state
            st.session_state.latitude = latitude
            st.session_state.longitude = longitude
            st.session_state.inidep = inidep
            st.session_state.enddep = enddep
            if point:
                st.session_state.delta = delta
            st.session_state.inidate = inidate
            st.session_state.enddate = enddate
            st.session_state.simulation_duration = simulation_duration

        # Insert your Mercator User
            u = st.text_input("Insert your Mercator username", on_change=collect_user)

            st.session_state['user'] = u

            # Insert your Mercator User
            p = st.text_input("Insert your Mercator password", type='password',on_change=collect_psd)

            st.session_state['psd'] = p
            
            if enddate:
                if u and p:  
                    st.header('Inputs are validated. Ready to download')

                    # Button to run the simulation
                    if st.button("Download data"):             
                    
                        #Ocean/Sea Data                        
                        output_path = 'data/MERCATOR/'
                        output_name = output_path + f'Mercator_analysis_{str(dt.year)+str(dt.month).zfill(2)+str(dt.day).zfill(2)}_mdk.nc'
                        
                        # Subset for ocean currents
                        download_mercator(lat_min,lat_max,lon_min,lon_max,0,120,
                                inidate,enddate,
                                st.session_state['down'],output_path=output_path,output_name=output_name,
                                user=u,password=p)

                        st.write("Mercator data downloaded!")                            
                        
                        #Met Data
                        output_path = 'data/ERA5/'

                        output_name = output_path + f'era5_winds10_{str(dt.year)+str(dt.month).zfill(2)+str(dt.day).zfill(2)}_mdk.nc'

                        # Create a thread to run the external script in the background
                        script_thread = threading.Thread(target=run_download_era5(str(lat_min),str(lon_min),str(lat_max),str(lon_max),
                                                                                  inidate,enddate,
                                                                                  output_path=output_path))

                        # Start the thread
                        script_thread.start()

                        # Wait for the thread to finish (optional, can continue with the Streamlit app while the script runs)
                        script_thread.join()

                        # Rename variables only if they exist in the dataset
                        met = xr.open_mfdataset('data/ERA5/temp*.nc')
                        met = rename_netcdf_variables_mdk2(met)

                        met.to_netcdf(output_name)

                        #remove the temporary files
                        subprocess.run([f'rm -rf {output_path}/temp*.nc'],shell=True)

                        st.write("ERA5 data downloaded!")

                        del u,p
                else:
                    st.text('Copernicus user is missing or not validated!')
    else:
        st.text('Waiting for Latitude and Longitude values')
                    
                

