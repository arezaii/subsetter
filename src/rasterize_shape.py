from src.shapefile_utils import ShapefileRasterizer
from src.argparse_utils import is_valid_file, is_valid_path, is_positive_integer
import argparse
import sys
import gdal
import logging
from datetime import datetime


def parse_args(args):
    parser = argparse.ArgumentParser('Generate a Raster From a Shapefile')

    parser.add_argument("--shapefile", "-s", dest="shapefile", required=True,
                        type=lambda x: is_valid_file(parser, x),
                        help="the input shapefile")

    parser.add_argument("--ref_file", "-r", dest="ref_file", required=True,
                        type=lambda x: is_valid_file(parser, x),
                        help="the reference tif to reproject to")

    parser.add_argument("--out_dir", "-o", dest="out_dir", required=False,
                        default='.',
                        help="the directory to write outputs to",
                        type=lambda x: is_valid_path(parser, x))

    parser.add_argument("--side_multiple", "-m", dest="side_multiple", required=False,
                        default=1,
                        help="integer multiple for bounding box side",
                        type=lambda x: is_positive_integer(parser, x))

    return parser.parse_args(args)


def main():
    # setup logging
    start_date = datetime.utcnow()
    logging.basicConfig(filename='rasterize_shape.log', filemode='w', level=logging.INFO)
    logging.info(f'start process at {start_date} from command {" ".join(sys.argv[:])}')
    args = parse_args(sys.argv[1:])
    reference_dataset = gdal.Open(args.ref_file)
    rasterizer = ShapefileRasterizer(shapefile_path=args.shapefile,
                                     reference_dataset=reference_dataset,
                                     output_path=args.out_dir)
    rasterizer.rasterize_shapefile_to_disk(args.out_dir, args.side_multiple)
    end_date = datetime.utcnow()
    logging.info(f'finish process at {end_date} for a runtime of {end_date-start_date}')


if __name__ == '__main__':
    main()

