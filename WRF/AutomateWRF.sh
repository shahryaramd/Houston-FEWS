#!/bin/bash

export DIR=/home/skahmad/WRF/Build_WRF/LIBRARIES
export LD_LIBRARY_PATH=${DIR}/grib2/lib:$LD_LIBRARY_PATH
export PATH=$DIR/mpich/bin:$PATH
export PATH=$DIR/netcdf/bin:$PATH

nn=$1

#clear system for WRF Downscaling

cd /home/skahmad/WRF/Build_WRF/DATA
rm gfs*

echo "Downloading GFS Data..."
lead=4



i=$(date +"%Y" -d "$nn days ago")	 ## "today")			## Year
j=$(date +"%m" -d "$nn days ago")	 ## "today")			## Month
k=$(date +"%d" -d "$nn days ago")	 ##"today")			## Day
#i=2019
#j=08
#k=31
j=$((10#$j)) # converting to decimal form octal in case of 08 or 09
k=$((10#$k))

echo $i-$(printf %02d $j)-$(printf %02d $k)_00:00:00
# GFS Forecast data processing
for l in $(seq -f "%03g" 0 12 $((24*$lead)))		## GFS Forecast hour
	do
		#~ ## Real-time
	file=gfs.t00z.pgrb2.0p25.f$l  
	wget ftp://ftp.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.$i$(printf %02d $j)$(printf %02d $k)/00/$file
done

##RUN WPS 
echo "Running WPS"
cd /home/skahmad/WRF/Build_WRF/WPS/
rm FILE:*
rm met_em.d0*
./geogrid.exe >& log.geogrid
./link_grib.csh /home/skahmad/WRF/Build_WRF/DATA/
ln -sf ungrib/Variable_Tables/Vtable.GFS Vtable
./ungrib.exe 
./metgrid.exe >& log.metgrid

#RUN WRF
echo "Running WRF"
cd ../WRF/run
rm met_em.d0*
rm wrfout_d0*
rm wrfrst_d0*
ln -sf ../../WPS/met_em* . 
mpirun -np 30 ./real.exe
tail rsl.error.0000
mpirun -np 30 ./wrf.exe
tail rsl.error.0000
