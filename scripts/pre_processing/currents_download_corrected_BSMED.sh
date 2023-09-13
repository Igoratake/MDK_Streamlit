#!/bin/bash

#####################################################
#
# Base configuration
#
#####################################################

# APPNAME: a variable used to print the program name in debug messages
APPNAME=$(basename $0)

# DST_PATH: the output folder
DST_PATH=/mnt/d/work/witoilglobal/interpolation_tests/

# WORK_PATH: the work and output directory
WORK_BASE_PATH="/mnt/d/work/witoilglobal/"
WORK_PATH="$WORK_BASE_PATH/currents_workdir/tmp"
WORK_OUTPATH="$WORK_BASE_PATH/currents_workdir/tmp"
WORK_INPATH="$WORK_BASE_PATH/currents_workdir/tmp"

# PROD_DATE: the production date
PROD_DATE=$(date -d "2020-11-26" +%Y%m%d)

# MOVE: 1 if data should be moved to the DST_PATH
MOVE=1

# load .bashrc
#source $HOME/.bashrc
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
#
rm $WORK_PATH/*.nc
rm $WORK_OUTPATH/*.nc
#####################################################
#
# Download data
#
#####################################################

for D in $(seq 0 1); do

    # set the current date
    CURRDATE=$(date -d "$PROD_DATE +$D days" +"%Y%m%d")
    CURRDATE_SHORT=$(date -d "$PROD_DATE +$D days" +"%y%m%d")
    NEXTDATE=$(date -d "$CURRDATE +1 days" +"%Y%m%d")

    # initialise flag

    FILE1UV=${WORK_PATH}/${PROD_DATE}/${CURRDATE}_h-CMCC--RFVL-BSeas3-BS-b${PROD_DATE}_fc-sv09.00.nc
    FILE2UV=${WORK_PATH}/${PROD_DATE}/${NEXTDATE}_h-CMCC--RFVL-BSeas3-BS-b${PROD_DATE}_fc-sv09.00.nc
    FILE1T=${WORK_PATH}/${PROD_DATE}/${CURRDATE}_h-CMCC--TEMP-BSeas3-BS-b${PROD_DATE}_fc-sv09.00.nc
    FILE2T=${WORK_PATH}/${PROD_DATE}/${NEXTDATE}_h-CMCC--TEMP-BSeas3-BS-b${PROD_DATE}_fc-sv09.00.nc


    # echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Checking presence of necessary files"
    # if [ -e $FILE1UV ] && [ -e $FILE2UV ] && [ -e $FILE1T ] && [ -e $FILE2T ]; then
    #   echo "Original CMCC BlackSea input files missing..."
    #   break
    # fi
    # echo "Good... moving ahead."

    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Removing unused vertical layers"
    if [[ $D = 0 ]]; then
      ncks -d depth,1.018237 -d depth,10.5366 -d depth,29.88564 -d depth,119.8554 $FILE1UV -o ${WORK_PATH}/UV_${CURRDATE}_step0.nc
      ncks -d depth,1.018237 -d depth,10.5366 -d depth,29.88564 -d depth,119.8554 $FILE1T -o ${WORK_PATH}/T_${CURRDATE}_step0.nc
    fi
    ncks -d depth,1.018237 -d depth,10.5366 -d depth,29.88564 -d depth,119.8554 $FILE2UV -o ${WORK_PATH}/UV_${NEXTDATE}_step0.nc
    ncks -d depth,1.018237 -d depth,10.5366 -d depth,29.88564 -d depth,119.8554 $FILE2T -o ${WORK_PATH}/T_${NEXTDATE}_step0.nc
    echo "Removed... moving ahead."
    #
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Merging files in time"
    cdo mergetime ${WORK_PATH}/UV_${CURRDATE}_step0.nc ${WORK_PATH}/UV_${NEXTDATE}_step0.nc ${WORK_PATH}/UV_${CURRDATE}_step1.nc
    cdo mergetime ${WORK_PATH}/T_${CURRDATE}_step0.nc ${WORK_PATH}/T_${NEXTDATE}_step0.nc ${WORK_PATH}/T_${CURRDATE}_step1.nc
    echo "Merged... moving ahead."


    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Splitting among variables"
    cp ${WORK_PATH}/UV_${CURRDATE}_step1.nc ${WORK_PATH}/${CURRDATE}_step1_U.nc
    mv ${WORK_PATH}/UV_${CURRDATE}_step1.nc ${WORK_PATH}/${CURRDATE}_step1_V.nc
    mv ${WORK_PATH}/T_${CURRDATE}_step1.nc ${WORK_PATH}/${CURRDATE}_step1_T.nc
    #
    # remove useless variables
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Removing unused variables"
    ncks -O -x -v bottomT ${WORK_PATH}/${CURRDATE}_step1_T.nc ${WORK_PATH}/${CURRDATE}_step1_T.nc
    ncks -O -x -v vo ${WORK_PATH}/${CURRDATE}_step1_U.nc ${WORK_PATH}/${CURRDATE}_step1_U.nc
    ncks -O -x -v uo ${WORK_PATH}/${CURRDATE}_step1_V.nc ${WORK_PATH}/${CURRDATE}_step1_V.nc
    #
    # convert to nc3
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Converting to netcdf3"
    ncks -3 ${WORK_PATH}/${CURRDATE}_step1_T.nc ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc
    ncks -3 ${WORK_PATH}/${CURRDATE}_step1_U.nc ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc
    ncks -3 ${WORK_PATH}/${CURRDATE}_step1_V.nc ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc
    #
    # rename variables
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Renaming variables"
    sleep 2
    ncrename -O -d lon,nav_lon -d lat,nav_lat -v lon,nav_lon -v lat,nav_lat -v time,time_counter -d time,time_counter -v thetao,votemper -d depth,deptht ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc
    ncrename -O -d lon,nav_lon -d lat,nav_lat -v lon,nav_lon -v lat,nav_lat -v time,time_counter -d time,time_counter -v uo,vozocrtx -d depth,depthu ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc
    ncrename -O -d lon,nav_lon -d lat,nav_lat -v lon,nav_lon -v lat,nav_lat -v time,time_counter -d time,time_counter -v vo,vomecrty -d depth,depthv ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc

    # back to nc4
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Back to netcdf4"
    sleep 2
    ncks -4 ${WORK_PATH}/${CURRDATE}_step1_T_v3.nc ${WORK_PATH}/${CURRDATE}_step1_T_v4.nc
    ncks -4 ${WORK_PATH}/${CURRDATE}_step1_U_v3.nc ${WORK_PATH}/${CURRDATE}_step1_U_v4.nc
    ncks -4 ${WORK_PATH}/${CURRDATE}_step1_V_v3.nc ${WORK_PATH}/${CURRDATE}_step1_V_v4.nc

    # interpolate
    echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Interpolating"
    python witoil_interp_med.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_T_v4.nc ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_T.nc
    python witoil_interp_med.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_U_v4.nc ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_U.nc
    python witoil_interp_med.py $CURRDATE ${WORK_PATH}/${CURRDATE}_step1_V_v4.nc ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_V.nc

    # # move files in the final directory
    # if [[ $MOVE = 1 ]]; then
    #     echo "[$APPNAME][$CURRDATE][$(date +"%H:%M")] Moving files to final directory"
    #     mv ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_T.nc ${DST_PATH}/
    #     mv ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_U.nc ${DST_PATH}/
    #     mv ${WORK_OUTPATH}/FULL_MDK_ocean_${CURRDATE_SHORT}_V.nc ${DST_PATH}/
    # fi
done
