# Subsetter
[![Build Status](https://travis-ci.com/arezaii/subsetter.svg?branch=master)](https://travis-ci.com/arezaii/subsetter)
## Prerequisites
To build solid files, one of the following tools is required:
pfmask-to-pfsol (included of ParFlow) 
or
[mask-to-pfsol](https://github.com/smithsg84/pf-mask-utilities.git)

For the solidfile generator to work, it must be able to locate one of the above tools.
The generator will search the following places, in this order.
* PFMASKUTILS environment variable
* mask-to-pfsol directory in PATH variable
* PARFLOW_DIR environment variable 
* ParFlow bin directory in PATH variable


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
python setup.py install
cd ../..
```

## Testing
```
chmod +x run_tests.sh
./run_tests.sh
```

## Usage

#### Rasterize a shapefile for use as a mask, based on a reference dataset
```
python -m src.rasterize_shape -i <path to shapefile parts> -s <shapefile name> -r <reference_dataset> -o [output_dir=.] -f [output filename] -s [pad to side multiple] -n [shapefile attribute name] -a [shapefile attribute values]
```

#### Create subset from CONUS models from a shapefile
```
python -m src.subset_conus -i <path to shapefile parts> -s <shapefile name> -c <path to conus input files>  -v [conus verson=1] -o [path_to_write_outputs=.]
```

#### Use a mask to clip multiple files to PFB or TIF

assumes all files are identically gridded and same as the mask file, if write_tifs=1 then you
must supply at least one tif with correct projection and transform information as either the mask file, 
as a reference dataset with the -r option, or in the list of datafiles to clip
```
python src.bulk_clipper -m <mask_file> -d <list_of_datafiles_to_clip> -t [write_tifs=0] -o [output_directory=.]
```

