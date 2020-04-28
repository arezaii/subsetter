import sys
from pathlib import Path
import pfio
import gdal
from shapefile_utils import ShapefileUtilities
import argparse
import os
from conus import Conus
from conus_sources import CyVerseDownloader
import file_reader
from clipper import Clipper


def is_valid_file(parser, arg):
    if not os.path.isfile(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')  # return open file handle


def is_positive_integer(parser, arg):
    ivalue = int(arg)
    if ivalue <= 0:
        raise parser.ArgumentTypeError("%s is an invalid positive int value" % arg)
    else:
        return ivalue


def is_valid_path(parser, arg):
    if not os.path.isdir(arg):
        parser.error("The path %s does not exist!" % arg)
    else:
        return arg  # return the arg


def parse_args(args):
    parser = argparse.ArgumentParser('Subset a ParFlow CONUS domain')

    parser.add_argument("--shapefile", "-s", dest="shapefile", required=True,
                        type=lambda x: is_valid_file(parser, x),
                        help="the input shapefile")

    parser.add_argument("--version", "-v", dest="conus_version", required=False,
                        default=1,
                        type=lambda x: is_positive_integer(parser, x),
                        help="the version of CONUS to subset from")

    parser.add_argument("--conus_files", "-c", dest="conus_files", required=False,
                        default='CONUS1_Inputs',
                        help="local path to the CONUS inputs to subset",
                        type=lambda x: is_valid_path(parser, x))

    parser.add_argument("--out_dir", "-o", dest="out_dir", required=False,
                        default='.',
                        help="the directory to write outputs to",
                        type=lambda x: is_valid_path(parser, x))

    return parser.parse_args(args)


def check_missing_conus_inputs(conus):
    missing_inputs = conus.check_inputs_exist()
    if len(missing_inputs) > 0:
        print(f'Missing required CONUS inputs: {missing_inputs}')
    return missing_inputs


def download_conus_inputs(conus, missing_files):
    downloader = CyVerseDownloader(dest=conus.local_path)
    for file in missing_files:
        downloader.get_conus_data(f'{conus.cyverse_path}{file}')


def main():
    # parse the command line arguments
    args = parse_args(sys.argv[1:])
    conus = Conus(args.conus_version, args.conus_files)
    missing_files = check_missing_conus_inputs(conus)
    # TODO: don't download inputs for the user, just tell them to go get the inputs or tell us where they live
    if len(missing_files) > 0:
        print("attempting to download missing inputs from cyverse")
        download_conus_inputs(conus, missing_files)
    if len(check_missing_conus_inputs(conus)) > 0:
        print("could not download all conus inputs")
        exit(1)
    else:
        print("located all CONUS inputs")

    shape_utils = ShapefileUtilities()
    conus_mask = file_reader.read_file(os.path.join(conus.local_path, conus.files.get("CONUS_MASK")))
    # TODO: why is this in the original code? Because it doesn't work without it
    conus_mask += 1
    # end
    conus_tif = gdal.Open(os.path.join(conus.local_path, conus.files.get("CONUS_MASK")))
    mem_raster_path = shape_utils.reproject(args.shapefile.name, conus_tif)
    shape_raster_array = file_reader.read_file(mem_raster_path)
    clip = Clipper()
    mask_array = clip.get_mask_array(shape_raster_array)
    return_arr, new_geom, bbox = clip.subset(conus_mask, mask_array, conus_tif)
    # TODO: Move this out of here, assume installed?
    # Download and install pf-mask-utilities
    if not os.path.isdir('pf-mask-utilities'):
        os.system('git clone https://github.com/smithsg84/pf-mask-utilities.git')
        os.chdir('pf-mask-utilities')
        os.system('make')
        os.chdir('..')
    clip.make_solid_file(return_arr, os.path.join(args.out_dir, Path(args.shapefile.name).stem))
    for key, value in conus.files.items():
        if key != 'CONUS_MASK':
            domain_file = file_reader.read_file(os.path.join(conus.local_path, value))
            return_arr1, new_geom1, bbox1 = clip.subset(domain_file, mask_array, conus_tif)
            # TODO: option to write tif instead of pfb
            # TODO: change 0's to x0, y0, z0
            # TODO: change 1000 to dx, dy=dx, dz
            pfio.pfwrite(return_arr1, os.path.join(args.out_dir, f'{key.lower()}.pfb'),
                         float(0), float(0), float(0),
                         float(1000), float(1000), float(1000))
    # TODO: save this bounding box data to a file
    print(bbox)


if __name__ == '__main__':
    main()
