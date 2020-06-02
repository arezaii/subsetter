import argparse
import logging
import os
import sys
from pathlib import Path
from src.argparse_utils import is_valid_path, is_positive_integer
from src.clipper import Clipper
from src.conus import Conus
from src.shapefile_utils import ShapefileRasterizer
from datetime import datetime
import src.bulk_clipper as bulk_clipper
import src.solidfile_generator as solidfile_generator
from src.tcl_builder import build_tcl
from src.clm_utils import ClmClipper


def parse_args(args):
    parser = argparse.ArgumentParser('Subset a ParFlow CONUS domain')

    parser.add_argument("--input_path", "-i", dest="input_path", required=True,
                        type=lambda x: is_valid_path(parser, x),
                        help="the input path to the shapefile file set")

    parser.add_argument("--shapefile", "-s", dest="shapefile", required=True,
                        help="the name of the shapefile file set")

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


def main():
    # setup logging
    start_date = datetime.utcnow()
    logging.basicConfig(filename='subset_conus.log', filemode='w', level=logging.INFO)
    logging.info(f'start process at {start_date} from command {" ".join(sys.argv[:])}')
    # parse the command line arguments
    args = parse_args(sys.argv[1:])
    conus = Conus(version=args.conus_version, local_path=args.conus_files)

    # Step 1, rasterize shapefile

    rasterizer = ShapefileRasterizer(args.input_path, args.shapefile, reference_dataset=conus.conus_mask_tif,
                                     no_data=-999, output_path=args.out_dir)
    shape_raster_array = rasterizer.rasterize_shapefile_to_disk(out_name='WBDHU8_raster_from_shapefile.tif',
                                                                side_multiple=32)

    # Step 2, Generate solid file
    clip = Clipper(shape_raster_array, conus.conus_mask_tif, no_data_threshold=-1)
    batches = solidfile_generator.make_solid_file(clipped_mask=clip.clipped_mask,
                                                  out_name=os.path.join(args.out_dir, rasterizer.shapefile_name))
    if len(batches) == 0:
        raise Exception("Did not make solid file correctly")

    # Step 3. Clip all the domain data inputs
    bulk_clipper.clip_inputs(clip,
                             [os.path.join(conus.local_path, value) for key, value in conus.files.items()
                              if key not in ['CONUS_MASK', 'CHANNELS']],
                             out_dir=args.out_dir, tif_outs=1)

    # Step 4. Clip CLM inputs

    clm_clipper = ClmClipper(shape_raster_array, conus.conus_mask_tif)
    latlon_formatted, latlon_data = clm_clipper.clip_latlon(os.path.join(conus.local_path, conus.clm.get('LAT_LON')))
    clm_clipper.write_lat_lon(latlon_formatted, os.path.join(args.out_dir, 'WBDHU8_latlon_test.sa'),
                              x=latlon_data.shape[2], y=latlon_data.shape[1], z=latlon_data.shape[0])

    land_cover_data, vegm_data = clm_clipper.clip_land_cover(lat_lon_array=latlon_formatted,
                                                             land_cover_file=os.path.join(conus.local_path,conus.clm.get('LAND_COVER')))

    clm_clipper.write_land_cover(vegm_data, 'WBDHU8_vegm_test.dat')

    # Step 5. Generate TCL File
    # TODO: Fix the arguments
    os.path.join(args.out_dir, 'runname.tcl')
    build_tcl(os.path.join(args.out_dir, 'runname.tcl'),
              'parking_lot_template.tcl',
              'runname',
              os.path.join(args.out_dir, f'{Path(conus.files.get("SLOPE_X")).stem}_clip.pfb'),
              os.path.join(args.out_dir, 'WBDHU8.pfsol'),
              os.path.join(args.out_dir, 'pme.pfb'), end_time=10, batches=batches,
              p=2, q=1, r=1, timestep=1)

    end_date = datetime.utcnow()
    logging.info(f'completed process at {end_date} for a runtime of {end_date-start_date}')


if __name__ == '__main__':
    main()
