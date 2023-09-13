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

"""
Application:
    This script has been developed to plot oil concentrations found at the
    sea surface based on MEDSLIK II outputs. The outputs are png figures.
"""

def generate_mask(filename):

    bnc_file = open(filename, "r")
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
    opa[opa==9999]=0.
    #opa[opa<10]=1.
    opa[opa!=0]=1.

    return xM,yM,opa


def mdkcurrents(file_name,layer):

    rawfields = np.loadtxt(file_name,skiprows=5)
    y = rawfields[:,0]
    x = rawfields[:,1]

    ftxt=open(file_name,'r')
    sData=ftxt.readlines()
    grid_info = sData[2].split()

    xmin=float(grid_info[0])
    xmax=float(grid_info[1])
    ymin=float(grid_info[2])
    ymax=float(grid_info[3])

    dy = (ymax-ymin)/(float(grid_info[5])-1)
    dx = (xmax-xmin)/(float(grid_info[4])-1)

    x_o = np.arange(xmin,xmax+dx/2,dx)
    y_o = np.arange(ymin,ymax+dy/2,dy)


    grid_x,grid_y = np.meshgrid(x_o,y_o)

    if layer == 'surf':
        u = rawfields[:,3]
        v = rawfields[:,4]
    elif layer == '10':
        u = rawfields[:,5]
        v = rawfields[:,6]
    elif layer == '30':
        u = rawfields[:,7]
        v = rawfields[:,8]
    elif layer == '120':
        u = rawfields[:,9]
        v = rawfields[:,10]

    grid_u = griddata(np.transpose([x,y]), u, (grid_x, grid_y), method='nearest')
    grid_v = griddata(np.transpose([x,y]), v, (grid_x, grid_y), method='nearest')

    return grid_x,grid_y,grid_u,grid_v

def oil_track(sNcFile, ds, time_index):

    # load ncfile
    ncfile = netCDF4.Dataset(sNcFile,'r')
    # load start position of the spill
    y0 = ncfile.variables['non_evaporative_volume'].initial_position_y
    x0 = ncfile.variables['non_evaporative_volume'].initial_position_x
    #print ("Spill location = " + str(x0) + "W ::::: " + str(y0) + "N ")

    # variable extraction
    lats = ncfile.variables['latitude'][time_index,:]
    lons = ncfile.variables['longitude'][time_index,:]

    # generate output grid
    grid_min_longitude = numpy.min(lons)-ds
    grid_min_latitude = numpy.min(lats)-ds
    grid_max_longitude = numpy.max(lons)+ds
    grid_max_latitude = numpy.max(lats)+ds

    x_points = numpy.arange(grid_min_longitude+ds/2,grid_max_longitude,ds)
    y_points = numpy.arange(grid_min_latitude+ds/2,grid_max_latitude,ds)
    box = numpy.zeros((len(y_points),len(x_points)))
    area = (ds*110)**2

    # conversion factor - barrel to tonnes
    oil_density = ncfile.variables['non_evaporative_volume'].oil_density
    #parcel_volume = ncfile.variables['non_evaporative_volume'].volume_of_parcel
    rbm3=0.158987
    barrel2tonnes=1/(rbm3*(oil_density/1000))

    # extract variables of interest
    particle_status = ncfile.variables['particle_status'][time_index,:]
    evaporative_volume = ncfile.variables['evaporative_volume'][time_index,:]
    non_evaporative_volume = ncfile.variables['non_evaporative_volume'][time_index,:]

    # Particle status guide
#        is=0 parcel not released
#        is=1 in the spreading surface slick
#        is=2 on surface but not spreading
#        is=3 dispersed into water column
#        is=-nsg beached on shore segment number nsg

    iNoise=numpy.logical_or(particle_status <= 0, particle_status > 2).nonzero()[0]
    #print("Drama: dispersed particles are being plotted as well!!!")
    lats = numpy.delete(lats, (iNoise), axis=0)
    lons = numpy.delete(lons, (iNoise), axis=0)
    evaporative_volume = numpy.delete(evaporative_volume, (iNoise), axis=0)
    non_evaporative_volume = numpy.delete(non_evaporative_volume, (iNoise), axis=0)


    xp=numpy.round((lons-numpy.min(x_points))/ds)
    yp=numpy.round((lats-numpy.min(y_points))/ds)
    total_volume=(evaporative_volume+non_evaporative_volume)/barrel2tonnes

    for aa in range(0,len(xp)):
        box[yp[aa].astype(int),xp[aa].astype(int)] = box[yp[aa].astype(int),xp[aa].astype(int)] + total_volume[aa]/area

    ncfile.close()
    return x0, y0,x_points, y_points, box

