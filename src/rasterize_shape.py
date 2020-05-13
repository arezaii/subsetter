from src.shapefile_utils import ShapefileRasterizer
from argparse_utils import is_valid_file, is_valid_path
import argparse
import sys
import gdal
import os


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

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    rasterizer = ShapefileRasterizer(args.shapefile, output_path=args.out_dir)
    reference_dataset = gdal.Open(args.ref_file)
    raster_path = rasterizer.reproject_and_mask(reference_dataset, no_data=0)
    rasterizer.write_to_tif(filename=".".join([os.path.join(args.out_dir, rasterizer.shapefile_name), "tif"]),
                            data_set=gdal.Open(raster_path))


if __name__ == '__main__':
    main()

