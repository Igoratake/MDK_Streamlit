#!/usr/bin/python

import os
import numpy
import math
import datetime
import netCDF4
import scipy.interpolate
import cPickle
import matplotlib as mpl
import shapefile
import glob
import pdb
import sys


def xp_environ(itosra_dir,xp_name):
	xp_files = itosra_dir + '/' + xp_name + '/xp_files'
	met_files = itosra_dir + '/' + xp_name + '/met_files'
	oce_files = itosra_dir + '/' + xp_name + '/oce_files'
	bnc_files = itosra_dir + '/' + xp_name + '/bnc_files'
	outputs = itosra_dir + '/' + xp_name + '/out_files'
    
	os.system('mkdir ' + itosra_dir + '/' + xp_name)
	os.system('mkdir ' + xp_files)
	os.system('mkdir ' + met_files)
	os.system('mkdir ' + oce_files)
	os.system('mkdir ' + bnc_files)
	os.system('mkdir ' + outputs)    

def mdk_extract_gen(iots_dir, xp_name, x_curr, y_curr, x_wind, y_wind):

	# name your sim
	xp_folder = iots_dir + xp_name

	os.system("LC_CTYPE=C && LANG=C sed 's/XCURR/" + str(x_curr) + "/' /scratch/work/scripts/templates/Extract_II_template.for > " + xp_folder + "/xp_files/Extract_II.for")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/YCURR/" + str(y_curr) + "/' " + xp_folder + "/xp_files/Extract_II.for")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/XWIND/" + str(x_wind) + "/' " + xp_folder + "/xp_files/Extract_II.for")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/YWIND/" + str(y_wind) + "/' " + xp_folder + "/xp_files/Extract_II.for")

def config1_gen_pointsource(iots_dir, xp_name, api_string, duration_string,\
    volume_string, time_string, hour_string, sim_length_string, lon_mean,lat_mean):

	# name your sim
	xp_folder = iots_dir + xp_name

	# get your date parameters
	YY = (time_string[6::])
	MM = (time_string[3:5])
	DD = (time_string[0:2])
	hh = (hour_string[0:2])
	mm = (hour_string[3:5])

	# get spill central position
	lon_deg = numpy.floor(numpy.abs(lon_mean))*(numpy.abs(lon_mean)/lon_mean)
	lon_sec = (lon_mean - lon_deg)*60.

	lat_deg = numpy.floor(numpy.abs(lat_mean))*(numpy.abs(lat_mean)/lat_mean)
	lat_sec = (lat_mean - lat_deg)*60.

	print('Spill coordinates: ')
	print('Lon: ' + str(lon_deg) + 'deg ' + str(lon_sec) + 'min')
	print('Lon: ' + str(lat_deg) + 'deg ' + str(lat_sec) + 'min')
	print lon_deg,lon_sec,lon_mean,lat_mean

	# add simulation mame
	os.system("LC_CTYPE=C && LANG=C sed 's/RUNNAME/" + xp_name + "/' /scratch/work/scripts//templates/config1_pointsource_template_0.txt > " + xp_folder + "/xp_files/config1_template_1.txt")

	# add spill time
	os.system("LC_CTYPE=C && LANG=C sed 's/HH/" + hh + "/' " + xp_folder + "/xp_files/config1_template_1.txt > " + xp_folder + "/xp_files/config1_template_2.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/mm/" + mm + "/' " + xp_folder + "/xp_files/config1_template_2.txt > " + xp_folder + "/xp_files/config1_template_3.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/DD/" + DD + "/' " + xp_folder + "/xp_files/config1_template_3.txt > " + xp_folder + "/xp_files/config1_template_4.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/MM/" + MM + "/' " + xp_folder + "/xp_files/config1_template_4.txt > " + xp_folder + "/xp_files/config1_template_5.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/YY/" + YY + "/' " + xp_folder + "/xp_files/config1_template_5.txt > " + xp_folder + "/xp_files/config1_template_6.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/SIMLENGTH/" + sim_length_string + "/' " + xp_folder + "/xp_files/config1_template_6.txt > " + xp_folder + "/xp_files/config1_template_7.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/APIOT/" + api_string + "/' " + xp_folder + "/xp_files/config1_template_7.txt > " + xp_folder + "/xp_files/config1_template_8.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/SRATE/" + volume_string + "/' " + xp_folder + "/xp_files/config1_template_8.txt > " + xp_folder + "/xp_files/config1.txt")

	os.system("LC_CTYPE=C && LANG=C sed -i 's/DURAT/" + duration_string + "/' " + xp_folder + "/xp_files/config1.txt")
	# add central position
	os.system("LC_CTYPE=C && LANG=C sed -i 's/LATd/" + '%02d' % (lat_deg) + "/' " + xp_folder + "/xp_files/config1.txt")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/LATm/" + '%05.3f' % (lat_sec) + "/' " + xp_folder + "/xp_files/config1.txt")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/LONd/" + '%02d' % (lon_deg) + "/' " + xp_folder + "/xp_files/config1.txt")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/LONm/" + '%02d' % (lon_sec) + "/' " + xp_folder + "/xp_files/config1.txt")
    	
