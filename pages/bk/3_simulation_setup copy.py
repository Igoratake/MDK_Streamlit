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

    dsname = f'{simdir}{simname}/oce_files/temp.nc'
    dsname2 = f'{simdir}{simname}/oce_files/temp2.nc'
    dsname3 = f'{simdir}{simname}/oce_files/temp3.nc'
    dsname4 = f'{simdir}{simname}/oce_files/temp4.nc'

    if selected_file:
        
        if 'ds' not in globals():
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

            ds.close()
            rec.to_netcdf(dsname)

        min_lat,max_lat = (rec.nav_lat.values.min(),rec.nav_lat.values.max())
        min_lon,max_lon = (rec.nav_lon.values.min(),rec.nav_lon.values.max())

        start_day = str(rec.isel(time_counter=1).time_counter.values.max())[0:10]
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
        last_date = pd.to_datetime(rec.time_counter.values[-1])

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
        st.session_state.oil_volume = float(oil_volume)

    if (spill_lentgh and spill_duration and spill_hour 
        and latitude and longitude and oil_volume):

        if st.button("Start File Transfer"):
            
            # Process for oce files
            rec2 = xr.open_dataset(dsname)          

            inidate = rec2.time_counter[0].values.astype('datetime64[D]').item()
            enddate = rec2.time_counter[-1].values.astype('datetime64[D]').item()
            
            # Display the selected file
            st.write(f"Date range is from {inidate.day}/{inidate.month}/{inidate.year} to {enddate.day}/{enddate.month}/{enddate.year}")

            subprocess.run([f'cdo -inttime,{inidate.year}-{inidate.month}-{inidate.day},12:00:00,1hour {dsname} {dsname2}'],shell=True,check=True)

            for var,varr in zip(['U','V','T'],['vozocrtx','vomecrty','votemper']):
                for t in rec2.time_counter:
                    
                    tt = t.values.astype('datetime64[D]').item()
                    day = str(tt.day).zfill(2)
                    month = str(tt.month).zfill(2)
                    year = str(tt.year)[2:]
                    subprocess.run([f'cdo seldate,{tt.year}-{tt.month}-{tt.day}T01:00:00,{tt.year}-{tt.month}-{tt.day+1}T00:00:00 {dsname2} {dsname3}'],shell=True,check=True)

                    # dss = xr.open_dataset(dsname3)

                    # dss2 = dss[['depth','nav_lat','nav_lon','time_counter',varr]]

                    # dss.close()

                    # dss2.to_netcdf(dsname4)                

                    # dss2.close()
                    if var =='T':
                        subprocess.run([f'ncks -O -x -v  vozocrtx,vomecrty {dsname3} {dsname4}'],shell=True)
                    if var =='U':
                        subprocess.run([f'ncks -O -x -v  votemper,vomecrty {dsname3} {dsname4}'],shell=True)
                    if var =='V':
                        subprocess.run([f'ncks -O -x -v  vozocrtx,votemper {dsname3} {dsname4}'],shell=True)

                    subprocess.run([f'cdo -O -b F32 setmisstoc,9999 -setmissval,9999 {dsname4} {simdir}{simname}/oce_files/MDK_ocean_{year}{month}{day}_{var}.nc'],shell=True)

                    subprocess.run(f'rm {dsname3}',shell=True,check=True)
                    subprocess.run(f'rm {dsname4}',shell=True,check=True)

            subprocess.run(f'rm {dsname}',shell=True,check=True)
            subprocess.run(f'rm {dsname2}',shell=True,check=True)       
            
            # Proccess for met files
            eraf = glob('data/ERA5/*')
            for file in eraf:
                mds = xr.open_dataset(file)
                mds2 = mds[['time','lat','lon','U10M','V10M']]
                mds2.to_netcdf(f"cases/{simname}/met_files/{file.split('_')[-1]}")
                # subprocess.run([f"cp {file} cases/{simname}/met_files/{file.split('_')[-1]}"],shell=True)

            # Process for Bathymetry and Coastline Files
            grid_string = glob(f'{simdir}{simname}/oce_files/*_T.nc')[0] 

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
