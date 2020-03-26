# Houston Flood Early Warning System (FEWS)
A repository for automation of flood early warning system for Houston



## Key Components:

1.	Satellite based nowcast precipitation from IMERG (0.1˚)

2.	Forecast precipitation from GFS, downscaled using WRF model to 0.1˚

3.	Hydrological Modeling – SWAT model (input forcings from IMERG and WRF-based precipitation)

4.	HEC RAS 2D Simulation (boundary conditions from SWAT output flows and IMERG + WRF precipitation)

## Details:

### WRF Setup

*	The namelist configuration files (containing WRF domain and nesting info) are shared in `WRF/` folder

*	WRF v4.1.2 was used for simulation

*	The automation script, calling WPS and WRF programs is also shared in `WRF/` folder


### HEC RAS 2D

*	Uses boundary conditions at four locations: 3 upstream inflow, 1 downstream outflow and precipitation over the catchment

*	Lidar DEM of 1m resolution used for defining the terrain 

*	Shapefiles for boundary conditions (`bc1.shp`) and RAS domain (`flowarea2d_merged.shp`) are shared on Github repository in `HEC_RAS/RAS_Model/` folder

*	Script automating the SWAT and RAS models along with post-processing the RAS outputs is shared at `HEC_RAS/Automate_SWAT_RAS.py` 




For more details, refer to the [documentation] (https://github.com/shahryaramd/HoustonFEWS/blob/master/Documentation-Houston%20Flood%20Inundation%20Forecasting%20System.docx)