def config1_gen_polysource(iots_dir, xp_name, api_string, duration_string,\
    volume_string, time_string, hour_string, sim_length_string, slick_num_string,lon_mean,lat_mean):

	# name your sim
	xp_folder = iots_dir + xp_name

	# get your date parameters
	YY = (time_string[6::])
	MM = (time_string[3:5])
	DD = (time_string[0:2])
	hh = (hour_string[0:2])
	mm = (hour_string[3:5])

	# get spill central position
	lon_deg = numpy.floor(numpy.abs(lon_mean))*(numpy.abs(lon_mean)/lon_mean)
	lon_sec = (lon_mean - lon_deg)*60.

	lat_deg = numpy.floor(numpy.abs(lat_mean))*(numpy.abs(lat_mean)/lat_mean)
	lat_sec = (lat_mean - lat_deg)*60.

	print('Spill coordinates: ')
	print('Lon: ' + str(lon_deg) + 'deg ' + str(lon_sec) + 'min')
	print('Lon: ' + str(lat_deg) + 'deg ' + str(lat_sec) + 'min')
	print lon_deg,lon_sec,lon_mean,lat_mean

	# add simulation mame
	os.system("LC_CTYPE=C && LANG=C sed 's/RUNNAME/" + xp_name + "/' /scratch/work/scripts//templates/config1_template_0.txt > " + xp_folder + "/xp_files/config1_template_1.txt")

	# add spill time
	os.system("LC_CTYPE=C && LANG=C sed 's/HH/" + hh + "/' " + xp_folder + "/xp_files/config1_template_1.txt > " + xp_folder + "/xp_files/config1_template_2.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/mm/" + mm + "/' " + xp_folder + "/xp_files/config1_template_2.txt > " + xp_folder + "/xp_files/config1_template_3.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/DD/" + DD + "/' " + xp_folder + "/xp_files/config1_template_3.txt > " + xp_folder + "/xp_files/config1_template_4.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/MM/" + MM + "/' " + xp_folder + "/xp_files/config1_template_4.txt > " + xp_folder + "/xp_files/config1_template_5.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/YY/" + YY + "/' " + xp_folder + "/xp_files/config1_template_5.txt > " + xp_folder + "/xp_files/config1_template_6.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/SIMLENGTH/" + sim_length_string + "/' " + xp_folder + "/xp_files/config1_template_6.txt > " + xp_folder + "/xp_files/config1_template_7.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/APIOT/" + api_string + "/' " + xp_folder + "/xp_files/config1_template_7.txt > " + xp_folder + "/xp_files/config1_template_8.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/N_SLICKS/" + slick_num_string + "/' " + xp_folder + "/xp_files/config1_template_8.txt > " + xp_folder + "/xp_files/config1_template_9.txt")
	os.system("LC_CTYPE=C && LANG=C sed 's/SRATE/" + volume_string + "/' " + xp_folder + "/xp_files/config1_template_9.txt > " + xp_folder + "/xp_files/config1_10.txt")

	# add spill polygon
	os.system("cat " + xp_folder + "/xp_files/config1_10.txt " + xp_folder + "/xp_files/multispills.txt >" + xp_folder + "/xp_files/config1.txt")

	# add central position
	os.system("LC_CTYPE=C && LANG=C sed -i 's/LATd/" + '%02d' % (lat_deg) + "/' " + xp_folder + "/xp_files/config1.txt")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/LATm/" + '%05.3f' % (lat_sec) + "/' " + xp_folder + "/xp_files/config1.txt")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/LONd/" + '%02d' % (lon_deg) + "/' " + xp_folder + "/xp_files/config1.txt")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/LONm/" + '%02d' % (lon_sec) + "/' " + xp_folder + "/xp_files/config1.txt")