def set_grid(sNcFile,time_line,ds):

    ncfile = netCDF4.Dataset(sNcFile,'r')

    # variable extraction
    lats = ncfile.variables['latitude'][time_line,:]
    lons = ncfile.variables['longitude'][time_line,:]

    # generate output grid
    grid_min_longitude = numpy.min(lons)-ds
    grid_min_latitude = numpy.min(lats)-ds
    grid_max_longitude = numpy.max(lons)+ds
    grid_max_latitude = numpy.max(lats)+ds
    
    return grid_min_longitude,grid_max_longitude,grid_min_latitude,grid_max_latitude
    
################################################################################
# USER INPUTS
################################################################################
input_folder = 'INPFOLD'

oce_folder = input_folder + "/OCE/"
sNcFile = (input_folder + '/spill_properties.nc')

iStartDay = date(INPYY,INPMM,INPDD).toordinal()
iStartHour = INPHH
iStartMinute = MUNIT


# set time steps of interest (hours by default -- Python counting starts from 0).
# It may be a single number e.g. [146] or a list of numbers e.g. np.arange(0,15)
# outputs can be every 6h, for instance, by changing the steps in np.arange to 6,
# for instance.
time_line = numpy.arange(0,DURA,1)
real_time = time_line/24. + (iStartHour+1.)/24. + iStartDay

# set the grid resolution (used to estimate concentrations) in degrees
grid_resolution = 0.15/110

# set output folder where .png files will be placed
output_folder = input_folder
os.system('mkdir ' + output_folder)

# set where you have placed the MEDSLIK bathymetry file
batfile = 'BATFOLD/dtm.bath'


################################################################################
# USER INPUTS - OVER!
################################################################################
# Load landmask
xm,ym,mask=generate_mask(batfile)

# From here onwards, the script should do everything pretty much automatic
# bugs/errors are expected and in case you unfortunate enough to find out one,
# feel free to send us comments/corrections.

# plotting loop
cc= 0
for ii in time_line:

    # extract values
    print('Drawing timestep ' + str(ii))
    x0, y0, x_points, y_points, box = oil_track(sNcFile, grid_resolution, ii)


    if ii==time_line[0]:     
    	
    	grid_min_longitude,grid_max_longitude,grid_min_latitude,grid_max_latitude = set_grid(sNcFile,time_line,grid_resolution)

	geo_buffer=0
    	
    	if np.logical_or((grid_max_latitude-grid_min_latitude)<1,(grid_max_longitude-grid_min_longitude)<1):
    		geo_buffer=.1
    		
#    	if np.abs(grid_max_latitude-grid_min_latitude)<1:
#    		grid_min_latitude=grid_min_latitude-.15
#    		grid_max_latitude=grid_max_latitude+.15
    		
