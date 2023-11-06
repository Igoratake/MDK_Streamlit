# Plots MEDSLIK-II oil trajectory from nc files
import numpy
import netCDF4
from datetime import  *
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from scipy.interpolate import griddata,interp2d
import numpy as np
import sys
import pdb
import scipy.stats
import os
import re

"""

"""


def center_track(sNcFile, time_index):

    # load ncfile
    ncfile = netCDF4.Dataset(sNcFile,'r')
    # load start position of the spill
    y0 = ncfile.variables['non_evaporative_volume'].initial_position_y
    x0 = ncfile.variables['non_evaporative_volume'].initial_position_x


    # variable extraction
    lats = ncfile.variables['latitude'][time_index,:]
    lons = ncfile.variables['longitude'][time_index,:]

    # extract variables of interest
    particle_status = ncfile.variables['particle_status'][time_index,:]

    # Particle status guide
#        is=0 parcel not released
#        is=1 in the spreading surface slick
#        is=2 on surface but not spreading
#        is=3 dispersed into water column
#        is=-nsg beached on shore segment number nsg

    iNoise=numpy.logical_or(particle_status <= 0, particle_status > 2).nonzero()[0]
    lats = numpy.delete(lats, (iNoise), axis=0)
    lons = numpy.delete(lons, (iNoise), axis=0)

    xc = np.mean(lons)
    yc = np.mean(lats)

    ncfile.close()
    return x0, y0,xc,yc


################################################################################
# USER INPUTS
################################################################################
# set file containing MEDSLIK II netcdf outputs
# set the folder where MEDSLIK outputs are stored
xp_name = input('type the name of the experiment youd like to postprocess (e.g.: "paria_case"): ')
print('List of simulations found in the experiment area')
os.system('ls -d /scratch/work/lab/' + xp_name + '/out_files/MDK_SIM_*')
sim_folder = input('type the name of folder containing simulation results ("MDK_SIM_2021_07_13_1000_myexp"): ')
input_folder = '/scratch/work/lab/' + xp_name + '/out_files/' + sim_folder
oce_folder = input_folder + "/OCE/"
sNcFile = (input_folder + '/spill_properties.nc')

# get sim _ info
with open(input_folder + '/config1.txt') as f:
    lines = f.readlines()

# sim_length
ss = lines[1]
rr = re.search('=(.*)\n',ss)
sim_length = int(lines[1][11:15])
# sim_day
ss = lines[5]
rr = re.search('=(.*)\n',ss)
dd = int(rr.group(1))
# sim_month
ss = lines[6]
rr = re.search('=(.*)\n',ss)
mm = int(rr.group(1))
# sim_year
ss = lines[7]
rr = re.search('=(.*)\n',ss)
yy = rr.group(1)
yy = '20' + yy
year=int(yy)
# sim_hora
ss = lines[8]
rr = re.search('=(.*)\n',ss)
hh = int(rr.group(1))
# sim_minute
ss = lines[9]
rr = re.search('=(.*)\n',ss)
mmin = int(rr.group(1))

# set the date when the simulation started
iStartDay = date(year,mm,dd).toordinal()
iStartHour = hh
iStartMinute = mmin

# set time steps of interest (hours by default -- Python counting starts from 0).
# It may be a single number e.g. [146] or a list of numbers e.g. np.arange(0,15)
# outputs can be every 6h, for instance, by changing the steps in np.arange to 6,
# for instance.
time_line = numpy.arange(0,sim_length,1)
real_time = time_line/24. + (iStartHour+1.)/24. + iStartDay

# set the grid resolution (used to estimate concentrations) in degrees
grid_resolution = 0.15/110

# set output folder where .png files will be placed
output_folder = input_folder
os.system('mkdir ' + output_folder)

################################################################################
# USER INPUTS - OVER!
################################################################################
# From here onwards, the script should do everything pretty much automatic
# bugs/errors are expected and in case you unfortunate enough to find out one,
# feel free to send us comments/corrections.

track_file =(input_folder + '/track_file.txt')
ff = open(track_file, 'w')

csv_file =(input_folder + '/centremass_file.txt')
gg = open(csv_file, 'w')

# plotting loop
cc= 0
for ii in time_line:

    # extract values
    x0, y0, x_mean, y_mean = center_track(sNcFile, ii)
    
    # plot currents - load current fields
    jday = np.floor(real_time[cc])
    hh = np.round((real_time[cc]-jday)*24)
    if hh == 0:
        full_date = date.fromordinal(int(jday-1))
        YY = full_date.strftime('%y')
        mm = full_date.strftime('%m')
        dd = full_date.strftime('%d')
        hh = 24
    else:
        full_date = date.fromordinal(int(jday))
        YY = full_date.strftime('%y')
        mm = full_date.strftime('%m')
        dd = full_date.strftime('%d')

    #oce_fields = (oce_folder + '/merc' + YY + mm + dd + '%02d' % (hh) + '.mrc')
    #xc,yc,uc,vc = mdkcurrents(oce_fields,'surf') #surf, 10, 30 or 120

    stringa = ('20' + YY + mm + dd + ' ' + '%02d' % (hh) + ':00 UTC   lon = ' + '%06.3f' % (x_mean) + '    lat = ' + '%06.3f' % (y_mean) + '\n')
    ff.write(stringa)
    stringa = ('20' + YY + mm + dd + ';' + '%02d' % (hh) + ';00;' + '%06.3f' % (x_mean) + ';' + '%06.3f' % (y_mean) + '\n')
    gg.write(stringa)

    print ("Spill GM location = " + str(x_mean) + "W ::::: " + str(y_mean) + "N ")
    cc = cc + 1
    
ff.close()