def get_shp2mdk_parts(sShapeDirectory,xp_folder):
    sShapeList=glob.glob(sShapeDirectory + '/*.shp')
    # read shapefile
    text_file = open(xp_folder + "/xp_files/multispills.txt", "w")

    for ia in range(0,len(sShapeList)):
        xi = shapefile.Reader(sShapeList[ia])
        fshapes = xi.shapes()
        frecords = xi.records()
        
        spill_counter = 1
        
        lon_mean = 0.
        lat_mean = 0.
        
        for record, shape in zip(frecords,fshapes):
            lons_p,lats_p = zip(*shape.points)
            lon_mean = lon_mean + numpy.mean(lons_p)
            lat_mean = lat_mean + numpy.mean(lats_p)

            parts = fshapes[0].parts

            for ii in range(0,len(parts)):
                
                counter_i = parts[ii]
                
                if parts[ii] == parts[-1]:
                    counter_e = len(lons_p)
                else:
                    counter_e = parts[ii+1]
                
                #poor man subsampling
                #if (counter_e - counter_i) > 100:
                #    step = 5
                #elif (counter_e - counter_i) < 10:
                #    continue
                #else:
                #    step = 1
                    
                counter = 1
                
                for zz in range(counter_i,counter_e):
                    string1 = ('S' + str(spill_counter) + 'lon[' + str(counter) + ']=' + str(lons_p[zz]) + '\n')
                    text_file.write(string1)
                    string2 = ('S' + str(spill_counter) + 'lat[' + str(counter) + ']=' + str(lats_p[zz]) + '\n')
                    text_file.write(string2)
                    counter = counter + 1
                    print '**************'
                    print string1
                    print string2
                    print str(spill_counter)
                    print '**************'
                
                spill_counter = spill_counter + 1
                
                #plt.plot(lons_p[counter_i:counter_e],lats_p[counter_i:counter_e],'k-')
                #plt.show()
                
                
                
    text_file.close()

    sW = numpy.min(lons_p)
    sE = numpy.max(lons_p)
    sS = numpy.min(lats_p)
    sN = numpy.max(lats_p)
    lon_mean = (sW+sE)/2.
    lat_mean = (sS+sN)/2.
    print 'Location centre of the spill'
    print lon_mean,lat_mean
    print 'in degs'
    print int(lon_mean),int(lat_mean)
    print 'and minutes'
    print (lon_mean-int(lon_mean))*60.,(lat_mean-int(lat_mean))*60.
    

    return sW,sE,sS,sN,spill_counter,lon_mean,lat_mean
    
def get_shp2mdk(sShapeDirectory,xp_folder):
	
	sShapeList=glob.glob(sShapeDirectory + '/*.shp')
	# read shapefile
	text_file = open(xp_folder + "/xp_files/multispills.txt", "w")

	for ia in range(0,len(sShapeList)):
		r = shapefile.Reader(sShapeList[ia])
		shapes = r.shapes()
		records = r.records()
		

		spill_counter = 1

		lon_mean = 0.
		lat_mean = 0.

		for record, shape in zip(records,shapes):
			lons_p,lats_p = zip(*shape.points)

			lon_mean = lon_mean + numpy.mean(lons_p)
			lat_mean = lat_mean + numpy.mean(lats_p)

			for zz in range(0,len(lons_p)):
				string1 = ('S' + str(spill_counter) + 'lon[' + str(zz+1) + ']=' + str(lons_p[zz]) + '\n')
				text_file.write(string1)
				string2 = ('S' + str(spill_counter) + 'lat[' + str(zz+1) + ']=' + str(lats_p[zz]) + '\n')
				text_file.write(string2)

			spill_counter = spill_counter + 1
		
	text_file.close()
	sW = numpy.min(lons_p)
	sE = numpy.max(lons_p)
	sS = numpy.min(lats_p)
	sN = numpy.max(lats_p)
	lon_mean = lon_mean/(spill_counter-1)
	lat_mean = lat_mean/(spill_counter-1)

	return sW,sE,sS,sN,spill_counter,lon_mean,lat_mean

