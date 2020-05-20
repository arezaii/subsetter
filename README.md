# Subsetter

## Prerequisites

### CyVerse account 
* access to avra

### Environment
* miniconda or anaconda
* CYVERSE_USERNAME environment variable set
* CYVERSE_PASSWORD environment variable set

### Packages
* [pf-mask-utilities](https://github.com/smithsg84/pf-mask-utilities.git)
* pfio-tools

## Setup
`conda env create -f=environment.yml`

## Testing
`run_tests.sh`

## Usage

**rasterize a shapefile for use as a mask, based on a reference dataset**
```
python rasterize_shape.py -s <shapefile> -r <reference_dataset> -o [output_dir=.]
```

**create subset from CONUS models from a shapefile**
```
python subset_conus.py -s <shapefile> -v -c <path to conus input files> [conus version=1]  -o [path_to_write_outputs=.]
```

**use a tif mask to clip multiple files to PFB or TIF**

assumes all files are identically gridded and same as the mask file
```
python bulk_clipper.py -m <mask_file> -d <list_of_datafiles_to_clip> -t [write_tifs=0] -o [output_directory=.]
```

