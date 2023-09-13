import numpy as np
import pdb
from datetime import  *
import os
import cdsapi

def get_era5(xmin,xmax,ymin,ymax,ii,out_folder):
  server = cdsapi.Client()
  dDate=date.fromordinal(int(ii))
  fDate=date.fromordinal(int(ii+1))
  date_string = dDate.strftime('%Y') + '-' + dDate.strftime('%m') + '-' + dDate.strftime('%d') + '/to/' + \
  dDate.strftime('%Y') + '-' + dDate.strftime('%m') + '-' + dDate.strftime('%d')
  print date_string
  location_string = str(ymax) + '/' + str(xmin) + '/' + str(ymin) + '/' + str(xmax)
  print location_string
  target_string = out_folder + '/pre_' + dDate.strftime('%Y') + dDate.strftime('%m') + dDate.strftime('%d') + '.nc'
  print target_string
  
  server.retrieve(
  'reanalysis-era5-single-levels',
  {
      'product_type': 'reanalysis',
      'format': 'netcdf',
      'variable': [
          '10m_u_component_of_wind', '10m_v_component_of_wind',
      ],
      'year': dDate.strftime('%Y'),
      'month': dDate.strftime('%m'),
      'day': dDate.strftime('%d'),
      'time': [
          '00:00', '01:00', '02:00',
          '03:00', '04:00', '05:00',
          '06:00', '07:00', '08:00',
          '09:00', '10:00', '11:00',
          '12:00', '13:00', '14:00',
          '15:00', '16:00', '17:00',
          '18:00', '19:00', '20:00',
          '21:00', '22:00', '23:00',
      ],
      'area': [
          ymax, xmin, ymin,
          xmax,
      ],
  },
  target_string)

# Script to download daily ERA-Interim files
# user info
xp_name = input('Name your experiment (e.g. "paria_case"): ')
time_string = input('Set spill date dd/mm/yy (e.g., "26/12/20" ): ')
hour_string = input('Set spill time (e.g., "01:22"): ')
sim_length = input('Set the length of your simulation (in h): ')

os.system('mkdir /scratch/work/lab/' + xp_name)
os.system('mkdir /scratch/work/lab/' + xp_name + '/met_files/')

out_folder= '/scratch/work/lab/' + xp_name + '/met_files/' 

#Set your area of interest
print('Set bounding box (in decimal degrees)')
xmin = np.floor(float(input('lon_min: ')))
xmax = np.ceil(float(input('lon_max: ')))
ymin = np.floor(float(input('lat_min: ')))
ymax = np.ceil(float(input('lat_max: ')))

# collect date
spill_year = int(time_string[6::])
spill_month = int(time_string[3:5])
spill_day = int(time_string[0:2])
spill_hour = int(hour_string[0:2])
spill_min = int(hour_string[3:5])

spill_date = date(2000+int(spill_year),int(spill_month),int(spill_day)).toordinal()
iStartDate = spill_date 

sim_length = int(sim_length)

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

iEndDate = iStartDate + dday

# Start download
for ii in range(iStartDate,iEndDate+2):
    print "Downloading file for: "
    dDate=date.fromordinal(int(ii))
    fDate=date.fromordinal(int(ii+1))
    file1 = 'pre_' + dDate.strftime('%Y') + dDate.strftime('%m') + dDate.strftime('%d') + '.nc'
    file2 = 'pre_' + fDate.strftime('%Y') + fDate.strftime('%m') + fDate.strftime('%d') + '.nc'

    get_era5(xmin,xmax,ymin,ymax,ii,out_folder)
    get_era5(xmin,xmax,ymin,ymax,ii+1,out_folder)

    os.system('cdo -b F64 mergetime ' + out_folder + file1 + ' ' + out_folder + file2 + ' ' + out_folder + 'output.nc')

    string1 = dDate.strftime('%Y') + '-' + dDate.strftime('%m') + '-' + dDate.strftime('%d') + 'T01:00:00'
    string2 = fDate.strftime('%Y') + '-' + fDate.strftime('%m') + '-' + fDate.strftime('%d') + 'T00:00:00'

    os.system('cdo seldate,' + string1 + ',' + string2 + ' ' + out_folder + '/output.nc ' + out_folder + '/' + file1[4::])
    os.system('ncrename -O -d longitude,lon -d latitude,lat -v longitude,lon -v latitude,lat -v u10,U10M -v v10,V10M ' + out_folder + '/' + file1[4::])

    os.system('rm ' + out_folder + '/output.nc')





