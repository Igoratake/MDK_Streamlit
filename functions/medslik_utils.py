#geo libs
import xarray as xr
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import Point
# from folium.plugins import HeatMap
# from streamlit_folium import st_folium,folium_static

#numerical and plotting libs
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import plotly.figure_factory as ff

#system libs
import os
import sys
import time
import datetime
import subprocess
import threading
from glob import glob
import multiprocessing

'''

This script contains several functions that can be used across MEDSLIK-II modeling.

'''

def check_land(lon,lat):

    '''
    This script receives a lon and lat value and  checks if the position is within land or sea
    It uses a shapefile of world boundaries currently based in geopandas database

    In case a position is on land:
        Script returns 0, since it will not be possible to simulate oil spill on land
    
    Otherwise returns 1 

    '''

    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    point = Point(lon, lat)

    is_within_land = world.geometry.contains(point).any()
    
    if is_within_land:
        sea=0
    else:
        sea=1

    return sea

def validate_date(date):

    '''
    Convert a date in string format to datetime, checking if the date provided is valid

    It also checks if date is in the future, blocking the user to procced

    '''

    try: 
        dt=datetime.datetime.strptime(date,'%d/%m/%Y %H:%M')
        if dt > datetime.datetime.today():
            dt = 'Date provided is in the future. No data will be available'               
        
    except:
        dt = 'Wrong date format'

    return dt

def search_and_replace(file_path, search_word, replace_word):
    with open(file_path, 'r') as file:
        file_contents = file.read()

        updated_contents = file_contents.replace(search_word, replace_word)

    with open(file_path, 'w') as file:
        file.write(updated_contents)

def write_cds(key):

    with open('~.cdsapirc_test') as f:
        f.write('url: https://cds.climate.copernicus.eu/api/v2\n')
        f.write(f'key: {key}\n')
        f.write('verify: 0')
        f.close()

def write_mrc(ds,simname=None):

    '''
    This function write the currents and sea surface temperature files for Medslik-II.

    Data has to be passed in hourly format and in netcdf format

    '''

#iterating at each hour to generate the .mrc files
    for i in range(0,len(ds.time)):            
        #select the i time instant
        rec = ds.isel(time=i)
        #get the datetime values from that instant
        try:
            dt = pd.to_datetime(rec.time.values)
        except:
            try:
                dt = datetime.datetime.strptime(str(rec.time.values),'%Y-%m-%d %H:%M:%S')
            except:
                raise ValueError('Datetime from the dataset in on an unknown format')
        
        #transforms it from xarray datset to pandas dataframe to facilitate the processes of adjusting values
        df = rec.to_dataframe().reset_index()
        df = df.fillna(0)
        df = df.drop(['time'],axis=1)
        #pivoting it in order to create the same pattern in .mrc files
        df = df.pivot(index = ['lat','lon'],columns='depth',values = ['thetao','uo','vo']).reset_index()
        #join colum information to 
        df.columns = [pair[0]+str(pair[1]).split('.')[0] for pair in df.columns]
        #dropping temperature columns
        df = df.drop(['thetao10','thetao30','thetao120'],axis=1)
        #sort first by latitude and then by longitude
        df = df.sort_values(['lon','lat'])
        df.columns = ['lat','lon','SST','u_srf','u_10m','u_30m','u_120m','v_srf','v_10m','v_30m','v_120m']
        df = df[['lat','lon','SST','u_srf','v_srf','u_10m','v_10m','u_30m','v_30m','u_120m','v_120m']]

        #making sure that .mrc files in 0 hour are written as 24
        #this code also makes sure that the file is written correctly even in the transition of months
        if dt.hour == 0:
            hour = 24
            day = (dt - datetime.timedelta(hours=1)).day
        else:
            hour = dt.hour
            day = dt.day

        #writing the current files
        with open(f'cases/{simname}/oce_files/merc{dt.year-2000:02d}{dt.month:02d}{day:02d}{hour:02d}.mrc', 'w') as f:
            f.write(f"Ocean forecast data for {day:02d}/{dt.month:02d}/{dt.year} {hour:02d}:00\n")
            f.write("Subregion of the Global Ocean:\n")
            f.write(f"{df.lon.min():02.2f}  {df.lon.max():02.2f}  {df.lat.min():02.2f} {df.lat.max():02.2f}   {len(rec.lon)}   {len(rec.lat)}   Geog. limits\n")
            f.write(f"{len(df)}   0.0\n")
            f.write("lat        lon        SST        u_srf      v_srf      u_10m      v_10m       u_30m      v_30m      u_120m     v_120m\n")
            
            for index, row in df.iterrows():
                f.write(f"{row['lat']:<10.4f}    {row['lon']:<10.4f}    {row['SST']:<10.4f}     {row['u_srf']:<10.4f}    {row['v_srf']:<10.4f}     {row['u_10m']:<10.4f}    {row['v_10m']:<10.4f}     {row['u_30m']:<10.4f}    {row['v_30m']:<10.4f}     {row['u_120m']:<10.4f}    {row['v_120m']:<10.4f}\n")

    print('Sea State variables written')

