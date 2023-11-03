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

# Functions outside this script
from functions.medslik_utils import *
import functions.download_mercator_parser
import functions.download_era5_parser
from scripts import *


# ================= MEDSLIK MODEL INPUTS ================= #
simname        = 'test2'      ### Simulation name - format (string)
sim_date       = '15/07/2023' ### Simulation start day  - format DD/MM/YYYY (string)
sim_hour       = '07:00'      ### Simulation start hour - format HH:mm (string)
longitude      = 18.00        ### Longitude of Simulation spill location - format Decimal degrees (float)
latitude       = 41.00        ### Latitude of Simulation spill  - format Decimal degrees (float)
delta          = 0.5          ### Standard delta to collect an area around lat and discharge point - format degrees (float)
sim_lenght     = 48           ### Length of the simulation - format hours (int)
spill_duration = 0            ### Duration of the spill - format hours (int)
oil_api        = 28           ### Oil API - format (float)
oil_volume     = 5            ### Volume of oil in tons - format (float) 
use_satellite  = False        ### Usage of Satellite imagery to model multiple slicks - True/False

# Obtaining spill rate from oil volume and spill duration
if spill_duration != 0:
    spill_rate = oil_volume/spill_duration
else:
    spill_duration = oil_volume    

# ================= DOWNLOAD OPTIONS ================= #
down = 'global'               ### Download data from global copernicus or local models - format(string) global/local
cop_username = None           ### Username to access copernicus datasets. Can be replaced here for practicity. - format None or string
cop_password = None           ### Password to access copernicus datasets. Can be replaced here for practicity. - format None or string
era_api_key  = None           ### API key to access era5 datasets. Can be replaced here for practicity. - format None or string



'''
These options are used for choosing which datasets to use when downloading data from external sources

'''

