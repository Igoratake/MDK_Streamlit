DIR_EXE=/scratch/work/MDK_Streamlit/MEDSLIK_II_2.02/RUN
DIR_SRC=$DIR_EXE/MODEL_SRC

gfortran  -I/usr/include -L/usr/lib  $DIR_SRC/Extract_II.for -lnetcdf -lnetcdff -o $DIR_EXE/Extract_II.exe
gfortran -o $DIR_EXE/jday $DIR_SRC/jday.f
gfortran  -I/usr/include -L/usr/lib -fno-align-commons $DIR_SRC/medslik_II.for -lnetcdf -lnetcdff -o $DIR_EXE/medslik_II.exe
gfortran -o $DIR_EXE/lat_lon.exe $DIR_SRC/lat_lon.for
