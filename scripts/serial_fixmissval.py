import os
import glob

list = glob.glob('/scratch/work/lab/rijeka/oce_files/MDK*.nc')

for ii in list:
	os.system('cdo -O -b F32 setmisstoc,9999 -setmissval,9999 ' + ii + ' ' + ii + '_')
	
