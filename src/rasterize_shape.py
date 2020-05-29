from src.shapefile_utils import ShapefileRasterizer
from src.argparse_utils import is_valid_file, is_valid_path, is_positive_integer
import src.file_io_tools as file_io_tools
import argparse
import sys
import logging
from datetime import datetime


def parse_args(args):
    parser = argparse.ArgumentParser('Generate a Raster From a Shapefile')

    parser.add_argument("--input_path", "-i", dest="input_path", required=True,
                        type=lambda x: is_valid_path(parser, x),
                        help="the input path to the shapefile file set")

    parser.add_argument("--shapefile", "-s", dest="shapefile", required=True,
                        help="the name of the shapefile file set")

    parser.add_argument("--ref_file", "-r", dest="ref_file", required=True,
                        type=lambda x: is_valid_file(parser, x),
                        help="the reference tif to reproject to")

    parser.add_argument("--out_dir", "-o", dest="out_dir", required=False,
                        default='.',
                        help="the directory to write outputs to",
                        type=lambda x: is_valid_path(parser, x))

    parser.add_argument("--out_file", "-f", dest="out_file", required=False,
                        default=None,
                        help="the filename to give the output",
                        type=str)

    parser.add_argument("--side_multiple", "-m", dest="side_multiple", required=False,
                        default=1,
                        help="integer multiple for bounding box side",
                        type=lambda x: is_positive_integer(parser, x))

    parser.add_argument("--attribute_ids", "-a", dest="attribute_ids", required=False,
                        default=[1], nargs='+',
                        help="list of attribute ID's to clip",
                        type=lambda x: is_positive_integer(parser, x))

    parser.add_argument("--attribute_name", "-n", dest="attribute_name", required=False,
                        default="OBJECTID",
                        help="name of the attribute field to query for attribute ids",
                        type=str)

    return parser.parse_args(args)


def main():
    # setup logging
    start_date = datetime.utcnow()
    logging.basicConfig(filename='rasterize_shape.log', filemode='w', level=logging.INFO)
    logging.info(f'start process at {start_date} from command {" ".join(sys.argv[:])}')
    args = parse_args(sys.argv[1:])
    rasterize_shape(args.input_path, args.shapefile, args.ref_file, args.out_dir, args.out_file, args.side_multiple,
                    args.attribute_name, args.attribute_ids)
    end_date = datetime.utcnow()
    logging.info(f'finish process at {end_date} for a runtime of {end_date - start_date}')


def rasterize_shape(input_path, shapefile, ref_file, out_dir='.', out_file=None, side_multiple=1, attribute_name=None,
                    attribute_ids=None):
    reference_dataset = file_io_tools.read_geotiff(ref_file)
    rasterizer = ShapefileRasterizer(input_path, shapefile_name=shapefile,
                                     reference_dataset=reference_dataset, output_path=out_dir)
    rasterizer.rasterize_shapefile_to_disk(out_dir=out_dir, out_name=out_file,
                                           side_multiple=side_multiple, attribute_ids=attribute_ids,
                                           attribute_name=attribute_name)


if __name__ == '__main__':
    main()

