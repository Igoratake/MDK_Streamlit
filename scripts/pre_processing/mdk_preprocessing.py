#my first medslik experiment
import numpy as np
from datetime import *
import netCDF4
import myots as myots
import sys
import os
import pdb

def oce_grid(filename):
	fOCM = netCDF4.Dataset(filename)
	x_mod = fOCM.variables['nav_lon'][:]
	y_mod = fOCM.variables['nav_lat'][:]
	return x_mod, y_mod
    
def wind_grid(filename):
	fOCM = netCDF4.Dataset(filename)
	x_mod = fOCM.variables['lon'][:]
	y_mod = fOCM.variables['lat'][:]
	return x_mod, y_mod

'''
this script generates all the necessary input files for a medslik_ii experiment
'''    
# experiment name
xp_name = input('Name your experiment (e.g. "paria_case"): ')

# working directory
working_dir = '/scratch/work/lab/'

# experiment folder
xp_folder = working_dir + xp_name
myots.xp_environ(working_dir,xp_name)

# period of interest
time_string = input('Set spill date dd/mm/yy (e.g., "26/12/20" ): ')
hour_string = input('Set spill time (e.g., "01:22"): ')
spill_year = int(time_string[6::])
spill_month = int(time_string[3:5])
spill_day = int(time_string[0:2])
spill_hour = int(hour_string[0:2])
spill_min = int(hour_string[3:5])

spill_date = date(2000+int(spill_year),int(spill_month),int(spill_day)).toordinal()
iStartDate = spill_date 
sim_length = input('Set the length of your simulation (in h): ')
sim_length = int(sim_length)

# members setup
oil_API = input('Set the spilled oil API (e.g. 28): ')
oil_API = '%02d' % (oil_API)
spill_duration = input('Set the duration of the spill (0 for instanteous spill or the number of hours of continuous release): ')
spill_duration = '%04d' % (spill_duration)
spill_volume = input('Set the spilled volume (in tons): ')
spill_volume = '%08.2f' % (spill_volume)
sim_length_string = '%04d' % (sim_length)

extra_count=0
if spill_min>0:
	hour_= int(spill_hour) + 1
else:
	hour_=int(spill_hour)

my_int = sim_length/24*24
rem_hours = sim_length - my_int
late_cases = rem_hours+hour_
num_days = sim_length/24

if np.logical_and(num_days>0,late_cases>=0):
	extra_count=extra_count+1
	
elif num_days==0:
	extra_count=extra_count+1

elif np.logical_and(late_cases>=24):
	extra_count=extra_count+1

dday=num_days + extra_count

# is it a point source or should we start from a polygon?
polycheck = input('Would you like to start ur simulation from a polygon ("y"/"n")? ')

if polycheck == 'y':
    # setting up the area of interest
    shp_string = input('Now, give the fullpath of where the spill shp is found: ')
    sW,sE,sS,sN,n_slicks,lon_mean,lat_mean = myots.get_shp2mdk_parts(shp_string,xp_folder)
    
elif polycheck == 'n':
    lon_mean = input('Longitude coordinates (decimal) for point source then: ')
    lat_mean = input('Latitude coordinates (decimal) for point source then: ')
    lon_mean = float(lon_mean)
    lat_mean = float(lat_mean)

forcing = input('Selected forecasting scale ("regional" or "global"). Regional scale simulations available only inside the Mediterranean Basin. : ')

# maximum spill displacement is computed assuming an average
# current speed of 2m/s

max_ds = ((sim_length*60*60)*0.001)/110.


xW= lon_mean - max_ds
xE= lon_mean + max_ds
yS= lat_mean - max_ds
yN= lat_mean + max_ds

grid_corners = np.array([xW,xE,yS,yN])

print('*********************************')
print('...generating runlist...')
print('*********************************')

if polycheck=='y':
    myots.config1_gen_polysource(working_dir, xp_name, oil_API, spill_duration,\
        spill_volume, time_string, hour_string, sim_length_string, str(n_slicks),lon_mean,lat_mean)
elif polycheck=='n':
    myots.config1_gen_pointsource(working_dir, xp_name, oil_API, spill_duration,\
        spill_volume, time_string, hour_string, sim_length_string,lon_mean,lat_mean)
    
