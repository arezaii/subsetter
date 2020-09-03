import argparse
import logging
import os
import sys
from pathlib import Path
from utils.arguments import is_valid_path, is_positive_integer
from pf_subsetter.clipper import MaskClipper
from pf_subsetter.domains import Conus
from pf_subsetter.rasterizer import ShapefileRasterizer
from datetime import datetime
import bin.bulk_clipper as bulk_clipper
import builders.solidfile as solidfile_generator
from builders.tcl import build_tcl
from utils.clm import ClmClipper
from pf_subsetter.data import parkinglot_template


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

    parser.add_argument("--conus_files", "-f", dest="conus_files", required=False,
                        default='CONUS1_Inputs',
                        help="local path to the CONUS inputs to subset",
                        type=lambda x: is_valid_path(parser, x))

    parser.add_argument("--out_dir", "-o", dest="out_dir", required=False,
                        default='.',
                        help="the directory to write outputs to",
                        type=lambda x: is_valid_path(parser, x))

    parser.add_argument("--out_name", "-n", dest="out_name", required=False,
                        default=None,
                        help="the name to give the outputs")

    parser.add_argument("--clip_clm", "-c", dest="clip_clm", required=False,
                        default=0,
                        help="also clip inputs for CLM",
                        type=int)

    parser.add_argument("--write_tcl", "-w", dest="write_tcl", required=False,
                        default=0,
                        help="generate the .tcl script for this subset",
                        type=int)

    parser.add_argument("--side_multiple", "-m", dest="side_multiple", required=False,
                        default=1,
                        help="integer multiple for bounding box side",
                        type=lambda x: is_positive_integer(parser, x))

    parser.add_argument("--attribute_ids", "-a", dest="attribute_ids", required=False,
                        default=[1], nargs='+',
                        help="list of attribute ID's to clip",
                        type=lambda x: is_positive_integer(parser, x))

    parser.add_argument("--attribute_name", "-e", dest="attribute_name", required=False,
                        default="OBJECTID",
                        help="name of the attribute field to query for attribute ids",
                        type=str)

    parser.add_argument("--tif_outs", "-t", dest="write_tifs", required=False,
                        default=0,
                        help="write tif output files",
                        type=int)

    return parser.parse_args(args)


def main():
    # setup logging
    start_date = datetime.utcnow()
    logging.basicConfig(filename='subset_conus.log', filemode='w', level=logging.INFO)
    logging.info(f'start process at {start_date} from command {" ".join(sys.argv[:])}')
    # parse the command line arguments
    args = parse_args(sys.argv[1:])
    if args.out_name is None:
        args.out_name = args.shapefile
    conus = Conus(version=args.conus_version, local_path=args.conus_files)


    # Step 1, rasterize shapefile

    rasterizer = ShapefileRasterizer(args.input_path, args.shapefile, reference_dataset=conus.get_domain_tif(),
                                     no_data=-999, output_path=args.out_dir, )
    rasterizer.rasterize_shapefile_to_disk(out_name=f'{args.out_name}_raster_from_shapefile.tif',
                                                                side_multiple=args.side_multiple,
                                                                attribute_name=args.attribute_name,
                                                                attribute_ids=args.attribute_ids)

    subset_mask = rasterizer.subset_mask

    # Step 2, Generate solid file
    clip = MaskClipper(subset_mask, no_data_threshold=-1)
    batches = solidfile_generator.make_solid_file(clipped_mask=clip.clipped_mask,
                                                  out_name=os.path.join(args.out_dir, args.out_name))
    if len(batches) == 0:
        raise Exception("Did not make solid file correctly")

    # Step 3. Clip all the domain data inputs
    bulk_clipper.clip_inputs(clip,
                             [os.path.join(conus.local_path, value) for key, value in conus.required_files.items()
                              if key not in ['DOMAIN_MASK', 'CHANNELS']],
                             out_dir=args.out_dir, tif_outs=args.write_tifs)

    # Step 4. Clip CLM inputs
    if args.clip_clm == 1:
        clm_clipper = ClmClipper(subset_mask)
        latlon_formatted, latlon_data = clm_clipper.clip_latlon(os.path.join(conus.local_path,
                                                                             conus.optional_files.get('LAT_LON')))

        clm_clipper.write_lat_lon(latlon_formatted, os.path.join(args.out_dir, f'{args.out_name}_latlon.sa'),
                                  x=latlon_data.shape[2], y=latlon_data.shape[1], z=latlon_data.shape[0])

        land_cover_data, vegm_data = clm_clipper.clip_land_cover(lat_lon_array=latlon_formatted,
                                                                 land_cover_file=os.path.join(conus.local_path,
                                                                                              conus.optional_files.get('LAND_COVER')))

        clm_clipper.write_land_cover(vegm_data, os.path.join(args.out_dir, f'{args.out_name}_vegm.dat'))

    # Step 5. Generate TCL File
    if args.write_tcl == 1:
        build_tcl(os.path.join(args.out_dir, f'{args.out_name}.tcl'),
                  parkinglot_template,
                  args.out_name,
                  os.path.join(args.out_dir, f'{Path(conus.required_files.get("SLOPE_X")).stem}_clip.pfb'),
                  os.path.join(args.out_dir, f'{args.out_name}.pfsol'),
                  os.path.join(args.out_dir, 'pme.pfb'), end_time=10, batches=batches,
                  p=2, q=1, r=1, timestep=1, constant=1)

    end_date = datetime.utcnow()
    logging.info(f'completed process at {end_date} for a runtime of {end_date-start_date}')


if __name__ == '__main__':
    main()
