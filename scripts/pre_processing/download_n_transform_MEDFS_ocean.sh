#!/bin/bash

#####################################################
#
# Base configuration
#
#####################################################
# add your CMEMS username and password
echo 'Downloading and transforming CMEMS MEDFS ocean fields.'
echo 'Please name your experiment (e.g. paria_case): '
read XP_NAME
echo 'Set spill date dd/mm/yy (e.g., 26/12/20 ): '
read DATE_STRING

SDAY=${DATE_STRING:0:2}
SMONTH=${DATE_STRING:3:2}
SYEAR=${DATE_STRING:6:2}
echo 'Set spill time (e.g., 01:22): '
read HOUR_STRING
HOUR=${HOUR_STRING:0:2}
MINUTE=${HOUR_STRING:3:2}
hour_=$((10#$HOUR))
minutes=$((10#$MINUTE))

echo 'Set the length of your simulation (in h): '
read sim_length
echo 'Set bounding box (in decimal degrees)'
echo 'lon_min : '
read lon_min
echo 'lon_max : '
read lon_max
echo 'lat_min : '
read lat_min
echo 'lat_max : '
read lat_max
echo 'In order to successfully run the script you will need to'
echo 'register at Marine Copernicus Service...'
echo 'Please provide your username (e.g., "my_cmems_username"):'
read CMEMS_USER
echo 'Please provide your password (e.g., "my_cmems_password"):'
read CMEMS_PASSWORD

# PROD_DATE: the ocean files will start from:
PROD_DATE=$(date -d "20$SYEAR-$SMONTH-$SDAY" +%Y%m%d)

# and include the next DDAY days
# NUMBER OF FILES NEEDED
declare -i extra_count=0
if [ $minutes -gt 0 ]
then
hour_=$((10#$hour + 1))
else
hour_=$((10#$hour))
fi

my_int=$((10#$sim_length/24*24))
rem_hours=$((10#$sim_length-10#$my_int))
late_cases=$((10#$rem_hours+10#$hour_))
num_days=$((10#$sim_length/24))

if [ $num_days -gt 0 -a $late_cases -ge 0 ]
then
let "extra_count=$extra_count + 1"
fi

if [ $num_days -eq 0 ]
then
let "extra_count=$extra_count + 1"
fi

if [ $late_cases -ge 24 ]
then
let "extra_count=$extra_count + 1"
fi

let "DDAY=$num_days + $extra_count"


# APPNAME: a variable used to print the program name in debug messages
APPNAME=$(basename $0)

# WORK_PATH: the work and output directory
XP_PATH="/scratch/work/lab/$XP_NAME"
WORK_BASE_PATH="/scratch/work/lab/$XP_NAME/oce_files/"
WORK_PATH="$WORK_BASE_PATH/tmp"
mkdir $XP_PATH
mkdir $WORK_BASE_PATH
mkdir $WORK_PATH


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

for D in $(seq 0 $DDAY); do

	# set the current date
	CURRDATE=$(date -d "$PROD_DATE +$D days" +"%Y-%m-%d")
	CURRDATE_SHORT=$(date -d "$PROD_DATE +$D days" +"%y%m%d")

	# initialise flag
	FILE1=${WORK_PATH}/${CURRDATE}_step1_U.nc
	FILE2=${WORK_PATH}/${CURRDATE}_step1_V.nc
	FILE3=${WORK_PATH}/${CURRDATE}_step1_T.nc

        # download level 1
        if [ ! -e $FILE1 ]; then
			
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 1.0182 --depth-max 1.0183 --variable uo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_u_0m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 10.5365 --depth-max 10.5367 --variable uo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_u_10m.nc 

		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 29.8855 --depth-max 29.8858 --variable uo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_u_30m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 119.853 --depth-max 119.856 --variable uo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_u_120m.nc 

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
			
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 1.0182 --depth-max 1.0183 --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_v_0m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 10.5365 --depth-max 10.5367 --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_v_10m.nc 

		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 29.8855 --depth-max 29.8858 --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_v_30m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-cur-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 119.853 --depth-max 119.856 --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_v_120m.nc 

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
				
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-tem-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 1.0182 --depth-max 1.0183 --variable thetao --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_t_0m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-tem-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 10.5365 --depth-max 10.5367 --variable thetao --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_t_10m.nc 

		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-tem-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 29.8855 --depth-max 29.8858 --variable thetao --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_t_30m.nc 
    	    
		python -m motuclient --motu https://nrt.cmems-du.eu/motu-web/Motu --service-id MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS --product-id med-cmcc-tem-an-fc-h --longitude-min $lon_min --longitude-max $lon_max --latitude-min $lat_min --latitude-max $lat_max --date-min "$CURRDATE 00:30:00" --date-max "$CURRDATE 23:30:00" --depth-min 119.853 --depth-max 119.856 --variable thetao --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-name ${WORK_PATH}/${CURRDATE}_t_120m.nc 

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
