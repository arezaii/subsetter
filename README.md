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

rasterize a shapefile for use as a mask, based on a reference dataset
`rasterize_shape.py -s <shapefile> -r <reference_dataset> -o [output_dir]`