# download and transform current field
stime1 = date.fromordinal(iStartDate)
stime2 = date.fromordinal(iStartDate + int(dday))

print('*********************************')
print('...downloading meteo-oceanographic forcing...')
print('*********************************')

if forcing=='regional':
	myots.medfs_currfile_gen(xp_name,xp_folder,stime1.strftime('%Y'),stime1.strftime('%m'),stime1.strftime('%d'),dday,str(xW),str(xE),str(yS),str(yN))    
elif forcing=='global':
	myots.mercator_currfile_gen(xp_name,xp_folder,stime1.strftime('%Y'),stime1.strftime('%m'),stime1.strftime('%d'),dday,str(xW),str(xE),str(yS),str(yN))

os.system("bash /scratch/work/lab/" + xp_name + "/currents_download.sh")

# download and transform wind fields
myots.mdk_windfile_gen(xp_name, xp_folder,stime1.strftime('%Y'),stime1.strftime('%m'),stime1.strftime('%d'),stime2.strftime('%Y'),stime2.strftime('%m'),stime2.strftime('%d'),str(xW),str(xE),str(yS),str(yN))
execfile("/scratch/work/lab/" + xp_name + "/download_era_custom.py")
os.system('rm -f ' + xp_folder + '/met_files/pre*.nc')

# generate coastline and bathymetry
print('*********************************')
print('...generating coastline and bathymetry fields...')
print('*********************************')

myots.bnc_files(xp_name,xp_folder)
execfile("/scratch/work/lab/" + xp_name + "/generate_coastline_custom.py")
execfile("/scratch/work/lab/" + xp_name + "/generate_bathymetry_custom.py")

# open an ocean forecast file
oce_dir = xp_folder + '/oce_files/'
oce_filename = (oce_dir + '/' + os.listdir(oce_dir)[0])
x_oce, y_oce = oce_grid(oce_filename)

wind_dir = xp_folder + '/met_files/'
wind_filename = (wind_dir + '/' + os.listdir(wind_dir)[0])
x_wind, y_wind = wind_grid(wind_filename)
# generate Extract file
print('*********************************')
print('...generating nc extracting file...')
print('*********************************')
myots.mdk_extract_gen(working_dir, xp_name, len(x_oce), len(y_oce),len(x_wind),len(y_wind))

# clean up experiment folder
os.system('rm -f ' + xp_folder + '/xp_files/config1_template*.txt')

print('*********************************')
print('...launching MEDSLIK - II ...')
print('*********************************')
# copy METOCEAN files to MEDSLIK-II installation
os.system('ln -sf ' + oce_dir + '/MDK*.nc /scratch/work/MEDSLIK_II_2.02/METOCE_INP/PREPROC/OCE/')
os.system('ln -sf ' + wind_dir + '/2*.nc /scratch/work/MEDSLIK_II_2.02/METOCE_INP/PREPROC/MET/')
# copy bnc files
os.system('ln -sf ' + xp_folder + '/bnc_files/dtm*.* /scratch/work/MEDSLIK_II_2.02/DTM_INP/')
# copy Extract and config files
os.system('ln -sf ' + xp_folder + '/xp_files/Extract_II.for /scratch/work/MEDSLIK_II_2.02/RUN/MODEL_SRC/')
os.system('ln -sf ' + xp_folder + '/xp_files/config1.txt /scratch/work/MEDSLIK_II_2.02/RUN/')
os.system('cd /scratch/work/MEDSLIK_II_2.02/RUN/;sh MODEL_SRC/compile.sh;./RUN.sh')

date_string = ( '%02d' % (spill_year) + '_' + '%02d' % (spill_month)  + '_' + '%02d' % (spill_day)  + '_' + '%02d' % (spill_hour)  + '%02d' % (spill_min)) 
os.system('mv /scratch/work/MEDSLIK_II_2.02/OUT/MDK_SIM_20' + date_string + '_' + xp_name +' ' + xp_folder + '/out_files/')

print('*********************************')
print("DONE. YOU SHOULD FIND THE SIMULATION RESULTS AT " + xp_folder + '/out_files/')
print("PROCEED TO POSTPROCESSING")
print('*********************************')

print("DONE. YOU SHOULD FIND THE SIMULATION RESULTS AT " + xp_folder + '/out_files/')
print("PROCEED TO POSTPROCESSING")