def write_eri(ds,date,simname=None):

    '''
    This function write the wind velocity as 10 m files for Medslik-II.

    Data has to be passed in hourly format and in netcdf format

    '''

    #iterating at each hour to generate the .eri files     
    try:
        date1 = f'{date.year}-{date.month:02d}-{date.day:02d} 00:00'
        date2 = f'{date.year}-{date.month:02d}-{date.day:02d} 23:00'
        met = ds.sel(time = slice(date1,date2))
        #getting date from the netcdf
        try:
            dt = pd.to_datetime(met.time[0].values)
        except:
            dt = datetime.datetime.strptime(str(met.time[0].values),'%Y-%m-%d %H:%M:%S')
        df = met.to_dataframe().reset_index()
        df = df.fillna(9999)
        df = df.pivot(index=['lat','lon'],columns='time',values=['U10M','V10M']).reset_index()
        df.columns = [pair[0]+str(pair[1]) for pair in df.columns]
        
        df = df.rename({'lonNaT':'lon','latNaT':'lat'},axis=1)
        df = df.sort_values(['lon','lat'], ascending=[True,False])
        
        #writing the wind files
        with open(f'cases/{simname}/met_files/erai{dt.year-2000:02d}{dt.month:02d}{dt.day:02d}.eri', 'w') as file:
            file.write(f" 10m winds forecast data for {dt.day:02d}/{dt.month:02d}/{dt.year}\n")
            file.write(" Subregion of the Global Ocean with limits:\n")
            file.write(f"  {df.lon.min():02.5f}  {df.lon.max():02.5f}  {df.lat.max():02.5f}  {df.lat.min():02.5f}   {len(met.lon)}   {len(met.lat)}   Geog. limits\n")
            file.write(f"   {len(df)}   0.0\n")
            file.write("                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  lat        lon        u00        v00        u01       v01      u02      v02     u03     v03     u04     v04     u05     v05     u06     v06\n")
            
            for index, row in df.iterrows():
                file.write(f"   {row['lat']: .4f}   {row['lon']: .4f}")
                
                for h in range(1,25):
                    try:
                        file.write(f"    {row.iloc[1+h]: .4f}    {row.iloc[25+h]: .4f}")
                    except:
                        file.write(f"    {0: .4f}    {0: .4f}")
                                
                    if h == 24:
                        file.write('\n')     

    except:
        print(f'{date} has no files in met directory')
        pass

