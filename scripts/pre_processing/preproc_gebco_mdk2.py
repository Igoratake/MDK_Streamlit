import argparse
import netCDF4
import numpy as np
import os
import xarray as xr

# crop GEBCO
def interp_gebco(gebco,grid):

	grid = xr.open_dataset(grid)
	gebco = xr.open_dataset(gebco)

	try:
		grid = grid.rename({'nav_lat':'lat','nav_lon':'lon'})
	except:
		pass

	# interpolation on medslik grid
	med = gebco.interp(lon=grid.lon.values.tolist(),lat=grid.lat.values.tolist())
	#converting from begative depths to positive
	med['elevation'] = med.elevation *-1
	#filling nan to -9999 as expected by medslik
	med = med.fillna(9999)	

	# Convert bathymetry to MDK-II
	mdk_z=[]

	llat,llon = len(med.lat),len(med.lon)
	
	for i in reversed(range(0,llat)):
		for j in range(0,llon):
			rec = med.isel(lat=i,lon=j)
			mdk_z.append(rec.elevation.values.max())

	mdk_z = np.array(mdk_z)
	land_mask = np.where(mdk_z <= 0)
	mdk_z[land_mask]=9999

	return grid.lon.values, grid.lat.values, mdk_z, llat, llon

################################################################################
# USER INPUTS
################################################################################

parser = argparse.ArgumentParser(description='Generate bathymetry fields at ocean current fields grid')
parser.add_argument('gebco',help='full path to your 08deg res GEBCO bathymetry')
parser.add_argument('input',help='full path to a MDK_ocean_YYMMDD_X.nc file from where interpolation grid will be taken from')
parser.add_argument('output_dir', help='Output directory where files will be saved')
args = parser.parse_args()
# set path for your original gebco netCDF file
gebco_filename = args.gebco 

# define where outputs will be placed (MEDSLIK-adapted bathymetry files)
output_dir= args.output_dir 

# the bathymetry fields will be interpolated to your hydrodynamic grid
oce_filename = args.input 

################################################################################
# USER INPUTS - OVER!
################################################################################
# From here onwards, the script should do everything pretty much automatic
# bugs/errors are expected and, in case you do find one,
# feel free to send us comments/corrections.

# extract bathymetry
mdk_x, mdk_y, mdk_z, llat, llon = interp_gebco(gebco_filename,oce_filename)

# write .bath file
BathFile=open(output_dir + "dtm.bath", "w")
BathFile.write("MEDSLIK-II compatible bathymetry file. Degraded resolution based on GEBCO 30''\n")
BathFile.write("%-7.4f %-7.4f %-7.4f %-7.4f \n" % (np.min(mdk_x),np.max(mdk_x),np.min(mdk_y),np.max(mdk_y)))
BathFile.write("%d %d \n" % (llon,llat))
np.savetxt(BathFile,mdk_z,fmt="%04.0f")
BathFile.close()
