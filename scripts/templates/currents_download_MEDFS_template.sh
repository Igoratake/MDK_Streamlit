#!/bin/bash

#####################################################
#
# Base configuration
#
#####################################################
#CMEMS Username and Password
CMEMS_USER=cmems_witoil
CMEMS_PASSWORD=witoil_cmems2020

# APPNAME: a variable used to print the program name in debug messages
APPNAME=$(basename $0)

# DST_PATH: the output folder
DST_PATH='/scratch/work/lab/XP_NAME//oce_files/'

# WORK_PATH: the work and output directory
WORK_BASE_PATH="/scratch/work/lab/XP_NAME//oce_files/"
WORK_PATH="$WORK_BASE_PATH/tmp"
WORK_OUTPATH="$WORK_BASE_PATH/tmp"
WORK_INPATH="$WORK_BASE_PATH/tmp"
mkdir $WORK_BASE_PATH
mkdir $WORK_PATH

# PROD_DATE: the production date
PROD_DATE=$(date -d "YYYY1-MM1-DD1" +%Y%m%d)

# MOVE: 1 if data should be moved to the DST_PATH
MOVE=1

#####################################################
#
# Initial debug info
#
#####################################################

echo "=============================="
echo "=== RUN $(date) "
echo "=============================="

#####################################################
#
# Initial clean
#
#####################################################

rm $WORK_PATH/*

#####################################################
#
# Download data
#
#####################################################

for D in $(seq 0 DDAY); do

	# set the current date
	CURRDATE=$(date -d "$PROD_DATE +$D days" +"%Y-%m-%d")
	CURRDATE_SHORT=$(date -d "$PROD_DATE +$D days" +"%y%m%d")

	# initialise flag
	FILE1=${WORK_PATH}/${CURRDATE}_step1_U.nc
	FILE2=${WORK_PATH}/${CURRDATE}_step1_V.nc
	FILE3=${WORK_PATH}/${CURRDATE}_step1_T.nc

        # download level 1
        if [ ! -e $FILE1 ]; then
			
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 1.0182 --depth-max 1.0183 --variable uo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_u_0m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 10.5365 --depth-max 10.5367 --variable uo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_u_10m.nc 

		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 29.8855 --depth-max 29.8858 --variable uo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_u_30m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 119.853 --depth-max 119.856 --variable uo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_u_120m.nc 

		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Merging depth levels"
		cdo merge ${WORK_PATH}/${CURRDATE}_u_0m.nc ${WORK_PATH}/${CURRDATE}_u_10m.nc ${WORK_PATH}/${CURRDATE}_u_30m.nc ${WORK_PATH}/${CURRDATE}_u_120m.nc ${WORK_PATH}/${CURRDATE}_step1_U.nc

		# convert to nc3
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Converting to netcdf3"
		ncks -3 ${WORK_PATH}/${CURRDATE}_step1_U.nc ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc
    
		# rename variables
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Renaming variables"
		ncrename -O -d lon,nav_lon -d lat,nav_lat -v lon,nav_lon -v lat,nav_lat -v time,time_counter -d time,time_counter -v uo,vozocrtx ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc

		# back to nc4
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Back to netcdf4"
		ncks -4 ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc ${WORK_PATH}/MDK_ocean_${CURRDATE_SHORT}_U_.nc   	
		
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Setting missing values"
		cdo -O -b F32 setmisstoc,9999 -setmissval,9999 ${WORK_PATH}/MDK_ocean_${CURRDATE_SHORT}_U_.nc ${WORK_BASE_PATH}/MDK_ocean_${CURRDATE_SHORT}_U.nc  
    	    
	fi
	
        # download level 1
        if [ ! -e $FILE2 ]; then
			
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 1.0182 --depth-max 1.0183 --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_v_0m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 10.5365 --depth-max 10.5367 --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_v_10m.nc 

		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 29.8855 --depth-max 29.8858 --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_v_30m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 119.853 --depth-max 119.856 --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_v_120m.nc 

		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Merging depth levels"
		cdo merge ${WORK_PATH}/${CURRDATE}_v_0m.nc ${WORK_PATH}/${CURRDATE}_v_10m.nc ${WORK_PATH}/${CURRDATE}_v_30m.nc ${WORK_PATH}/${CURRDATE}_v_120m.nc ${WORK_PATH}/${CURRDATE}_step1_V.nc

		# convert to nc3
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Converting to netcdf3"
		ncks -3 ${WORK_PATH}/${CURRDATE}_step1_V.nc ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc
    
		# rename variables
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Renaming variables"
		ncrename -O -d lon,nav_lon -d lat,nav_lat -v lon,nav_lon -v lat,nav_lat -v time,time_counter -d time,time_counter -v vo,vomecrty ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc

		# back to nc4
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Back to netcdf4"
		ncks -4 ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc ${WORK_PATH}/MDK_ocean_${CURRDATE_SHORT}_V_.nc 
		  
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Setting missing values"
		cdo -O -b F32 setmisstoc,9999 -setmissval,9999 ${WORK_PATH}/MDK_ocean_${CURRDATE_SHORT}_V_.nc ${WORK_BASE_PATH}/MDK_ocean_${CURRDATE_SHORT}_V.nc  	
    	    
	fi
	
        # download level 1
        if [ ! -e $FILE3 ]; then
				
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-tem-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 1.0182 --depth-max 1.0183 --variable thetao --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_t_0m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-tem-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 10.5365 --depth-max 10.5367 --variable thetao --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_t_10m.nc 

		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-tem-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 29.8855 --depth-max 29.8858 --variable thetao --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_t_30m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-tem-an-fc-h --longitude-min lonmin --longitude-max lonmax --latitude-min latmin --latitude-max latmax --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 119.853 --depth-max 119.856 --variable thetao --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_t_120m.nc 

		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Merging depth levels"
		cdo merge ${WORK_PATH}/${CURRDATE}_t_0m.nc ${WORK_PATH}/${CURRDATE}_t_10m.nc ${WORK_PATH}/${CURRDATE}_t_30m.nc ${WORK_PATH}/${CURRDATE}_t_120m.nc ${WORK_PATH}/${CURRDATE}_step1_T.nc

		# convert to nc3
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Converting to netcdf3"
		ncks -3 ${WORK_PATH}/${CURRDATE}_step1_T.nc ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc
    
		# rename variables
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Renaming variables"
		ncrename -O -d lon,nav_lon -d lat,nav_lat -v lon,nav_lon -v lat,nav_lat -v time,time_counter -d time,time_counter -v thetao,votemper ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc

		# back to nc4
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Back to netcdf4"
		ncks -4 ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc ${WORK_PATH}/MDK_ocean_${CURRDATE_SHORT}_T_.nc   
		
		echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Setting missing values"
		cdo -O -b F32 setmisstoc,9999 -setmissval,9999 ${WORK_PATH}/MDK_ocean_${CURRDATE_SHORT}_T_.nc ${WORK_BASE_PATH}/MDK_ocean_${CURRDATE_SHORT}_T.nc  	
    	    
	fi
	

done

rm -fR $WORK_PATH