def process_mrc(i, concat,simname=None):
    
    rec = concat.isel(time=i)
    #get the datetime values from that instant
    try:
        dt = pd.to_datetime(rec.time.values)
    except:
        try:
            dt = datetime.datetime.strptime(str(rec.time.values),'%Y-%m-%d %H:%M:%S')
        except:
            raise ValueError('Datetime from the dataset in on an unknown format')
    
    #transforms it from xarray datset to pandas dataframe to facilitate the processes of adjusting values
    df = rec.to_dataframe().reset_index()
    df = df.fillna(0)
    df = df.drop(['time'],axis=1)
    #pivoting it in order to create the same pattern in .mrc files
    df = df.pivot(index = ['lat','lon'],columns='depth',values = ['thetao','uo','vo']).reset_index()
    #join colum information to 
    df.columns = [pair[0]+str(pair[1]).split('.')[0] for pair in df.columns]
    #dropping temperature columns
    df = df.drop(['thetao10','thetao30','thetao120'],axis=1)
    #sort first by latitude and then by longitude
    df = df.sort_values(['lon','lat'])
    df.columns = ['lat','lon','SST','u_srf','u_10m','u_30m','u_120m','v_srf','v_10m','v_30m','v_120m']
    df = df[['lat','lon','SST','u_srf','v_srf','u_10m','v_10m','u_30m','v_30m','u_120m','v_120m']]

    #making sure that .mrc files in 0 hour are written as 24
    #this code also makes sure that the file is written correctly even in the transition of months
    if dt.hour == 0:
        hour = 24
        day = (dt - datetime.timedelta(hours=1)).day
        month = (dt - datetime.timedelta(hours=1)).month
    else:
        hour = dt.hour
        day = dt.day
        month = dt.month

    #writing the current files
    with open(f'cases/{simname}/oce_files/merc{dt.year-2000:02d}{month:02d}{day:02d}{hour:02d}.mrc', 'w') as f:
        f.write(f"Ocean forecast data for {day:02d}/{month:02d}/{dt.year} {hour:02d}:00\n")
        f.write("Subregion of the Global Ocean:\n")
        f.write(f"{df.lon.min():02.2f}  {df.lon.max():02.2f}  {df.lat.min():02.2f} {df.lat.max():02.2f}   {len(rec.lon)}   {len(rec.lat)}   Geog. limits\n")
        f.write(f"{len(df)}   0.0\n")
        f.write("lat        lon        SST        u_srf      v_srf      u_10m      v_10m       u_30m      v_30m      u_120m     v_120m\n")
        
        for index, row in df.iterrows():
            f.write(f"{row['lat']:<10.4f}    {row['lon']:<10.4f}    {row['SST']:<10.4f}     {row['u_srf']:<10.4f}    {row['v_srf']:<10.4f}     {row['u_10m']:<10.4f}    {row['v_10m']:<10.4f}     {row['u_30m']:<10.4f}    {row['v_30m']:<10.4f}     {row['u_120m']:<10.4f}    {row['v_120m']:<10.4f}\n")

# Define a function to process multiple time steps in parallel
def parallel_processing_mrc(concat,simname=None):
    num_time_steps = len(concat.time)
    pool = multiprocessing.Pool()  # Create a pool of workers
    results = [pool.apply_async(process_mrc, args=(i, concat,simname)) for i in range(num_time_steps)]
    pool.close()  # Close the pool, no more tasks can be submitted
    pool.join()   # Wait for all worker processes to finish

def run_process_gebco(gebco,grid,output_dir):
  
    script_name = 'scripts/pre_processing/preproc_gebco_mdk2.py'

    # Run the external Python script as a subprocess
    subprocess.run([f'{sys.executable}', script_name, gebco,grid,output_dir])

def run_process_gshhs(gshhs,grid,output_dir):
  
    script_name = 'scripts/pre_processing/preproc_gshhs_mdk2.py'

    # Run the external Python script as a subprocess
    subprocess.run([f'{sys.executable}', script_name, gshhs,grid,output_dir])

