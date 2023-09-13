#!/bin/bash

#####################################################
#
# Base configuration
#
#####################################################
# add your CMEMS username and password
echo 'Donwloading and transforming CMEMS GLOBAL ocean fields.'
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

# DST_PATH: the output folder
DST_PATH='/scratch/work/lab/$XP_NAME/oce_files/'

# WORK_PATH: the work and output directory
WORK_BASE_PATH="/scratch/work/lab/$XP_NAME/oce_files/"
WORK_PATH="$WORK_BASE_PATH/tmp"
WORK_OUTPATH="$WORK_BASE_PATH/tmp"
WORK_INPATH="$WORK_BASE_PATH/tmp"
mkdir $WORK_BASE_PATH
mkdir $WORK_PATH
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

for D in $(seq 0 $DDAY); do

    # set the current date
    CURRDATE=$(date -d "$PROD_DATE +$D days" +"%Y-%m-%d")
    CURRDATE_SHORT=$(date -d "$PROD_DATE +$D days" +"%y%m%d")
    PASTDATE=$(date -d "$CURRDATE -1 days" +"%Y-%m-%d")
    NEXTDATE=$(date -d "$CURRDATE +1 days" +"%Y-%m-%d")

    # initialise flag
    FILE1=${WORK_PATH}/${CURRDATE}_depth1_step0.nc
    FILE2=${WORK_PATH}/${CURRDATE}_depth2_step0.nc
    FILE3=${WORK_PATH}/${CURRDATE}_depth3_step0.nc
    FILE4=${WORK_PATH}/${CURRDATE}_depth4_step0.nc

    while true ; do

        # if file exist exit!
        if [ -e $FILE1 ] && [ -e $FILE2 ] && [ -e $FILE3 ] && [ -e $FILE4 ]; then
    	    break
        fi

        # download level 1
        if [ ! -e $FILE1 ]; then
			
    	    python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024 --date-min "$PASTDATE 12:00:00" --date-max "$NEXTDATE 12:00:00" --depth-min 0 --depth-max 1 -x $lon_min -X $lon_max -y $lat_min -Y $lat_max --variable thetao --variable uo --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-dir $WORK_INPATH --out-name $FILE1 &
    	    PID1=$!
        fi

        # download level 2
        if [ ! -e $FILE2 ]; then
    	    python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024  --date-min "$PASTDATE 12:00:00" --date-max "$NEXTDATE 12:00:00" --depth-min 9 --depth-max 11 -x $lon_min -X $lon_max -y $lat_min -Y $lat_max --variable thetao --variable uo --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-dir $WORK_INPATH --out-name $FILE2 &
    	    PID2=$!
        fi

        # download level 3
        if [ ! -e $FILE3 ]; then
    	    python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024  --date-min "$PASTDATE 12:00:00" --date-max "$NEXTDATE 12:00:00" --depth-min 29 --depth-max 30 -x $lon_min -X $lon_max -y $lat_min -Y $lat_max --variable thetao --variable uo --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-dir $WORK_INPATH --out-name $FILE3 &
    	    PID3=$!
        fi

        # download level 4
        if [ ! -e $FILE4 ]; then
    	    python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024 --date-min "$PASTDATE 12:00:00" --date-max "$NEXTDATE 12:00:00" --depth-min 130 --depth-max 131 -x $lon_min -X $lon_max -y $lat_min -Y $lat_max --variable thetao --variable uo --variable vo --user $CMEMS_USER --pwd $CMEMS_PASSWORD --out-dir $WORK_INPATH --out-name $FILE4 &
    	    PID4=$!
        fi

        # wait for the second two downloads to finish
		echo $PID1,$PID2
        tail --pid=$PID1 -f /dev/null
        tail --pid=$PID2 -f /dev/null
        tail --pid=$PID3 -f /dev/null
        tail --pid=$PID4 -f /dev/null

    done

    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Merging depth levels"
    cdo merge $FILE1 $FILE2 $FILE3 $FILE4 ${WORK_PATH}/${CURRDATE}_step1.nc

    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Splitting among variables"
    cp ${WORK_PATH}/${CURRDATE}_step1.nc ${WORK_PATH}/${CURRDATE}_step1_T.nc
    cp ${WORK_PATH}/${CURRDATE}_step1.nc ${WORK_PATH}/${CURRDATE}_step1_U.nc
    mv ${WORK_PATH}/${CURRDATE}_step1.nc ${WORK_PATH}/${CURRDATE}_step1_V.nc

    # remove useless variables

    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Removing useless variables"
    ncks -O -x -v uo,vo ${WORK_PATH}/${CURRDATE}_step1_T.nc ${WORK_PATH}/${CURRDATE}_step1_T.nc
    ncks -O -x -v vo,thetao ${WORK_PATH}/${CURRDATE}_step1_U.nc ${WORK_PATH}/${CURRDATE}_step1_U.nc
    ncks -O -x -v uo,thetao ${WORK_PATH}/${CURRDATE}_step1_V.nc ${WORK_PATH}/${CURRDATE}_step1_V.nc

    # convert to nc3
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Converting to netcdf3"
    ncks -3 ${WORK_PATH}/${CURRDATE}_step1_T.nc ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc
    ncks -3 ${WORK_PATH}/${CURRDATE}_step1_U.nc ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc
    ncks -3 ${WORK_PATH}/${CURRDATE}_step1_V.nc ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc

    # rename variables
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Renaming variables"
    ncrename -O -d longitude,nav_lon -d latitude,nav_lat -v longitude,nav_lon -v latitude,nav_lat -v time,time_counter -d time,time_counter -v thetao,votemper -d depth,deptht ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc
    ncrename -O -d longitude,nav_lon -d latitude,nav_lat -v longitude,nav_lon -v latitude,nav_lat -v time,time_counter -d time,time_counter -v uo,vozocrtx -d depth,depthu ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc
    ncrename -O -d longitude,nav_lon -d latitude,nav_lat -v longitude,nav_lon -v latitude,nav_lat -v time,time_counter -d time,time_counter -v vo,vomecrty -d depth,depthv ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc

    # back to nc4
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Back to netcdf4"
    ncks -4 ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc ${WORK_PATH}/${CURRDATE}_step1_T_v4.nc
    ncks -4 ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc ${WORK_PATH}/${CURRDATE}_step1_U_v4.nc
    ncks -4 ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc ${WORK_PATH}/${CURRDATE}_step1_V_v4.nc


    # interpolate
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Interpolating"
    python /scratch/work/scripts/templates/witoil_interp_mercator.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_T_v4.nc ${WORK_BASE_PATH}/MDK_ocean_${CURRDATE_SHORT}_T.nc
    python /scratch/work/scripts/templates/witoil_interp_mercator.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_U_v4.nc ${WORK_BASE_PATH}/MDK_ocean_${CURRDATE_SHORT}_U.nc
    python /scratch/work/scripts/templates/witoil_interp_mercator.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_V_v4.nc ${WORK_BASE_PATH}/MDK_ocean_${CURRDATE_SHORT}_V.nc

done

#rm -fR $WORK_PATH
