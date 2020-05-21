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
* [pfio-tools](https://github.com/hydroframe/tools)

## Setup
```
git clone https://github.com/arezaii/subsetter
cd subsetter
conda env create -f=environment.yml
conda activate pf_subsetter
git clone https://github.com/smithsg84/pf-mask-utilities.git
cd pf-mask-utilities
make
cd ..
git clone https://github.com/hydroframe/tools
cd tools/pfio
python setup.py install
cd ../..
```

## Testing
```
chmod +x run_tests.sh
./run_tests.sh [cyverse_account] [cyverse_password]
```

## Usage

**rasterize a shapefile for use as a mask, based on a reference dataset**
```
python src/rasterize_shape.py -s <shapefile> -r <reference_dataset> -o [output_dir=.]
```

**create subset from CONUS models from a shapefile**
```
python src/subset_conus.py -s <shapefile> -v -c <path to conus input files> [conus version=1]  -o [path_to_write_outputs=.]
```

**use a tif mask to clip multiple files to PFB or TIF**

assumes all files are identically gridded and same as the mask file
```
python src/bulk_clipper.py -m <mask_file> -d <list_of_datafiles_to_clip> -t [write_tifs=0] -o [output_directory=.]
```