def write_config_files(spill_dictionary = None,use_slk_contour=False,separate_slicks=False,s_volume=None,s_rate=None,s_num=None):

    #obtaining the variables
    simname = spill_dictionary['simname']
    dt_sim = spill_dictionary['dt_sim']
    sim_length = spill_dictionary['sim_length']
    longitude = spill_dictionary['longitude']
    latitude = spill_dictionary['latitude']
    spill_duration = spill_dictionary['spill_duration']
    spill_rate = spill_dictionary['spill_rate']
    oil_api = spill_dictionary['oil_api']
    number_slick = spill_dictionary['number_slick']

     # # modify config_1.txt
    print('...config1.txt...')

    # Iterating through slicks or doing for single simulation
    if separate_slicks == False:
        config_file = f'cases/{simname}/xp_files/config1.txt'
    
    else:
        config_file = f'cases/{simname}/xp_files/slick{s_num+1}/config1.txt'

    subprocess.run([f'cp scripts/templates/config1_template_0.txt {config_file}'],shell=True)

    #adding spill Name - Add slick number if separate slicks
    if separate_slicks == False:
        search_and_replace(config_file, 'RUNNAME', simname)
    else:
        search_and_replace(config_file, 'RUNNAME', simname+f'_slick{s_num+1}')

    #adding spill date and hour information
    search_and_replace(config_file, 'DD', f'{dt_sim.day:02d}')
    search_and_replace(config_file, 'MM', f'{dt_sim.month:02d}')
    search_and_replace(config_file, 'YY', f'{dt_sim.year-2000:02d}')
    search_and_replace(config_file, 'c_Hour', f'{dt_sim.hour:02d}')
    search_and_replace(config_file, 'c_minute', f'{dt_sim.minute:02d}')

    #adding simulation length
    search_and_replace(config_file, 'SIMLENGTH', f'{sim_length:04d}') 

    #  adding spill coordinates - dd for degrees and mm for minutes
    # Latitude
    dd = int(latitude)
    mm = (float(latitude)-dd)*60
    search_and_replace(config_file, 'LATd', f'{dd:02d}')
    search_and_replace(config_file, 'LATm', f'{mm:.3f}')          
    
    # Longitude
    dd = int(longitude)
    mm = (float(longitude)-dd)*60
    search_and_replace(config_file, 'LONd', f'{dd:02d}')
    search_and_replace(config_file, 'LONm', f'{mm:.3f}')

    # spill duration
    if separate_slicks == False:
        search_and_replace(config_file, 'SDUR', f'{spill_duration:04d}')
    else:
        search_and_replace(config_file, 'SDUR', f'{s_rate:04d}')

    # spill volume
    if separate_slicks == False:
        search_and_replace(config_file, 'SRATE', f'{spill_rate:08.2f}')
    else:
        search_and_replace(config_file, 'SRATE', f'{s_volume:08.2f}')

    # oil characteristics
    search_and_replace(config_file, 'APIOT', f'{oil_api}') 

    #number of slicks
    search_and_replace(config_file, 'N_SLICK', f'{number_slick}')

    #slick countour
    if use_slk_contour == True:
        slik = 'YES'

        if separate_slicks == False:
            with open(f'cases/{simname}/xp_files/slick_countour.txt', 'r') as file1:
                content = file1.read()
            with open(config_file, 'a') as file2:
            # Append the contents of the first file to config file
                file2.write(content)
        else:
            with open(f'cases/{simname}/xp_files/slick{s_num+1}/slick_countour.txt', 'r') as file1:
                content = file1.read()
            with open(config_file, 'a') as file2:
            # Append the contents of the first file to config file
                file2.write(content)
    else:
        slik = 'NO'  

    #Writing that will use slick countor
    search_and_replace(config_file, 'SSLICK', f'{slik}')

#Dictionary containing names with the possibility to rename

def rename_netcdf_variables_mdk2(ds):

    variables_to_rename = {'depthu': 'depth', 'depthv': 'depth', 'deptht': 'depth',
                            'nav_lat':'lat','nav_lon':'lon', 'y':'lat','x':'lon',
                            'latitude':'lat','longitude':'lon',
                            'votemper':'thetao','mesh2d_tem1':'thetao',
                            'vozocrtx':'uo','mesh2d_ucx':'uo',
                            'vomecrty':'vo','mesh2d_ucy':'vo',
                            'u10':'U10M','mesh2d_windx':'U10M',
                            'v10':'V10M','mesh2d_windy':'V10M',
                            'time_counter':'time'}
    
    # Rename variables only if they exist in the dataset
    for old_name, new_name in variables_to_rename.items():
        if old_name in ds.variables:
            ds = ds.rename({old_name: new_name})

    return ds