# Subsetter

## Prerequisites

### Environment
* miniconda or anaconda
* CONUS1 and or CONUS2 source files for clipping

### Packages
* [pfio-tools](https://github.com/hydroframe/tools)
* pfmask-to-pfsol or mask-to-pfsol 

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
python -m src.rasterize_shape -i <path to shapefile parts> -s <shapefile name> -r <reference_dataset> -o [output_dir=.]
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

