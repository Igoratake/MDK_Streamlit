#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import numpy as np
import os
import sys
#os.environ['PROJ_LIB'] = '/home/augustosepp/miniconda2/pkgs/proj4-5.2.0-he6710b0_1/share/proj/'
import matplotlib.pyplot as plt#; plt.switch_backend('agg')
from mpl_toolkits.basemap import Basemap

"""
Created on Tue May  8 14:34:25 2018

Simple program to check whether MEDSLIK-II bathymetry file has been
generated in accordance.

@author: asepp
"""

# input files

original_medf = sys.argv[1]
outfile = sys.argv[2]

# check .bath integrity
# load .bath file
bnc_file = open(original_medf, "r")
bnc_data = bnc_file.readlines()

# extract boundaries
header_1 = bnc_data[1].split()
xmin = float(header_1[0])
xmax = float(header_1[1])
ymin = float(header_1[2])
ymax = float(header_1[3])

# number of elements in .bath matrix
header_2 = bnc_data[2].split()
c_1 = int(header_2[0])
r_1 = int(header_2[1])

# extract bathymetry values
bnc_control = []
for i in bnc_data[3::]:
    sdepth=i.split()
    bnc_control.append(float(sdepth[0]))

# regrid data
del_x = (xmax-xmin)/(c_1-1)
del_y = (ymax-ymin)/(r_1-1)
lon_ck=np.arange(xmin,xmax+del_x/2,del_x)
lat_ck=np.arange(ymin,ymax+del_y/2,del_y)

opa = np.zeros((r_1,c_1))
xM = np.zeros((r_1,c_1))
yM = np.zeros((r_1,c_1))

index=0
for i in range(0,len(lat_ck)):
    for j in range(0,len(lon_ck)):
        opa[i,j] = bnc_control[index]
        xM[i,j]=lon_ck[j]
        yM[i,j]=lat_ck[i]
        index=index+1

yM = np.flipud(yM)

plot_opa = np.copy(opa)
plot_opa[plot_opa==9999]=-9999

# png format output
plt.figure(figsize=(7, 7))

m = Basemap(llcrnrlon=xmin,llcrnrlat=ymin,\
            urcrnrlon=xmax,urcrnrlat=ymax,\
            rsphere=(6378137.00,6356752.3142),\
            resolution='i',projection='merc',\
            lat_0=(ymin + ymax)/2,\
			lon_0=(xmin + xmax)/2)

x,y=m(xM,yM)
m.drawcoastlines(linewidth=0.5)
m.pcolor(x,y,plot_opa,vmin=0,vmax=1000)
#m.plot(x_t,y_t,'w+')
plt.colorbar()
plt.savefig(outfile)
plt.close('all')
