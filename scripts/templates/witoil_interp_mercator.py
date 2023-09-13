#!/usr/bin/python

from netCDF4 import Dataset
import numpy as np
import pdb
from datetime import  *
import sys

def load_oceanfields(sFileName):
	fM=Dataset(sFileName,"r")
	iLatitude=fM.variables["nav_lat"][:]
	iLongitude=fM.variables["nav_lon"][:]

	if sFileName[-7:-6]=='T':
		iVar=fM.variables["votemper"][:] # water temperature in deg C
	elif sFileName[-7:-6]=='U':
		iVar=fM.variables["vozocrtx"][:] # u component of water velocity in m/s
	elif sFileName[-7:-6]=='V':
		iVar=fM.variables["vomecrty"][:] # v component
	else:
		print('Could not detect ocean field. Have you changed the file naming scheme?')
	iDepth=fM.variables["depth"][:]  # in m
	iTime=fM.variables["time_counter"][:]  # hours since 1950-01-01 00:00:00
	fM.close()

	return iLongitude,iLatitude,iVar,iTime,iDepth

# organizing your inputs
date_input = sys.argv[1]
input_file = sys.argv[2]
output_file = sys.argv[3]

# split ur date string
YYYY = date_input[0:4]
MM = date_input[5:7]
DD = date_input[8:10]

# this is your current date in hours since 1950-01-01 00:00:00
currdate = (date(int(YYYY),int(MM),int(DD)).toordinal() - date(1950,1,1).toordinal())*24

# your output file will cover hourly data from:
start_date = currdate + 1 # MDK files cover from 01:00AM

# till
end_date = currdate + 24 # till 24:00

# double check whether your input files is appropriate for a nice interpolation
x,y,var,time_input,depth = load_oceanfields(input_file)
if np.logical_or(time_input[0] > start_date, time_input[-1] < end_date):
	print('Ocean fields do not cover the period of interest.')
	sys.exit()

# state that your files will have
lowres_timeline = time_input
highres_timeline = np.linspace(start_date,end_date,24)


out_field = np.zeros((len(highres_timeline),len(depth),len(y),len(x)))-32767.0

# name variables in output file
if input_file[-7:-6]=='T':
	var_name = "votemper"
	var_units = 'deg C'
elif input_file[-7:-6]=='U':
	var_name = "vozocrtx"
	var_units = 'm/s'
elif input_file[-7:-6]=='V':
	var_name = "vomecrty"
	var_units = 'm/s'
else:
	print('Could not detect ocean field. Have you changed the file naming scheme?')
	sys.exit()

#interpolating
for ii in range(0,len(y)):
	for jj in range(0,len(x)):
		for dd in range(0,len(depth)):

			if var[0,dd,ii,jj]>-20:
				out_field[:,dd,ii,jj]=np.interp(highres_timeline,lowres_timeline,var[:,dd,ii,jj])
				#pdb.set_trace()
				#Extrapolating data
				if (dd!=0 and any(out_field[:,dd,ii,jj]<-3) and all(out_field[:,dd-1,ii,jj]>-3)):
					out_field[:,dd,ii,jj]=out_field[:,dd-1,ii,jj]

	#----------------------------------------------------------------------------
	# Masking

out_field[np.where(out_field < -100)] = 9999

#Generates NC files

# U component
f = Dataset(output_file, "w", "NETCDF3_CLASSIC")
f.history = 'MERCATOR Forecast - MyOcean -- Adapted to Medslik-II'
f.createDimension('time_counter',None)
f.createDimension('y', len(y))
f.createDimension('x', len(x))
f.createDimension('depth',len(depth))
time = f.createVariable('time_counter', 'd', ('time_counter',))
# Geo coordinates
yCoord= f.createVariable('nav_lat', 'd', ('y'))
xCoord= f.createVariable('nav_lon', 'd', ('x'))
# Zonal velocity component
uCoord= f.createVariable(var_name, 'd',('time_counter','depth','y','x'))
#variable=f.createvariable(what I'm gonna put inside, type (d for double, i for int...), (dimension,))
time[:] = highres_timeline
#Filling the sausage
yCoord[:]=y
xCoord[:]=x
#Filling the sausage chap. II
uCoord[:]=out_field
#Adding units
yCoord.units = 'degrees_north'
xCoord.units = 'degrees_east'
time.units = 'hours since 1950-01-01 00:00'
uCoord.units=var_units
uCoord.missing_value=9999
f.close()
