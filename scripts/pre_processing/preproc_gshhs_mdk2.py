#!/usr/bin/python
# pre_processor MEDSLIK - II

# Developed for coastline extraction from gshhs full resolution.
# It will extract coastline files for whichever part of the globe you
# wish and make it compatible with MEDSLIK-II.

import numpy as np
import argparse
import xarray as xr
import geopandas as gpd
from shapely.geometry import box
import os

def generate_coastline_gshhs(gshhs,grid,output_dir):

	grid = xr.open_dataset(grid)

	try:
		grid = grid.rename({'nav_lat':'lat','nav_lon':'lon'})
	except:
		pass

	# 1 degree buffer to collect more coastline
	buffer = 1
	#defining minimum and maximum of coordinates box search 
	xmin = grid.lon.min() - buffer
	xmax = grid.lon.max() + buffer
	ymin = grid.lat.min() - buffer
	ymax = grid.lat.max() + buffer

	shp = gpd.read_file(gshhs)

	# Cropping to a smaller area
	shp = shp.cx[xmin:xmax, ymin:ymax]

	#shp with linestring instead of polygons
	shp['geometry'] = shp.geometry.boundary

	# Cropping the selected linestrings to the same bounding box
	shp = shp.clip_by_rect(xmin.values.max(),ymin.values.max(), xmax.values.max(),ymax.values.max())

	# Removing empty geometries
	shp = shp[~shp.is_empty]

	#Transforming it back again to geodataframe
	shp = gpd.GeoDataFrame(geometry = shp)

	#removing any multiline strings left on the shapefile
	shp = shp.explode(index_parts=True)

	# writes the first line of the .map file. It should contain the # of "isles"
	CoastFile=open(output_file,'w')
	CoastFile.write("%-4.0f \n" % (len(shp)))
	iTargetSites=[]
	iTargetSite=np.array([0.,0.,0.,0.])

	for i,polygon in shp.iterrows():

		# extracts the island
		pol = polygon.geometry

		# Extract the exterior coordinates of the polygon
		# exterior_coords = list(pol.exterior.coords)
		exterior_coords = list(pol.coords)
		
		#prints the length of the island
		CoastFile.write("%-4.0f %1.0f \n" % (len(exterior_coords),0))
		#prints data related to the island
		for segment in exterior_coords:
			CoastFile.write("%-8.5f %-6.5f \n" % (segment[0], segment[1]))

		for i in range(0,len(exterior_coords)-1):
						iTargetSite[0]=exterior_coords[i][0]
						iTargetSite[1]=exterior_coords[i][1]
						iTargetSite[2]=exterior_coords[i+1][0]
						iTargetSite[3]=exterior_coords[i+1][1]
						iTargetSites.append(list(iTargetSite))

	CoastFile.close()
	np.savetxt(output_file[:-3] + 'txt', np.array(iTargetSites))


################################################################################
# USER INPUTS
################################################################################

parser = argparse.ArgumentParser(description='Generate bathymetry fields at ocean current fields grid')
parser.add_argument('gshhs',help='full path to your GSHHS coastline shapefile')
parser.add_argument('input',help='full path to a MDK_ocean_YYMMDD_X.nc file from where interpolation grid will be taken from')
parser.add_argument('output_dir', help='Output directory where files will be saved')
args = parser.parse_args()

# set path for your original gebco netCDF file
gshhs_filename = args.gshhs 

# define where outputs will be placed (MEDSLIK-adapted nc files)
output_dir= args.output_dir 

# the bathymetry fields will be interpolated to your hydrodynamic grid
# therefore, let us know where you've placed your current files
oce_filename = args.input 

################################################################################
# USER INPUTS - OVER!
################################################################################
# From here onwards, the script should do everything pretty much automatic
# bugs/errors are expected and, in case you do find one,
# feel free to send us comments/corrections.

# extract coastline
output_file = output_dir + "/dtm.map"
generate_coastline_gshhs(gshhs_filename,oce_filename,output_file)
