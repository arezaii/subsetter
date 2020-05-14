import argparse
import logging
import os
import sys
from argparse_utils import is_valid_path, is_positive_integer, is_valid_file
import gdal
import file_io_tools
import tcl_builder
from clipper import Clipper
from conus import Conus
from conus_sources import CyVerseDownloader
from shapefile_utils import ShapefileRasterizer


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
    # setup logging
    logging.basicConfig(filename='subset.log', filemode='w', level=logging.INFO)
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

    shape_utils = ShapefileRasterizer(args.shapefile)
    conus_mask = file_io_tools.read_file(os.path.join(conus.local_path, conus.files.get("CONUS_MASK")))
    # having to add 1 to this CONUS1 mask file so that it has non-zero data.
    if conus.version == 1:
        conus_mask += 1
    # end
    conus_tif = gdal.Open(os.path.join(conus.local_path, conus.files.get("CONUS_MASK")))
    mem_raster_path = shape_utils.reproject_and_mask(conus_tif)
    shape_raster_array = file_io_tools.read_file(mem_raster_path)
    clip = Clipper()
    # TODO: Why this get_mask_array call? To convert from no_data=-999 mask to 0 and 1's mask for the
    mask_array = clip.get_mask_array(shape_raster_array)
    # TODO: Why do we need to subset conus mask? We already have the mask, right?
    # This is getting back our bounding box and converting to a 32x32 grid?
    return_arr, new_geom, new_mask, bbox = clip.subset(conus_mask, mask_array, conus_tif, no_data=0.0)
    # TODO: Move this out of here, assume installed?
    # Download and install pf-mask-utilities
    if not os.path.isdir('pf-mask-utilities'):
        os.system('git clone https://github.com/smithsg84/pf-mask-utilities.git')
        os.chdir('pf-mask-utilities')
        os.system('make')
        os.chdir('..')
    batches = clip.make_solid_file(return_arr, os.path.join(args.out_dir, shape_utils.shapefile_name))
    if len(batches) == 0:
        raise Exception("Did not make solid file correctly")
    for key, value in conus.files.items():
        if key not in ['CONUS_MASK', 'CHANNELS']:
            domain_file = file_io_tools.read_file(os.path.join(conus.local_path, value))
            return_arr1, new_geom1, new_mask1, bbox1 = clip.subset(domain_file, shape_raster_array, conus_tif)
            file_io_tools.write_pfb(return_arr1, os.path.join(args.out_dir, f'{key.lower()}.pfb'), 0, 0, 0, 1000, 1000)
            file_io_tools.write_array_to_geotiff(os.path.join(args.out_dir, f'{key.lower()}.tif'), return_arr1,
                                                 new_geom1, conus_tif.GetProjection())
    file_io_tools.write_bbox(bbox, os.path.join(args.out_dir, 'bbox.txt'))

    # TODO: Fix the arguments
    os.path.join(args.out_dir, 'runname.tcl')
    tcl_builder.build_tcl(os.path.join(args.out_dir, 'runname.tcl'),
                          'parking_lot_template.tcl',
                          'runname',
                          os.path.join(args.out_dir, 'slope_x.pfb'),
                          os.path.join(args.out_dir, 'WBDHU8.pfsol'),
                          os.path.join(args.out_dir, 'pme.pfb'), end_time=10, batches=batches,
                          p=2, q=1, r=1, timestep=1)


if __name__ == '__main__':
    main()
