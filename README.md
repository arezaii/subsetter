# Subsetter
[![Build Status](http://travis-ci.com/arezaii/subsetter.svg?branch=master)](http://travis-ci.com/arezaii/subsetter)
## Prerequisites
To build solid files, one of the following tools is required:
pfmask-to-pfsol (included of ParFlow) 
or
[mask-to-pfsol](https://github.com/smithsg84/pf-mask-utilities.git)

*If using mask-to-pfsol, be sure to follow [instructions](https://github.com/smithsg84/pf-mask-utilities.git) for building the utilities.*

For the solidfile generator to work, it must be able to locate one of the above tools.
The generator will search the following places, in this order.
1. PFMASKUTILS environment variable
2. mask-to-pfsol directory in PATH variable
3. PARFLOW_DIR environment variable 
4. ParFlow bin directory in PATH variable


### Environment
* miniconda or anaconda
* CONUS1 and or CONUS2 source files for clipping

### Packages
* [pfio-tools](https://github.com/hydroframe/tools)


## Setup

```
git clone https://github.com/arezaii/subsetter
cd subsetter
conda env create -f=environment.yml
conda activate pf_subsetter
git clone https://github.com/hydroframe/tools
cd tools/pfio
pip install .
cd ../..
```

## Input Files

For CONUS 1 and 2 models, input files are required. 

#### CONUS 1 Required files

Domain Files:

* CONUS_MASK: Domain_Blank_Mask.tif
* SUBSURFACE_DATA: grid3d.v3.pfb
* PME: PmE.flux.pfb
* SLOPE_X: slopex.pfb
* SLOPE_Y: slopey.pfb
* DEM: CONUS2.0_RawDEM_CONUS1clip.tif

CLM Files:
* LAND_COVER: conus1_landcover.sa
* LAT_LON: conus1_Grid_Centers_Short_Deg.format.sa

#### CONUS 2 Required files

* CONUS_MASK: conus_1km_PFmask2.tif
* SUBSURFACE_DATA: 3d-grid.v3.tif
* PME: PME.tif
* SLOPE_X: Str3Ep0_smth.rvth_1500.mx0.5.mn5.sec0.up_slopex.tif
* SLOPE_Y: Str3Ep0_smth.rvth_1500.mx0.5.mn5.sec0.up_slopey.tif
* SINKS: conus_1km_PFmask_manualsinks.tif
* RESERVOIRS: conus_1km_PFmask_reservoirs.tif
* LAKE_BORDER: conus_1km_PFmask_selectLakesborder.tif
* LAKE_MASK: conus_1km_PFmask_selectLakesmask.tif
* CHANNELS: 1km_upscaledNWM_ChannelOrder5_mod2.tif
* CELL_TYPES: 1km_PF_BorderCellType.tif
* DEM: CONUS2.0_RawDEM.tif

CLM Files:
* LAND_COVER: 1km_CONUS2_landcover_IGBP.tif
* LAT_LON: latlonCONUS2.sa

## Testing

Run these tests to do some basic checks to make sure the tools are working correctly after install or update.

```
chmod +x run_tests.sh
./run_tests.sh
```

## Usage


#### Create subset from CONUS models from a shapefile
```
python -m src.subset_conus -i <path_to_shapefile_parts> -s <shapefile_name> -f <path_to_conus_input_files> 
                            -n [name_for_output_files=shapfile_name] 
                            -v [conus_verson=1] 
                            -o [path_to_write_outputs=.] 
                            -c [clip_clm=0]
                            -w [write_tcl=0]
                            -m [side_length_multiple=1]
                            -e [shapefile_attribute_name='OBJECTID']
                            -a [shapefile_attribute_ids=[1]]
                            -t [tif_outs=0]

```
example usage:

Create a subset of the CONUS1 domain with CLM inputs based on the shapefile at ~/downloads/shapfiles/WBDHU8.shp and write the .tcl file to run the model
```
python -m src.subset_conus -i ~/downloads/shapefiles -s WBDHU8 -f ~/downloads/conus1 -c 1 -w 1 -n watershedA_conus1_clip
```

#### Rasterize a shapefile for use as a mask, based on a reference dataset
```
python -m src.rasterize_shape -i <path_to_shapefile_parts> -s <shapefile_name> -r <reference_dataset> 
                              -o [path_to_write_outputs=.] 
                              -n [output_filename=shapfile_name] 
                              -m [side_length_multiple=1] 
                              -e [shapefile_attribute_name='OBJECTID'] 
                              -a [shapefile_attribute_ids=[1]]
```


example usage:

Reproject the shapefile at ~/downloads/shapfiles/WBDHU8.shp to the CONUS1 projection and extent
```
python -m src.rasterize_shape -i ~/downloads/shapefiles -s WBDHU8
```


#### Use a mask to clip multiple files to PFB or TIF

assumes all files are identically gridded and same as the mask file, if write_tifs=1 then you
must supply at least one tif with correct projection and transform information as either the mask file, 
as a reference dataset with the -r option, or in the list of datafiles to clip
```
python -m src.bulk_clipper -m <mask_file> -d <list_of_datafiles_to_clip> 
                           -t [write_tifs=0] 
                           -o [output_directory=.]
```
example usage:

Clip the model outputs to the bounds of a mask generated from rasterize_shape or subset_conus
```
python -m src.bulk_clipper -m ~/outputs/WBDHU8.tif -d ~/outputs/runname.out.press.00001.pfb ~/outputs/runname.out.press.00002.pfb
```

### Optional Arguments Explanation

Many optional arguments are available for the subset_conus and rasterize_shape. Below is an explanationo of the options.
```
-n [name for output files=shapfile_name] The name to give the output raster, defaults to shapefile name
-v [conus verson=1] The version of the ParFlow CONUS model to subset from (1 or 2), defaults to version 1
-o [path_to_write_outputs=.] The path to write the output files, defaults to current directory
-c [clip_clim=0] Whether or not to clip the CLM lat/lon and vegm data. Defaults to False.
-w [write_tcl=0] Whether or not to write the .tcl file to run the ParFlow model. Defaults to False
-m [side_length_multiple=1] Add padding to side lengths of outputs. 1=no pad, 2= even length sides. Default 1 
-e [shapefile_attribute_name='OBJECTID'] The name of the attribute table column to uniquely ID objects. Default 'OBJECTID' 
-a [shapefile_attribute_ids=[1]] The list of objects in the shapefile to rasterize. Default [1]
-t [tif_outs=0] Whether or not to write outputs as .tif files. Defaults to False.
```