#    	if np.abs(grid_max_longitude-grid_min_longitude)<1:
#    		grid_min_longitude=grid_min_longitude-.15
#    		grid_max_longitude=grid_max_longitude+.15
#    		
#    	if grid_min_latitude<-90:
#    		grid_min_latitude=-90
#    		
#    	if grid_max_latitude>90:
#    		grid_max_latitude=90
#
#    	if grid_min_longitude<-180:
#    		grid_min_longitude=-180
#    	if grid_max_longitude>180:
#    		grid_max_longitude=180   		
    		
    	print('MEDSLIK-II grid boundaries')
    	print('')
    	print('LatMin: ',grid_min_latitude)
    	print('LatMax: ',grid_max_latitude)
    	print('LonMin: ',grid_min_longitude)
    	print('LonMax: ',grid_max_longitude)
    	    			
        m = Basemap(llcrnrlon=grid_min_longitude-geo_buffer,llcrnrlat=grid_min_latitude-geo_buffer,\
            urcrnrlon=grid_max_longitude+geo_buffer,urcrnrlat=grid_max_latitude+geo_buffer,\
            rsphere=(6378137.00,6356752.3142),\
            resolution='f',projection='merc',\
            lat_0=(grid_max_latitude + grid_min_latitude)/2.,\
			lon_0=(grid_max_longitude + grid_min_longitude)/2.,epsg=4326)#4232)   

    # plot trajectory - set map
    plt.figure()

    # plot trajectory - use only non zero areas
    oiled_grid_points=numpy.argwhere(box!=0)
    X=x_points[oiled_grid_points[:,1]]
    Y=y_points[oiled_grid_points[:,0]]
    x,y=m(X,Y)
    x0,y0=m(x0,y0)
    #xr,yr = m(x0+.01,y0+.01) # Spill position
    box_plot=box[oiled_grid_points[:,0],oiled_grid_points[:,1]]

    if cc==0:
        # plot trajectory - define the size of your markers based on the window size
        plot_ds = np.diff(x)
        marker_size = scipy.stats.mode(plot_ds).mode
    
    # plot trajectory - define maximum and minimum concentration values
    vmin = 0.
    if len(box_plot)<1:
        vmax=0.001
    else:
        vmax = np.percentile(box_plot, 92.5) #+.1*np.std(box_plot)

 
    # plot trajectory - actual plot
    cs = m.scatter(x, y, s=1,c=box_plot, edgecolor='',cmap = 'gist_yarg',vmin=vmin,vmax=vmax, marker = 's')
    m.plot(x0,y0,'go',markersize=1)

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

    oce_fields = (oce_folder + '/merc' + YY + mm + dd + '%02d' % (hh) + '.mrc')
    xc,yc,uc,vc = mdkcurrents(oce_fields,'surf') #surf, 10, 30 or 120

    # plot currents - mask land points
    if cc==0:
        f = interp2d(xm[0,:],ym[:,0],mask, kind='linear')
        subset_mask = f(xc[0,:],yc[:,0])
        
        # set scale
        vzao=np.max(np.sqrt(uc**2+vc**2))


        if vzao>1.5:
            scale=20
        elif np.logical_and(vzao>1.,vzao<1.5):
            scale=10
        elif np.logical_and(vzao>.25,vzao<=1.):
            scale=1
        else:
            scale=0.5

        print('Quiver scale applied - ' + str(scale))
        print('Consider applying an ad-hoc scale value if arrows are too small/large')

    uc = uc*subset_mask
    vc = vc*subset_mask
    x,y = m(xc,yc)

    if geo_buffer>0:
        dz = m.quiver(x,y,uc,vc,np.sqrt(uc**2+vc**2),scale=scale,headwidth=5,pivot='middle',width=0.003,zorder=3,color ='w',alpha=1)
    else:
        dz = m.quiver(x[::3,::3],y[::3,::3],uc[::3,::3],vc[::3,::3],np.sqrt(uc[::3,::3]**2+vc[::3,::3]**2),scale=scale,headwidth=5,pivot='middle',width=0.003,zorder=3,color ='w',alpha=1)
    
    cbar = m.colorbar(dz,'right',extend="both",pad=.5)
    cbar.ax.tick_params(labelsize=4)
    cbar.set_label('m/s')

    cbar2 = m.colorbar(cs,'bottom',extend="both",pad=0.5)
    cbar2.ax.tick_params(labelsize=4)
    cbar2.set_label('ton/km2')
    m.plot(x0,y0,'go',markersize=1)
    
    m.drawcoastlines(linewidth=0.05)
    m.fillcontinents(alpha=1,zorder=3)
    m.drawmeridians(numpy.arange(grid_min_longitude-geo_buffer,grid_max_longitude+geo_buffer,(grid_max_longitude-grid_min_longitude+2*geo_buffer)/4.), labels=[0,0,0,1],color='white',linewidth=0.03, fontsize = 8) # draw parallels

    m.drawparallels(numpy.arange(grid_min_latitude-geo_buffer,grid_max_latitude+geo_buffer,(grid_max_latitude-grid_min_latitude+2*geo_buffer)/4.),labels=[1,0,0,0],color='white',linewidth=0.03, fontsize = 8) # draw meridians

    #m.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 300, verbose= True, zorder=2)
    plt.title('Simulated spill trajectory - ' + dd + '.' + mm + '.20' + YY + ' ' + '%02d' % (hh) + ':' + '%02d' % (iStartMinute) + ' UTC')
    
    plt.savefig(output_folder + '/surface_oil_' + '%03d' % (ii+1) + 'h.png',dpi=200,bbox_inches='tight')
    plt.close('all')

    cc = cc + 1
