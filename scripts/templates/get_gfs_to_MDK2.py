from netCDF4 import Dataset
import numpy as np
import os
from datetime import  *
import pdb

def interp_t(iOutputUd, iOutputRefHours, iInputRefHours):
        # prepare storing matrixes
        iShapeO = np.shape(iOutputUd)
        iOutputU = np.zeros((len(iOutputRefHours),iShapeO[1],iShapeO[2]))

        #interpolating
        for ii in range(0,iShapeO[1]):
                for jj in range(0,iShapeO[2]):
                                iOutputU[:,ii,jj]=np.interp(iOutputRefHours,iInputRefHours,iOutputUd[:,ii,jj])

        return iOutputU


def open_gfs(ncfile):
	f = Dataset(ncfile,'r')
	iLatitude=f.variables["latitude"][:]
	iLongitude=f.variables["longitude"][:]#-360.
	iU = f.variables["ugrd10m"][:]
	iV = f.variables["vgrd10m"][:]
	return iLatitude,iLongitude,iU,iV

# Define the directory in which you want to place ur files
iWorkingDirectory= '/scratch/work/lab/XP_NAME/met_files/'
iPprocDirectory='/scratch/work/lab/XP_NAME/met_files/'

# Define start and end data of the pre-processing
iStartDate = date(YYYY1,MM1,DD1).toordinal()
iEndDate = date(YYYY2,MM2,DD2).toordinal()

# Define geo constraints
iLonMin = np.floor(float(lonmin))
iLonMax = np.ceil(float(lonmax))
iLatMin = np.floor(float(latmin))
iLatMax = np.ceil(float(latmax))

if iLonMax < 0:
	iLonMax = 360 + iLonMax
if iLonMin < 0:
	iLonMin = 360 + iLonMin

## Time line
iOutTimeLine=np.arange(0,24)
iInTimeLine=[0,3,6,9,12,15,18,21,24]
d_time = np.array([0,2,4,6])

print('Starting main loop')
for i in range(iStartDate,iEndDate+1,1):

	# Keep track of what you are doing
	iDateI=date.fromordinal(int(i))
	iDateF=date.fromordinal(int(i+1))

	print('Downloading ' +  'GFS_' + iDateI.strftime('%y') + iDateI.strftime('%m') + iDateI.strftime('%d') + '.nc')

	timewindow_string = iDateI.strftime('%Y') + '-' + iDateI.strftime('%m') + '-' + iDateI.strftime('%d') + 'T00:00:00Z):1:(' + iDateF.strftime('%Y') + \
				  	  '-' + iDateF.strftime('%m') + '-' + iDateF.strftime('%d') + 'T00:00:00Z)]'
	spatial_string = '[(' + str(iLatMin) + '):1:(' + str(iLatMax) + ')][(' + str(iLonMin) + '):1:(' + str(iLonMax) + ')]'

	#https://pae-paha.pacioos.hawaii.edu/thredds/dodsC/ncep_global/NCEP_Global_Atmospheric_Model_best.ncd
	request_string = 'https://pae-paha.pacioos.hawaii.edu/erddap/griddap/ncep_global.nc?ugrd10m[(' + timewindow_string + spatial_string + ',vgrd10m[(' + \
					  timewindow_string + spatial_string

	#request_string = 'http://oos.soest.hawaii.edu/erddap/griddap/NCEP_Global_Best.nc?ugrd10m[(' + timewindow_string + spatial_string + ',vgrd10m[(' + \
	#				  timewindow_string + spatial_string
	download_string = 'wget --output-document=' + iWorkingDirectory + 'pre_' + iDateI.strftime('%Y') + iDateI.strftime('%m') + iDateI.strftime('%d') + '.nc "' + request_string + '"'
	eval("os.system('" + download_string + "')")
    	# Temporal interpolation
	ncfile = (iWorkingDirectory + 'pre_' +iDateI.strftime('%Y') + iDateI.strftime('%m') + iDateI.strftime('%d') + '.nc')
	iLatitude,iLongitude,iU,iV = open_gfs(ncfile)

	## Allocation matrixes
	iOutputU = interp_t(iU, iOutTimeLine, iInTimeLine)
	iOutputV = interp_t(iV, iOutTimeLine, iInTimeLine)

	# Masking
	iOutputU=np.where(iOutputU < -100,9999,iOutputU)
	iOutputV=np.where(iOutputV < -100,9999,iOutputV)
	
	# Fixing longitude
	toohigh=np.where(iLongitude>180)
	iLongitude[toohigh]=iLongitude[toohigh]- 360.

	# Fixing latitude issue (MDK files go from N to S)
	iOutputU=np.flip(iOutputU,axis=1)
	iOutputV=np.flip(iOutputV,axis=1)
	iLatitude=np.flip(iLatitude)

	#Generates NC files
	# U component

	sConvertedFilename=iPprocDirectory + iDateI.strftime('%Y') + iDateI.strftime('%m') + iDateI.strftime('%d') + '.nc'
	f = Dataset(sConvertedFilename,"w","NETCDF3_CLASSIC")
	f.history = 'GFS 10m winds -- Adapted to Medslik-II'
	f.createDimension('time',None)
	f.createDimension('lat', len(iLatitude))
	f.createDimension('lon', len(iLongitude))
	#time = f.createVariable('time_counter', 'd', ('time_counter',))
	time = f.createVariable('time', 'd', ('time',))
	# Geo coordinates
	yCoord= f.createVariable('lat', 'd', ('lat',))
	xCoord= f.createVariable('lon', 'd', ('lon',))
	# Zonal velocity component
	uCoord= f.createVariable('U10M', 'd',('time','lat','lon'))
	vCoord= f.createVariable('V10M', 'd',('time','lat','lon'))
	#variable=f.createvariable(what I'm gonna put inside, type (d for double, i for int...), (dimension,))
	time[:] = i + np.arange(1./24,24./24,1./24)
	#Filling the sausage
	yCoord[:]=iLatitude#[::-1]
	xCoord[:]=iLongitude
	#Filling the sausage chap. II
	uCoord[:]=np.flipud(iOutputU)
	vCoord[:]=np.flipud(iOutputV)
	#Adding units
	yCoord.units = 'degrees_north'
	xCoord.units = 'degrees_east'
	xCoord.lon_min = np.min(iLongitude)
	yCoord.lat_min = np.min(iLatitude)
	time.units = 'pythonic days'
	uCoord.units='m*s-1'
	uCoord.missing_value=9999
	vCoord.units='m*s-1'
	vCoord.missing_value=9999
	f.close()

#os.system('rm -f ' + iPprocDirectory + '/pre*.nc')
