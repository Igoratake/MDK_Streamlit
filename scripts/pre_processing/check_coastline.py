import numpy as np
import os
import sys
import matplotlib.pyplot as plt 
from mpl_toolkits.basemap import Basemap

"""
Created on Tue May  8 14:34:25 2018

Simple program to check whether MEDSLIK-II coastline file has been
generated in accordance.

@author: asepp
"""

# input files

original_medf = sys.argv[1]
outfile = sys.argv[2]

# check .map integrity
# load .map file
cst_data = np.loadtxt(original_medf)
xmin = np.min(cst_data[:,0])
xmax = np.max(cst_data[:,0])
ymin = np.min(cst_data[:,1])
ymax = np.max(cst_data[:,1])

# png format output
plt.figure(figsize=(7, 7))

m = Basemap(llcrnrlon=xmin-.1,llcrnrlat=ymin-.1,\
            urcrnrlon=xmax+.1,urcrnrlat=ymax+.1,\
            rsphere=(6378137.00,6356752.3142),\
            resolution='f',projection='merc',\
            lat_0=(ymin + ymax)/2,\
			lon_0=(xmin + xmax)/2)


xx1 = cst_data[:,0]
xx2 = cst_data[:,2]
yy1 = cst_data[:,1]
yy2 = cst_data[:,3]

x1,y1=m(xx1,yy1)
x2,y2=m(xx2,yy2)

plt.plot(x1,y1,'r.')
plt.plot(x2,y2,'r.')

#for ii in range(0,len(x1)):
#	plt.plot([x1,x2],[y1,y2],'k-')

#input_folder ='/Users/asepp/work/witoilglobal/gofs_tests/cedre_xp/gofs_results/1905/MERCATOR_global_2021_05_19_0120_1905_s2_wdg35/'
m.drawcoastlines(linewidth=.5)
#plt.show()
plt.savefig(outfile)
plt.close('all')