if __name__ == '__main__':


    ############# INITIAL CHECKING AND DOWNLOAD #############
    # Check if coordinates are on sea
    sea =  check_land(longitude,latitude)    

    if sea==0:
        raise ValueError('Coordinates values are on land. Try another location')
    
    if 30.37 < float(latitude) < 45.7 and -17.25 < float(longitude) < 35.9 and down=='global':
        print('Coordinates lie within Mediterranean Sea\n Your data is set to global.\n'
                'Press y to continue with global or n to change to Med Sea Data')     
        
        while True:
            check = input().lower()
            if check == 'n':
                down = 'local'
                break
            elif check =='y':
                break
            else:
                print('wrong input. Try again')
    
    # Download area
    print (f'Download coordinates are:'
           f'Min lat = {(latitude-delta):.2f} Max lat = {(latitude+delta):.2f}'
           f'Min lon = {(longitude+delta):.2f} Max lon = {(longitude+delta):.2f}')
    
    # Simulation dates
    dt = validate_date(sim_date)

    if isinstance(dt,str):
        raise ValueError('Wrong date format.')

    dtini = dt - datetime.timedelta(days=1)
    if (datetime.datetime.today()-dt).days <10:
        print('ERA5 data might not be available in the selected date')
        
    inidate = f'{dtini.year}-{str(dtini.month).zfill(2)}-{str(dtini.day).zfill(2)}'
    inidate2 = inidate + 'T00:00:00Z'         

    dtend = dt + datetime.timedelta(days= (sim_lenght/24) + 2) 

    enddate = f'{dtend.year}-{str(dtend.month).zfill(2)}-{str(dtend.day).zfill(2)}'
    enddate2 = enddate + 'T00:00:00Z'

    if cop_username == None:
        print('Please input your copernicus user name')
        cop_username = input()
    
    if cop_password == None:
        print('Please input your copernicus password')
        cop_password = input()
    

    ### Mercator download ###
    output_path = 'data/MERCATOR/'                            
    # Create a thread to run the external script in the background
    script_thread = subprocess.run([f'{sys.executable}', 'functions/download_mercator_parser.py',
                                    inidate2,enddate2,'0','130',
                                    str(latitude),str(longitude),str(delta),
                                    down,output_path,
                                    cop_username,cop_password]) 
    
    ### ERA5 download ###
    #Met Data
    output_path = 'data/ERA5/'

    # Create a thread to run the external script in the background
    script_thread = subprocess.run([f'{sys.executable}','functions/download_era5_parser.py',
                                    str(latitude),str(longitude),str(delta),
                                    inidate,enddate,output_path])
    
    ############# PRE PROCESSING DATA AND FILES #############

    simdir = 'cases/'
    #Creating all directories    
    subprocess.run(f'mkdir {simdir}{simname}/',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/oce_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/met_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/bnc_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/xp_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/out_files',shell=True)
    subprocess.run(f'mkdir {simdir}{simname}/detections',shell=True)   

    list_of_files = glob('data/MERCATOR/*.nc')
    selected_file = max(list_of_files, key=os.path.getctime)

    if '_med_' in selected_file:
        lon = 'lon'
        lat = 'lat'

    else:
        lon = 'longitude'
        lat = 'latitude'

    ds = xr.open_dataset(selected_file)  

    if 'med' not in selected_file:
        try:
            ds = ds.rename({'latitude':'lat','longitude':'lon'})
        except:
            pass      

    min_lat,max_lat = (ds.lat.values.min(),ds.lat.values.max())
    min_lon,max_lon = (ds.lon.values.min(),ds.lon.values.max())

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
    subprocess.run([f'{sys.executable}', 'scripts/pre_processing/preproc_gebco_mdk2.py', 
                    'data/gebco/GEBCO_2023.nc',
                    grid_string, f'{simdir}{simname}/bnc_files/'])

    # gshhs in intermediate resolution
    subprocess.run([f'{sys.executable}', 'scripts/pre_processing/preproc_gshhs_mdk2.py', 
                    'data/gshhs/gshhg-shp-2.3.7/GSHHS_shp/i/GSHHS_i_L1.shp',
                    grid_string, f'{simdir}{simname}/bnc_files/'])

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
    subprocess.run([f"{config} sed -i s/SIMLENGTH/{sim_lenght:04d}/ {config_file}"],shell=True)       

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
    subprocess.run([f"{config} sed -i s/SDUR/{spill_duration:04d}/ {config_file}"],shell=True)

    # spill volume
    subprocess.run([f"{config} sed -i s/SRATE/{oil_volume:08.2f}/ {config_file}"],shell=True)

    # oil characteristics
    subprocess.run([f"{config} sed -i s/APIOT/{oil_api}/ {config_file}"],shell=True)

    # copy METOCEAN files to MEDSLIK-II installation
    subprocess.run([f'cp {simdir}{simname}/oce_files/* MEDSLIK_II_2.02/METOCE_INP/PREPROC/OCE/'],shell=True)
    subprocess.run([f'cp {simdir}{simname}/oce_files/* MEDSLIK_II_2.02/RUN/TEMP/OCE/'],shell=True)

    subprocess.run([f'cp {simdir}{simname}/met_files/* MEDSLIK_II_2.02/METOCE_INP/PREPROC/MET/'],shell=True)
    subprocess.run([f'cp {simdir}{simname}/met_files/* MEDSLIK_II_2.02/RUN/TEMP/MET/'],shell=True)
    # copy bnc files
    subprocess.run([f'cp {simdir}{simname}/bnc_files/* MEDSLIK_II_2.02/DTM_INP/'],shell=True)
    # copy Extract and config files
    subprocess.run([f'cp {simdir}{simname}/xp_files/Extract_II.for MEDSLIK_II_2.02/RUN/MODEL_SRC/'],shell=True)
    subprocess.run([f'cp {simdir}{simname}/xp_files/medslik_II.for MEDSLIK_II_2.02/RUN/MODEL_SRC/'],shell=True)
    subprocess.run([f'cp {simdir}{simname}/xp_files/config1.txt MEDSLIK_II_2.02/RUN/'],shell=True)

    # Compile and start running
    subprocess.run([f'cd MEDSLIK_II_2.02/RUN/; sh MODEL_SRC/compile.sh; ./RUN.sh'],shell=True,check=True)