def mercator_currfile_gen(xp_name, xp_folder,YYYY1,MM1,DD1,DDAY,xW,xE,yS,yN):

	# eliminate eventual zeros from date strings... in a not very polished way
	mm = int(MM1)
	MM1 = str(mm)
    
	mm = int(DD1)
	DD1 = str(mm)

	# add time constraints

	os.system("LC_CTYPE=C && LANG=C sed 's/YYYY1/" + YYYY1 + "/' /scratch/work/scripts//templates/currents_download_MERCATOR_template.sh > " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/MM1/" + MM1 + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/DD1/" + DD1 + "/' " + xp_folder + "/currents_download.sh")

	os.system("LC_CTYPE=C && LANG=C sed -i 's/DDAY/" + str(DDAY) + "/' " + xp_folder + "/currents_download.sh")
	# add geo constraints
	os.system("LC_CTYPE=C && LANG=C sed -i 's/lonmin/" + xW + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/lonmax/" + xE + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/latmin/" + yS + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/latmax/" + yN + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/XP_NAME/" + xp_name + "/' " + xp_folder + "/currents_download.sh")

def medfs_currfile_gen(xp_name, xp_folder,YYYY1,MM1,DD1,DDAY,xW,xE,yS,yN):

	# eliminate eventual zeros from date strings... in a not very polished way
	mm = int(MM1)
	MM1 = str(mm)
    
	mm = int(DD1)
	DD1 = str(mm)

	# add time constraints

	os.system("LC_CTYPE=C && LANG=C sed 's/YYYY1/" + YYYY1 + "/' /scratch/work/scripts//templates/currents_download_MEDFS_template.sh > " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/MM1/" + MM1 + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/DD1/" + DD1 + "/' " + xp_folder + "/currents_download.sh")

	os.system("LC_CTYPE=C && LANG=C sed -i 's/DDAY/" + str(DDAY) + "/' " + xp_folder + "/currents_download.sh")
	# add geo constraints
	os.system("LC_CTYPE=C && LANG=C sed -i 's/lonmin/" + xW + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/lonmax/" + xE + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/latmin/" + yS + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/latmax/" + yN + "/' " + xp_folder + "/currents_download.sh")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/XP_NAME/" + xp_name + "/' " + xp_folder + "/currents_download.sh")
	
def mdk_windfile_gen(xp_name, xp_folder,YYYY1,MM1,DD1,YYYY2,MM2,DD2,xW,xE,yS,yN):

	# eliminate eventual zeros from date strings... in a not very polished way
	mm = int(MM1)
	MM1 = str(mm)

	mm = int(MM2)
	MM2 = str(mm)

	mm = int(DD1)
	DD1 = str(mm)

	mm = int(DD2)
	DD2 = str(mm)

	# add time constraints
	os.system("LC_CTYPE=C && LANG=C sed 's/YYYY1/" + YYYY1 + "/' /scratch/work/scripts//templates/download_era5_template.py > " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/YYYY2/" + YYYY2 + "/' " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/MM1/" + MM1 + "/' " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/MM2/" + MM2 + "/' " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/DD1/" + DD1 + "/' " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/DD2/" + DD2 + "/' " + xp_folder + "/download_era_custom.py")
	# add geo constraints
	os.system("LC_CTYPE=C && LANG=C sed -i 's/lonmin/" + xW + "/' " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/lonmax/" + xE + "/' " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/latmin/" + yS + "/' " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/latmax/" + yN + "/' " + xp_folder + "/download_era_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed -i 's/XP_NAME/" + xp_name + "/' " + xp_folder + "/download_era_custom.py")

def bnc_files(xp_name, xp_folder):

	# add time constraints 
	os.system("LC_CTYPE=C && LANG=C sed 's/XP_NAME/" + xp_name + "/' /scratch/work/scripts//templates/generate_bathymetry_template.py > " +  xp_folder + "/generate_bathymetry_custom.py")
	os.system("LC_CTYPE=C && LANG=C sed 's/XP_NAME/" + xp_name + "/' /scratch/work/scripts//templates/generate_coastline_template.py > " +  xp_folder + "/generate_coastline_custom.py")

def interp_t(iOutputUd, iHRTimeLine, iLRTimeLine):
		# prepare storing matrixes
		iShapeO = numpy.shape(iOutputUd)
		iOutputU=numpy.zeros((24,4,iShapeO[2],iShapeO[3]))-32767.0	# u(time,depth,y,x)
		#interpolating
		for ii in range(0,iShapeO[2]):
			for jj in range(0,iShapeO[3]):
				for dd in range(0,4):
					if iOutputUd[0,dd,ii,jj]>-20:
						iOutputU[:,dd,ii,jj]=numpy.interp(iHRTimeLine,iLRTimeLine,iOutputUd[:,dd,ii,jj])
						#Extrapolating data
						if (dd!=0 and any(iOutputU[:,dd,ii,jj]<-2) and all(iOutputU[:,dd-1,ii,jj]>-2)):
							iOutputU[:,dd,ii,jj]=iOutputU[:,dd-1,ii,jj]
		return iOutputU

def oce_grid(filename):

	fOCM = netCDF4.Dataset(filename)
	x_mod = fOCM.variables['nav_lon'][:]
	y_mod = fOCM.variables['nav_lat'][:]
	fOCM.close()
	return x_mod, y_mod

# Getting header
def getheader(fid):

	A=numpy.fromfile(fid,dtype='>i',count=8,sep="")

	cnt=A.size

	if cnt<8:  # This gets triggered by the EOF
		return

	else:
		# ver=bitand(bitshift(A(3),-8),255);
		a=A[2] >> 8
		b=255
		ver= a & b

	# Assuming that the GSHHS version used is recent (and comes with MEDSLIK-II Installation pack)

		level = A[2] & b
		a=A[2] >> 16
		greenwich= a & b

		a=A[2] >> 24
		source=a & b

		A[2]=level

		#A[8]=greenwich*65536

		if A.size<=8:
			A=numpy.hstack((A,greenwich*65536))
		else:
			A[8]=greenwich*65536

		A2=numpy.fromfile(fid,dtype='>i',count=3,sep="")


		return A, cnt

def extract_coastline(x_mod,y_mod,sOutputFile):

	# Define limits
	iLatitudeMin= numpy.min(y_mod)
	iLatitudeMax= numpy.max(y_mod)
	iLongitudeMin= numpy.min(x_mod)
	iLongitudeMax= numpy.max(x_mod)

	# Path for your full resolution GSHHS file

	file='/scratch/work/scripts//work/data/gshhs/gshhs_f.b'

	lats=numpy.array([iLatitudeMin, iLatitudeMax])
	longs=numpy.array([iLongitudeMin, iLongitudeMax])

	llim=numpy.remainder(longs[0]+360,360)*1e6
	rlim=numpy.remainder(longs[1]+360,360)*1e6
	tlim=lats[1]*1e6
	blim=lats[0]*1e6


	mrlim=numpy.remainder(longs[1]+360+180,360)-180
	mllim=numpy.remainder(longs[0]+360+180,360)-180
	mtlim=lats[1]
	mblim=lats[0]


	# Preparing matrices
	ncst=numpy.nan+numpy.zeros((10561669,2))
	Area=numpy.zeros((188611,1))
	k=numpy.ones((188612,1))
	decfac=12500

	# Open GSHHS_f file

	fid = open(file, 'r')

	Area2=Area.copy()

	A,cnt=getheader(fid)


	l=-1

	while (cnt>0):

	# A: 1:ID, 2:num points, 3:land/lake etc., 4-7:w/e/s/n, 8:area, 9:greenwich crossed.

		iPointsInSegment=A[1]*2
		C=numpy.fromfile(fid,dtype='>i',count=iPointsInSegment,sep="")  # Read all points in the current segment

	#For Antarctica the lime limits are 0 to 360 (exactly), thus c==0 and the
	#line is not chosen for (e.g. a conic projection of part of Antarctica)
	#Fix 30may/02

		if A[4]==360e6: A[4]=A[4]-1

		a=rlim>llim # Map limits cross longitude jump? (a==1 is no)
		b=A[8]<65536 # Cross boundary? (b==1 if no).
		c=llim<numpy.remainder(A[4]+360e6,360e6)
		d=rlim>numpy.remainder(A[3]+360e6,360e6)
		e=tlim>A[5] and blim<A[6]

	#  This test checks whether the lat/long box containing the line overlaps that of
	# the map. There are various cases to consider, depending on whether map limits
	# and/or the line limits cross the longitude jump or not.


		if e and (  (a and ( (b and c and d) or (not b and (c or d)) )) or (not a and (not b or (b and (c or d))) ) ):

			l=l+1
			iLengthC=C.size

			x=C[numpy.arange(0,iLengthC,2)]*1e-6
			y=C[numpy.arange(1,iLengthC,2)]*1e-6
			dx=numpy.diff(x,n=1,axis=0)

			higher=dx>356
			lower=dx<-356
			eastern=x[0]>180
			x=x-360*numpy.cumsum([numpy.hstack((eastern.astype(int),higher.astype(int) - lower.astype(int)))])

	#Antarctic is a special case - extend contour to make nice closed polygon
	#that doesn't surround the pole.

			if numpy.abs(x[0])<1 and numpy.abs(y[0]+68.9)<1:

				y=numpy.concatenate((-89.9, -78.4, y[x<=-180], y[x>-180], -78.4, -89.9*numpy.ones((18,1))))
				iAntarctic=numpy.arange(-180,161,20)
				x=numpy.concatenate((180, 180,x[x<=-180]+360,x[x>-180],-180, iAntarctic.conj().transpose()))
				del iAntarctic


	# First and last point should be the same IF THIS IS A POLYGON
	# if the Area=0 then this is a line, and don't add points!

			if A[7]>0:

				if x[-1] != x[0] or y[-1] != y[0]:

					x=numpy.hstack((x,x[0]))
					y=numpy.hstack((y,y[0]))


	# get correct curve orientation for patch-fill algorithm.

				iCurveOrientation=numpy.diff(x,n=1,axis=0) * ( y[0:-1] + y[1:] ) / 2
				Area2[l]=iCurveOrientation.sum(axis=0),
				del iCurveOrientation
				Area[l]=A[7] / 10

				# ok for now

				if numpy.remainder(A[2],2)==0:
					Area[l]=-numpy.abs(Area[l]);

					if Area2[l]>0:

						x=x[::-1]
						y=y[::-1]
						#ok for now
				else:
					if Area2[l]<0:
						x=x[::-1]
						y=y[::-1]
						#ok for now

			else:

	# Later on 2 point lines are clipped so we want to avoid that

				if x.size==2:

					x=numpy.hstack((x[0],x.mean(axis=0), x[1]))
					y=numpy.hstack((y[0],y.mean(axis=0), y[1]))


	# Here we try to reduce the number of points.

			xflag=0

			if x.max(0)>180: # First, save original curve for later if we anticipate

				sx=x.copy()
				sy=y.copy()   # a 180-problem.
				xflag=1

	#Look for points outside the lat/long boundaries, and then decimate them
	 # by a factor of about 'decfac' (don't get rid of them completely because that
	   # can sometimes cause problems when polygon edges cross curved map edges).

			tol=0.2

			#ok for now

	#Do y limits, then x so we can keep corner points.

			nn=numpy.logical_or((y>mtlim+tol),(y<mblim-tol))

	# keep one extra point when crossing limits, also the beginning/end point.

			bb=numpy.concatenate(([0],numpy.diff(nn.astype(int),n=1,axis=0)))>0

			cc=numpy.concatenate((numpy.diff(nn.astype(int),n=1,axis=0),[0]))<0

			dd=bb.astype(int) + cc.astype(int)

			minlon=dd>dd.min(0)

			nn=nn-minlon.astype(int)

			nn[0]=0
			nn[-1]=0

			del bb
			del cc
			del dd
			del minlon

	# decimate vigorously

			bb=numpy.remainder(numpy.arange(1,numpy.size(nn)+1,1),decfac)
			nn=numpy.logical_and(nn,bb.astype(int))

			x=numpy.delete(x,nn.nonzero(),axis=0)
			y=numpy.delete(y,nn.nonzero(),axis=0)

			#ok for now

			if mrlim>mllim: # no wraparound

				aa=numpy.logical_or(x>mrlim+tol,x<mllim-tol)
				bb=numpy.logical_and(aa,y<mtlim)
				nn=numpy.logical_and(bb,y>mblim)

				#ok for now

			else:

				aa=numpy.logical_and(x>mrlim+tol,x<mllim-tol)
				bb=numpy.logical_and(aa,y<mtlim)
				nn=numpy.logical_and(bb,y>mblim)



	# ------------------------------------------------------------------------------------------------------
			del bb

			bb=numpy.concatenate(([0],numpy.diff(nn.astype(int),n=1,axis=0)))>0
			cc=numpy.concatenate((numpy.diff(nn.astype(int),n=1,axis=0),[0]))<0
			dd=bb.astype(int) + cc.astype(int)

			minlon=dd>dd.min(0)
			nn=nn-minlon.astype(int)

			nn[0]=0
			nn[-1]=0

			del bb
			del cc
			del dd
			del aa

			#ok for now

			# decimating vigorously again

			bb=numpy.remainder(numpy.arange(1,numpy.size(nn)+1,1),decfac)

			nn=numpy.logical_and(nn.astype(int),bb.astype(int))

			x=numpy.delete(x,nn.nonzero(),axis=0)
			y=numpy.delete(y,nn.nonzero(),axis=0)

			# Move all points "near" to map boundaries.
			# I'm not sure about the wisdom of this - it might be better to clip
			# to the boundaries instead of moving. Hmmm.


			y[y>(mtlim+tol)]=mtlim+tol

			y[y<(mblim-tol)]=mblim-tol

			# ok for now

			if mrlim>mllim: # Only clip long bdys if I can tell I'm on the right
			# or left (i.e. not in wraparound case
				x[x>(mrlim+tol)]=mrlim+tol
				x[x<(mllim-tol)]=mllim-tol

			# ok for now

			# plot(x,y);pause;

			k[l+1]=k[l]+x.size+1;

			ncst[numpy.arange((k[l].astype(int)),(k[l+1].astype(int)-1),1),0]=x

			ncst[numpy.arange((k[l].astype(int)),(k[l+1].astype(int)-1),1),1]=y

			ncst[k[l+1].astype(int),]=[numpy.nan,numpy.nan]

			# This is a little tricky...the filling algorithm expects data to be in the
			# range -180 to 180 deg long. However, there are some land parts that cut across
			# this divide so they appear at +190 but not -170. This causes problems later...
			# so as a kludge I replicate some of the problematic features at 190-360=-170.
			# Small islands are just duplicated, for the Eurasian landmass I just clip
			# off the eastern part.

			if xflag:

				l=l+1
				Area[l]=Area[l-1]

				#ok for now

				if abs(Area[l])>1e5:

					iIndexBase=numpy.arange(0,sx.size,1)

					nn=iIndexBase[numpy.where(sx>180)]
					nn=numpy.hstack((nn,nn[0]))

					k[l+1]=k[l]+nn.size+1

					ncst[numpy.arange((k[l].astype(int)),(k[l+1].astype(int))-1,1),0]=sx[nn]-360
					ncst[numpy.arange((k[l].astype(int)),(k[l+1].astype(int))-1,1),1]=sy[nn]

					# ok for now

				else:   # repeat the island at the other edge.

					k[l+1]=k[l]+sx.size+1

					ncst[numpy.arange((k[l].astype(int)),(k[l+1].astype(int))-1,1),0]=sx-360
					ncst[numpy.arange((k[l].astype(int)),(k[l+1].astype(int))-1,1),1]=sy


				ncst[k[l+1].astype(int),]=[numpy.nan,numpy.nan]


		try:
			A,cnt=getheader(fid)
		except:
			print 'Data extraction process has finished. Slicing...'
			break

	#Getting rid of unused rows

	ncst=numpy.delete(ncst, (numpy.arange(k[l+1].astype(int), ncst.size/2)), axis=0) # get rid of unused part of data matrices
	Area=numpy.delete(Area, (numpy.arange((l+1), Area.size+1)), axis=0)
	k=numpy.delete( k , ( numpy.arange ( (l+2) , k.size+1)), axis=0)

	print '...Done. Printing it on a txt file...'

	iSegmentLength=numpy.diff(k,n=1,axis=0)

	# Organizing segments according to their length -- descending order
	IX=iSegmentLength.argsort(axis=0)[::-1]

	# writes the first line of the .map file. It should contain the # of "isles"
	CoastFile=open(sOutputFile,'w')
	CoastFile.write("%-4.0f \n" % (IX.size))
	iTargetSites=[]
        iTargetSite=numpy.array([0.,0.,0.,0.])

	# prints coastline data island by island


	for t in IX:

		# extracts the island
		iCoastalSection=ncst[numpy.arange(k[t].astype(int),k[t+1].astype(int)-1,1),]
		iCoastalLength=iCoastalSection.size/2
		#prints the length of the island
		CoastFile.write("%-4.0f %1.0f \n" % (iCoastalLength,0))
		#prints data related to the island
		for r in numpy.arange(0,iCoastalSection.size/2,1):
			CoastFile.write("%-8.5f %-6.5f \n" % (iCoastalSection[r,0], iCoastalSection[r,1]))

		for i in range(0,len(iCoastalSection)-1):
                        iTargetSite[0]=iCoastalSection[i,0]
                        iTargetSite[1]=iCoastalSection[i,1]
                        iTargetSite[2]=iCoastalSection[i+1,0]
                        iTargetSite[3]=iCoastalSection[i+1,1]
                        iTargetSites.append(list(iTargetSite))

	CoastFile.close()
	numpy.savetxt(sOutputFile[:-3] + 'txt', numpy.array(iTargetSites))

def load_gebco(filename):

	fGEBCO = netCDF4.Dataset(filename)
	zz=fGEBCO.variables["z"][:]
	cols, rows = fGEBCO.variables["dimension"]
	iDs = fGEBCO.variables["spacing"][0]

	# Coordinates for GEBCO corners - LAT,LON
	iNECorner=numpy.array([89.+(59./60)+45./(60*60), -179.-(59./60)-45./(60*60)])
	iSWCorner=numpy.array([-90.,180.])

	iLatitude=numpy.arange(iNECorner[0],iSWCorner[0],-iDs)
	iLongitude=numpy.arange(iNECorner[1],iSWCorner[1],iDs)

	# Reshape bathymetry into m x n matrix
	a=numpy.shape(iLongitude)[0]
	b=numpy.shape(iLatitude)[0]
	Z = zz.reshape(b, a)
	fGEBCO.close()
	return iLatitude, iLongitude, Z

# crop GEBCO
def interp_gebco(iLatitude, iLongitude, Z, x_mod, y_mod):

	iLatitudeMin= numpy.min(y_mod)
	iLatitudeMax= numpy.max(y_mod)
	iLongitudeMin= numpy.min(x_mod)
	iLongitudeMax= numpy.max(x_mod)

	print 'Cropping bat file for:'
	print str(iLongitudeMin), str(iLongitudeMax), ' Longitude'
	print str(iLatitudeMin), str(iLatitudeMax), ' Latitude'
	# Crop to area of interest
	iLonIndex=numpy.argwhere((iLongitude>=iLongitudeMin) & (iLongitude<=iLongitudeMax))
	iLatIndex=numpy.argwhere((iLatitude>=iLatitudeMin) & (iLatitude<=iLatitudeMax))

	x_crop, y_crop = numpy.meshgrid(iLongitude[iLonIndex],iLatitude[iLatIndex])
	z_crop = Z[numpy.min(iLatIndex):(numpy.max(iLatIndex)+1),numpy.min(iLonIndex):(numpy.max(iLonIndex)+1)]

	# Generate interpolator
	y_crop = numpy.flipud(y_crop)
	x_crop = numpy.flipud(x_crop)
	z_crop = numpy.flipud(z_crop)

	z_int = scipy.interpolate.RectBivariateSpline(y_crop[:,1],x_crop[1,:],z_crop)

	# Interpolate
	#z_proc = z_int(y_mod[:,1],x_mod[1,:])
	z_proc = z_int(y_mod,x_mod)

	# Fix orientation
	z_proc = numpy.flipud(z_proc)

	# Convert bathymetry to MDK-II
	mdk_z=[]
	mdk_x=[]
	mdk_y=[]

	r_,c_ = z_proc.shape
	for i in range(0,r_,1):
		for j in range(0,c_,1):
			mdk_z.append(z_proc[i,j])
			mdk_x.append(x_mod[j])
			mdk_y.append(y_mod[i])

	mdk_z = numpy.array(mdk_z)
	land_mask = numpy.where(mdk_z > 0)
	mdk_z[land_mask]=-9999
	mdk_z = -1.*(mdk_z)
	return mdk_x, mdk_y, mdk_z, c_, r_


