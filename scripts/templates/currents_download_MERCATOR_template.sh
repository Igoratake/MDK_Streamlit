#!/bin/bash

#####################################################
#
# Base configuration
#
#####################################################

#CMEMS Username and Password
CMEMS_USER=your_cmems_user
CMEMS_PASSWORD=your_cmems_password

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
mkdir $WORK_INPATH

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
			
    	    python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024 --date-min "$PASTDATE 12:00:00" --date-max "$NEXTDATE 12:00:00" --depth-min 0 --depth-max 1 -x lonmin -X lonmax -y latmin -Y latmax --variable thetao --variable uo --variable vo --user $CMEMS_USER --pwd $CMEMS_PASS --out-dir $WORK_INPATH --out-name $FILE1 &
    	    PID1=$!
        fi

        # download level 2
        if [ ! -e $FILE2 ]; then
    	    python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024  --date-min "$PASTDATE 12:00:00" --date-max "$NEXTDATE 12:00:00" --depth-min 9 --depth-max 11 -x lonmin -X lonmax -y latmin -Y latmax --variable thetao --variable uo --variable vo --user $CMEMS_USER --pwd $CMEMS_PASS --out-dir $WORK_INPATH --out-name $FILE2 &
    	    PID2=$!
        fi

        # download level 3
        if [ ! -e $FILE3 ]; then
    	    python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024  --date-min "$PASTDATE 12:00:00" --date-max "$NEXTDATE 12:00:00" --depth-min 29 --depth-max 30 -x lonmin -X lonmax -y latmin -Y latmax --variable thetao --variable uo --variable vo --user $CMEMS_USER --pwd $CMEMS_PASS --out-dir $WORK_INPATH --out-name $FILE3 &
    	    PID3=$!
        fi

        # download level 4
        if [ ! -e $FILE4 ]; then
    	    python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024 --date-min "$PASTDATE 12:00:00" --date-max "$NEXTDATE 12:00:00" --depth-min 130 --depth-max 131 -x lonmin -X lonmax -y latmin -Y latmax --variable thetao --variable uo --variable vo --user $CMEMS_USER --pwd $CMEMS_PASS --out-dir $WORK_INPATH --out-name $FILE4 &
    	    PID4=$!
        fi
#$CMEMS_USER --pwd $CMEMS_PASS
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
    python /scratch/work/scripts/templates/witoil_interp_mercator.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_T_v4.nc ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_T.nc
    python /scratch/work/scripts/templates/witoil_interp_mercator.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_U_v4.nc ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_U.nc
    python /scratch/work/scripts/templates/witoil_interp_mercator.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_V_v4.nc ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_V.nc

    # move files in the final directory
    if [[ $MOVE = 1 ]]; then
        echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Moving files to final directory"
        mv ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_T.nc ${DST_PATH}/MDK_ocean_${CURRDATE_SHORT}_T.nc
        mv ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_U.nc ${DST_PATH}/MDK_ocean_${CURRDATE_SHORT}_U.nc
        mv ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_V.nc ${DST_PATH}/MDK_ocean_${CURRDATE_SHORT}_V.nc
		rm $WORK_PATH/*
    fi
done

rm -fR $WORK_PATH
