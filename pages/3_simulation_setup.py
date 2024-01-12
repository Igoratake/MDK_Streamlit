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

#Page code
    
prev_simname = st.session_state.get("Insert Simulation name", "")
simname = st.text_input("Insert Simulation name", prev_simname)

#Experiments directory
simdir = 'cases/'
raw_oce = 'data/MERCATOR/'
raw_met = 'data/ERA5/'

def search_and_replace(file_path, search_word, replace_word):
    with open(file_path, 'r') as file:
        file_contents = file.read()

        updated_contents = file_contents.replace(search_word, replace_word)

    with open(file_path, 'w') as file:
        file.write(updated_contents)

def run_process_gebco(gebco,grid,output_dir):
  
    script_name = 'scripts/pre_processing/preproc_gebco_mdk2.py'

    # Run the external Python script as a subprocess
    subprocess.run([f'{sys.executable}', script_name, gebco,grid,output_dir])

def run_process_gshhs(gshhs,grid,output_dir):
  
    script_name = 'scripts/pre_processing/preproc_gshhs_mdk2.py'

    # Run the external Python script as a subprocess
    subprocess.run([f'{sys.executable}', script_name, gshhs,grid,output_dir])


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

    if selected_file:

        ds = xr.open_dataset(selected_file)  

        if 'med' not in selected_file:
            try:
                ds = ds.rename({'latitude':'lat','longitude':'lon'})
            except:
                pass      

        min_lat,max_lat = (ds.lat.values.min(),ds.lat.values.max())
        min_lon,max_lon = (ds.lon.values.min(),ds.lon.values.max())

        start_day = str(ds.isel(time=1).time.values.max())[0:10]
        st.text(start_day)

        st.text('Coordinates are:\n'
                f'Mininum Latitude: {min_lat:.2f} Maximum Latitude: {max_lat:.2f}\n'
                f'Mininum Longitude: {min_lon:.2f} Maximum Longitude: {max_lon:.2f}\n'
                'Discharge Point must be inside this geo box'
                '\n\n'
                'The Simulation needs to start at:\n'
                f'{start_day}'
                )
        
        # Input fields for latitude, longitude, date of event, and simulation duration
        spill_hour = st.text_input(f"Spill initial time eg. (12:00)",'12:00')
        latitude = st.text_input("Latitude (decimal degrees)")
        longitude = st.text_input("Longitude (decimal degrees)")
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

        
        spill_lentgh = st.number_input("Insert simulation length", 24, max_value=hours)

        st.session_state.latitude = latitude
        st.session_state.longitude = longitude
        st.session_state.spill_hour = spill_hour
        st.session_state.spill_duration = int(spill_duration)
        st.session_state.spill_length = int(spill_lentgh)
        st.session_state.oil_api = oil_api
        if oil_volume:
            st.session_state.oil_volume = float(oil_volume)

    if (spill_lentgh and spill_duration and spill_hour 
        and latitude and longitude and oil_volume):

        if st.button("Start File Transfer"):
            
            # Process for oce files
            tot = ds.sel(depth=[0,10,30,120],method='nearest')
            tot = tot.resample(time="1H").interpolate("linear")

            for i in range(0,len(tot.time)):

                rec = tot.isel(time=i)
                dt = pd.to_datetime(rec.time.values)
                
                df = rec.to_dataframe().reset_index()
                df = df.fillna(0)
                df = df.drop(['time'],axis=1)
                df = df.pivot(index = ['lat','lon'],columns='depth',values = ['thetao','uo','vo']).reset_index()
                
                df.columns = [pair[0]+str(pair[1]).split('.')[0] for pair in df.columns]
                df = df.drop(['thetao10','thetao29','thetao119'],axis=1)
                df = df.sort_values(['lat','lon'])
                df.columns = ['lat','lon','SST','u_srf','u_10m','u_30m','u_120m','v_srf','v_10m','v_30m','v_120m']
                df = df[['lat','lon','SST','u_srf','v_srf','u_10m','v_10m','u_30m','v_30m','u_120m','v_120m']]

                if dt.hour == 0:

                    hour = 24
                    day = dt.day-1

                else:
                    hour = dt.hour
                    day = dt.day

                with open(f'cases/{simname}/oce_files/merc{dt.year-2000}{dt.month:02d}{day:02d}{hour:02d}.mrc', 'w') as f:
                    f.write(f"Ocean forecast data for {day:02d}/{dt.month:02d}/{dt.year} {hour:02d}:00\n")
                    f.write("Subregion of the Global Ocean:\n")
                    f.write(f"{df.lon.min():02.2f}  {df.lon.max():02.2f}  {df.lat.min():02.2f} {df.lat.max():02.2f}   {len(tot.lon)}   {len(tot.lat)}   Geog. limits\n")
                    f.write(f"{len(df)}   0.0\n")
                    f.write("lat        lon        SST        u_srf      v_srf      u_10m      v_10m       u_30m      v_30m      u_120m     v_120m\n")
                    
                    for index, row in df.iterrows():
                        f.write(f"{row['lat']:<10.4f}    {row['lon']:<10.4f}    {row['SST']:<10.4f}     {row['u_srf']:<10.4f}    {row['v_srf']:<10.4f}     {row['u_10m']:<10.4f}    {row['v_10m']:<10.4f}     {row['u_30m']:<10.4f}    {row['v_30m']:<10.4f}     {row['u_120m']:<10.4f}    {row['v_120m']:<10.4f}\n")
     
            
            # Proccess for met files
            eraf = glob('data/ERA5/*')
            for file in eraf:

                subprocess.run(f'cp {file} cases/{simname}/met_files/',shell=True)
                met = xr.open_dataset(file)
                dt = pd.to_datetime(met.time[0].values)
                
                met = met.isel(time=slice(0,-1))
                df = met.to_dataframe().reset_index()
                df = df.fillna(9999)
                df = df.pivot(index=['lat','lon'],columns='time',values=['U10M','V10M']).reset_index()
                df.columns = [pair[0]+str(pair[1]) for pair in df.columns]
                
                df = df.rename({'lonNaT':'lon','latNaT':'lat'},axis=1)
                df = df.sort_values(['lon','lat'], ascending=[True,False])
                
                with open(f'cases/{simname}/met_files/erai{dt.year-2000}{dt.month:02d}{dt.day:02d}.eri', 'w') as file:
                    file.write(f" 10m winds forecast data for {dt.day:02d}/{dt.month:02d}/{dt.year}\n")
                    file.write(" Subregion of the Global Ocean with limits:\n")
                    file.write(f"  {df.lon.min():02.5f}  {df.lon.max():02.5f}  {df.lat.max():02.5f}  {df.lat.min():02.5f}   {len(met.lon)}   {len(met.lat)}   Geog. limits\n")
                    file.write(f"   {len(df)}   0.0\n")
                    file.write("                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  lat        lon        u00        v00        u01       v01      u02      v02     u03     v03     u04     v04     u05     v05     u06     v06\n")
                    
                    for index, row in df.iterrows():
                        file.write(f"   {row['lat']: .4f}   {row['lon']: .4f}")
                        
                        for h in range(1,25):
                            dt_str = str(dt)
                            u_str = 'U10M' + dt_str.replace(' 00',f' {h:02d}')
                            v_str = 'V10M' + dt_str.replace(' 00',f' {h:02d}')
                            try:
                                file.write(f"    {row[u_str]: .4f}    {row[v_str]: .4f}")
                            except:
                                file.write(f"    {0: .4f}    {0: .4f}")
                                        
                            if h == 24:
                                file.write('\n')

            # Process for Bathymetry and Coastline Files
            grid_string = glob(f'{simdir}{simname}/oce_files/*_T.nc')[0] 

            # Bathymetry for gebco 2023
            run_process_gebco('data/gebco/GEBCO_2023.nc', 
                            grid_string, f'{simdir}{simname}/bnc_files/')
            # gshhs in intermediate resolution
            run_process_gshhs('data/gshhs/gshhg-shp-2.3.7/GSHHS_shp/i/GSHHS_i_L1.shp', 
                            grid_string, f'{simdir}{simname}/bnc_files/')


            # prepare Extract_II.for, medslik_II.for and config1.txt
            print('Preparing configuration files... ')

            # get dimensions from ncfiles
            my_o = xr.open_dataset(glob(f'cases/{simname}/oce_files/*nc')[0]).isel(time_counter=0).votemper.values.shape
            my_w = xr.open_dataset(glob(f'cases/{simname}/met_files/*nc')[0]).isel(time=0).U10M.values.shape

            nmax = np.max([np.max(my_o),np.max(my_w)])
            imx_o = my_o[1]
            jmx_o = my_o[0]
            imx_w = my_w[1]
            jmx_w = my_w[0]

            # modify extract
            print('...extract_ii.for...')
            config = "LC_CTYPE=C && LANG=C"
            extract_for = f'cases/{simname}/xp_files/Extract_II.for'
            xcurr = 'XCURR'
            ycurr = 'YCURR'
            xwind = 'XWIND'
            ywind = 'YWIND'

            subprocess.run([f'cp scripts/templates/Extract_II_template.for {extract_for}'],shell=True)

            subprocess.run([f"{config} sed -i s/{xcurr}/{imx_o}/g {extract_for}"],shell=True)
            subprocess.run([f"{config} sed -i s/{ycurr}/{jmx_o}/g {extract_for}"],shell=True)
            subprocess.run([f"{config} sed -i s/{xwind}/{imx_w}/g {extract_for}"],shell=True)
            subprocess.run([f"{config} sed -i s/{ywind}/{jmx_w}/g {extract_for}"],shell=True)
           
            # modify medslik_ii
            print('...medslik_ii.for...')

            med_for = f'cases/{simname}/xp_files/medslik_II.for'

            subprocess.run([f'cp scripts/templates/medslik_II_template.for {med_for}'],shell=True)

            # Replacing NMAX in medslik fortran with a python function
            search_and_replace(med_for, 'NMAX', str(nmax))

            # # modify config_1.txt
            print('...config1.txt...')

            config_file = f'cases/{simname}/xp_files/config1.txt'

            subprocess.run([f'cp scripts/templates/config1_template_0.txt {config_file}'],shell=True)

            #adding spill date
            subprocess.run([f"{config} sed -i s#RUNNAME#{simname}#g {config_file}"],shell=True)
            subprocess.run([f"{config} sed -i s/DD/{sim_date.day:02d}/ {config_file}"],shell=True)
            subprocess.run([f"{config} sed -i s/MM/{sim_date.month:02d}/ {config_file}"],shell=True)
            subprocess.run([f"{config} sed -i s/YY/{sim_date.year-2000}/ {config_file}"],shell=True)
            subprocess.run([f"{config} sed -i s/HH/{sim_date.hour:02d}/ {config_file}"],shell=True)
            subprocess.run([f"{config} sed -i s/mm/{sim_date.minute:02d}/ {config_file}"],shell=True)   

            #adding simulation length
            subprocess.run([f"{config} sed -i s/SIMLENGTH/{st.session_state['spill_length']:04d}/ {config_file}"],shell=True)       

            #  adding spill coordinates - dd for degrees and mm for minutes
            # Latitude
            dd = int(latitude)
            mm = (float(latitude)-dd)*60          
            subprocess.run([f"{config} sed -i s/LATd/{dd:02d}/ {config_file}"],shell=True)
            subprocess.run([f"{config} sed -i s/LATm/{mm:.3f}/ {config_file}"],shell=True)
           
           # Longitude
            dd = int(longitude)
            mm = (float(longitude)-dd)*60
            subprocess.run([f"{config} sed -i s/LONd/{dd:02d}/ {config_file}"],shell=True)
            subprocess.run([f"{config} sed -i s/LONm/{mm:.3f}/ {config_file}"],shell=True)

            # spill duration
            subprocess.run([f"{config} sed -i s/SDUR/{st.session_state['spill_duration']:04d}/ {config_file}"],shell=True)

            # spill volume
            subprocess.run([f"{config} sed -i s/SRATE/{st.session_state['oil_volume']:08.2f}/ {config_file}"],shell=True)

            # oil characteristics
            subprocess.run([f"{config} sed -i s/APIOT/{oil_api}/ {config_file}"],shell=True)


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

            # # add spill polygon
            # n_slicks=np.loadtxt(xp_folder + '/' + folder_name + '/xp_files/n_poly.txt')
            # subprocess.run({config} sed -i '' 's/N_SLICKS/" + str(int(n_slicks)) + "/' " + xp_folder + '/' + folder_name + '/xp_files/config1_.txt')
            # subprocess.run({config} sed -i '' 's/APIOT/30.8/' " + xp_folder + '/' + folder_name + '/xp_files/config1_.txt')
            # subprocess.run('cat '  + xp_folder + '/' + folder_name + '/xp_files/config1_.txt ' + xp_folder + '/' + folder_name + '/xp_files/poly_mdk_fmt.txt > ' + xp_folder + '/' + folder_name + '/xp_files/config1.txt')

            st.text('Pre-processing for ' + simname + ' done. Proceeding.')      
