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

#system libs
import os
import sys
import time
import datetime
import subprocess
import threading
from glob import glob

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

def run_download_mercator(inidate,enddate,inidep,enddep,latitude,longitude,delta,down,output_path,user,psd):
  
    script_name = 'functions/download_mercator_parser.py'

    # Run the external Python script as a subprocess
    subprocess.run([f'{sys.executable}', script_name, inidate,enddate,inidep,enddep,
                    latitude,longitude,delta,down,output_path,user,psd])

def run_download_era5(latitude,longitude,delta,inidate,enddate,output_path):
    
    script_name = 'functions/download_era5_parser.py'

    # Run the external Python script as a subprocess
    subprocess.run([f'{sys.executable}', script_name, latitude,longitude,delta,inidate,enddate,output_path])

def validate_date(date):
    
    try: 
        dt=datetime.datetime.strptime(date,'%d/%m/%Y')
        if dt > datetime.datetime.today():
            dt = 'Date provided is in the future. No data will be available'               
        
    except:
        dt = 'Wrong date format'

    return dt


#Page code

st.set_page_config(page_title="Downloading Data", page_icon="⬇️")


# Initialize the previous input values
prev_down = st.session_state.get("Download values", 'global')
st.session_state['down'] = prev_down

prev_latitude = st.session_state.get("latitude (decimal degrees)", '')
prev_longitude = st.session_state.get("longitude (decimal degrees)", '')
prev_delta = st.session_state.get("Max and Min around Discharge (decimal degrees)", "0.5")
prev_inidep = st.session_state.get("Initial depth (meters)", 0)
prev_enddep = st.session_state.get("Final depth (meters)", 150)
prev_inidate = st.session_state.get("Initial Date", "")
prev_enddate = st.session_state.get("End Date", "")
prev_simulation_duration = st.session_state.get("Simulation Lengh (hours)", 48)
prev_simulation_data = st.session_state.get("Data Source", 'glo')

st.header('Area of interest')
st.text('Please input the coordinates of the oil spill or area you wish to download data from')
# Input fields for latitude, longitude, date of event, and simulation duration
latitude = st.text_input("Latitude (decimal degrees)", prev_latitude)
longitude = st.text_input("Longitude (decimal degrees)", prev_longitude)

if latitude and longitude:
    sea =  check_land(longitude,latitude)    

    if sea==0:
        st.text('Your coordinates lie within land. Please check your values again')
    
    else:

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

        st.text('your download area will approximately 0.5 degrees around the discharge location')
        st.text(f'Latitude: {float(latitude)-0.5:.2f}-{float(latitude)+0.5:.2f}')
        st.text(f'Longitude: {float(longitude)-0.5:.2f}-{float(longitude)+0.5:.2f}')
        st.text('\n')
        st.text('\n')
        st.text(f'Change box below only if necessary')
        
        delta = st.text_input("Delta latitude and longitude (degrees)", prev_delta)            

        inidep = st.text_input("Initial depth (meters)", prev_inidep)
        enddep = st.text_input("Final depth (meters)", prev_enddep)
        
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
                            
                            # Create a thread to run the external script in the background
                            script_thread = threading.Thread(target=run_download_mercator(inidate2,enddate2,inidep,enddep,
                                                                    latitude,longitude,delta,
                                                                    st.session_state['down'],output_path=output_path,
                                                                    user = u,psd = p))

                            # Start the thread
                            script_thread.start()

                            # Wait for the thread to finish (optional, can continue with the Streamlit app while the script runs)
                            script_thread.join()

                            st.write("Mercator data downloaded!")                            
                            
                            #Met Data
                            output_path = 'data/ERA5/'

                            # Create a thread to run the external script in the background
                            script_thread = threading.Thread(target=run_download_era5(latitude,longitude,delta,inidate,enddate,output_path=output_path))

                            # Start the thread
                            script_thread.start()

                            # Wait for the thread to finish (optional, can continue with the Streamlit app while the script runs)
                            script_thread.join()

                            st.write("ERA5 data downloaded!")

                            del u,p
                    else:
                        st.text('Copernicus user is missing or not validated!')
                    
                   

