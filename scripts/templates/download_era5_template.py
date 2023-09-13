import numpy as np
import pdb
from datetime import  *
import os
import cdsapi

def get_era5(xmin,xmax,ymin,ymax,ii,out_folder):
  server = cdsapi.Client()
  dDate=date.fromordinal(int(ii))
  fDate=date.fromordinal(int(ii+1))
  target_string = out_folder + 'pre_' + dDate.strftime('%Y') + dDate.strftime('%m') + dDate.strftime('%d') + '.nc'
  
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

#Set your area of interest
xmin = np.floor(np.float(lonmin))
xmax = np.ceil(np.float(lonmax))
ymin = np.floor(np.float(latmin))
ymax = np.ceil(np.float(latmax))

# Set your period of interest
iStartDate = date(YYYY1,MM1,DD1).toordinal()
iEndDate = date(YYYY2,MM2,DD2).toordinal()

# Define output folder
out_folder = '/scratch/work/lab/XP_NAME/met_files/'

# Start download
for ii in range(iStartDate,iEndDate+2):

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


