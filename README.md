[![Build Status](http://travis-ci.com/arezaii/subsetter.svg?branch=master)](http://travis-ci.com/arezaii/subsetter)

# Subsetter
The pf_subsetter is a suite of tools for clipping ParFlow inputs and outputs. Included are command
line scripts to: 

1. subset the inputs from CONUS1 or CONUS2 domains [subset_conus](#Use_a_mask_to_clip_multiple_files_to_PFB_or_TIF)
2. generate a rasterized mask from a shapefile [rasterize_shape](#Create_subset_from_CONUS_models_from_a_shapefile)
3. clip data from any number of supported input files [bulk_clip](#Rasterize_a_shapefile_for_use_as_a_mask)


## Prerequisites

### Packages
* [parflowio](https://github.com/hydroframe/parflowio)
* [gdal](https://gdal.org/download.html)
* [numpy](https://numpy.org/install/)
* [pyyaml](https://pypi.org/project/PyYAML/)
* [pandas](https://pandas.pydata.org/)


#### Building Solid Files

To build solid files (.pfsol), one of the following tools is required:
`pfmask-to-pfsol` (included with ParFlow) 
or
[mask-to-pfsol](https://github.com/smithsg84/pf-mask-utilities.git)

*If using `mask-to-pfsol`, be sure to follow [instructions](https://github.com/smithsg84/pf-mask-utilities.git) for building the utilities.*

##### Environment Variables

For the solidfile generator to work, it must be able to locate either `mask-to-pfsol` or `pfmask-to-pfsol`

The generator will search the following places, in this order.
1. PFMASKUTILS environment variable
2. *mask-to-pfsol* directory in PATH variable
3. PARFLOW_DIR environment variable 
4. ParFlow *bin* directory in PATH variable


## Setup

Create a clean environment using anaconda or miniconda:

```
git clone https://github.com/arezaii/subsetter
cd subsetter
conda env create -f=environment.yml
conda activate pf_subsetter
```

## Input Files

For CONUS1 and CONUS2 domains, local copies of model input files are required.  

#### CONUS1 Files

    required_files:
      DOMAIN_MASK: Domain_Blank_Mask.tif
      SUBSURFACE_DATA: grid3d.v3.pfb
      PME: PmE.flux.pfb
      SLOPE_X: slopex.pfb
      SLOPE_Y: slopey.pfb
    optional_files:
      LAND_COVER: conus1_landcover.sa
      LAT_LON: conus1_Grid_Centers_Short_Deg.format.sa
      DEM: CONUS2.0_RawDEM_CONUS1clip.tif

#### CONUS2 Files

    required_files:
      DOMAIN_MASK: conus_1km_PFmask2.tif
      SUBSURFACE_DATA: 3d-grid.v3.tif
      PME: PME.tif
      SLOPE_X: Str3Ep0_smth.rvth_1500.mx0.5.mn5.sec0.up_slopex.tif
      SLOPE_Y: Str3Ep0_smth.rvth_1500.mx0.5.mn5.sec0.up_slopey.tif
      SINKS: conus_1km_PFmask_manualsinks.tif
      RESERVOIRS: conus_1km_PFmask_reservoirs.tif
      LAKE_BORDER: conus_1km_PFmask_selectLakesborder.tif
      LAKE_MASK: conus_1km_PFmask_selectLakesmask.tif
      CHANNELS: 1km_upscaledNWM_ChannelOrder5_mod2.tif
      CELL_TYPES: 1km_PF_BorderCellType.tif
    optional_files:
      LAND_COVER: 1km_CONUS2_landcover_IGBP.tif
      LAT_LON: latlonCONUS2.sa
      DEM: CONUS2.0_RawDEM.tif

**Local Filenames**

If your local filenames differ from this list, update the local filenames in:

`pf_subsetter/data/conus_manifest.yaml`
 


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
                            -x [padding for left and right=0]
                            -y [padding on top and bottom=0]
                            -e [shapefile_attribute_name='OBJECTID']
                            -a [shapefile_attribute_ids=[1]]
                            -t [tif_outs=0]

```
**Example usage:**

Create a subset of the CONUS1 domain with CLM inputs based on the shapefile at ~/downloads/shapfiles/WBDHU8.shp and write the .tcl file to run the model
```
python -m src.subset_conus -i ~/downloads/shapefiles -s WBDHU8 -f ~/downloads/conus1 -c 1 -w 1 -n watershedA_conus1_clip
```

#### Rasterize a shapefile for use as a mask
```
python -m src.rasterize_shape -i <path_to_shapefile_parts> -s <shapefile_name> -r <reference_dataset> 
                              -o [path_to_write_outputs=.] 
                              -n [output_filename=shapfile_name] 
                              -x [padding for left and right=0]
                              -y [padding on top and bottom=0]
                              -e [shapefile_attribute_name='OBJECTID'] 
                              -a [shapefile_attribute_ids=[1]]
```


**Example usage:**

Reproject the shapefile at ~/downloads/shapfiles/WBDHU8.shp to the CONUS1 projection and extent
```
python -m src.rasterize_shape -i ~/downloads/shapefiles -s WBDHU8
```


#### Use a mask to clip multiple files to PFB or TIF

assumes all files are identically gridded and same as the mask file, if write_tifs=1 then you
must supply at least one tif with correct projection and transform information as either the mask file, 
as a reference dataset with the -r option, or in the list of datafiles to clip
```
python -m src.bulk_clipper [-m <mask_file> OR -b <bbox file>] -d <list_of_datafiles_to_clip> 
                           -t [write_tifs=0] 
                           -o [output_directory=.]
```
**Example usage with mask file:**

Clip the domain outputs to the bounds of a mask generated from rasterize_shape or subset_conus
```
python -m src.bulk_clipper -m ~/outputs/WBDHU8.tif -d ~/outputs/runname.out.press.00001.pfb ~/outputs/runname.out.press.00002.pfb
```

**Example usage with bounding box file:**

Clip the domain outputs, starting at x,y, and extending for nx, ny
```
python -m src.bulk_clipper -b ~/outputs/bbox.txt -d ~/outputs/runname.out.press.00001.pfb ~/outputs/runname.out.press.00002.pfb
```
where bbox.txt is a tab-separted text file in the format:

| x   | y   | nx | ny |
|-----|-----|----|----|
| x_1 | y_1 | nx | ny |

Example bbox clipping only the very first (lower left) cell in a domain:

| x   | y   | nx | ny |
|-----|-----|----|----|
| 1 | 1 | 1 | 1 |

### Optional Arguments Explanation

Many optional arguments are available for the subset_conus and rasterize_shape. Below is an explanationo of the options.
```
-n [name for output files=shapfile_name] The name to give the output raster, defaults to shapefile name
-v [conus verson=1] The version of the ParFlow CONUS model to subset from (1 or 2), defaults to version 1
-o [path_to_write_outputs=.] The path to write the output files, defaults to current directory
-c [clip_clim=0] Whether or not to clip the CLM lat/lon and vegm data. Defaults to False.
-w [write_tcl=0] Whether or not to write the .tcl file to run the ParFlow model. Defaults to False
-x [padding for left and right=0] Add padding to side lengths of outputs. 1=no pad, 2= even length sides. Default 1 
-y [padding on top and bottom=0]
-e [shapefile_attribute_name='OBJECTID'] The name of the attribute table column to uniquely ID objects. Default 'OBJECTID' 
-a [shapefile_attribute_ids=[1]] The list of objects in the shapefile to rasterize. Default [1]
-t [tif_outs=0] Whether or not to write outputs as .tif files. Defaults to False.
```


## Supported File Types

1. PFB
2. TIF
3. .sa