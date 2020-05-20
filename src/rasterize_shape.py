from src.shapefile_utils import ShapefileRasterizer
from argparse_utils import is_valid_file, is_valid_path, is_positive_integer
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

    parser.add_argument("--side_multiple", "-m", dest="side_multiple", required=False,
                        default=1,
                        help="integer multiple for bounding box side",
                        type=lambda x: is_positive_integer(parser, x))

    return parser.parse_args(args)


def rasterize_shapefile_to_disk(reference_dataset, shapefile, out_dir, side_multiple=1):
    rasterizer = ShapefileRasterizer(shapefile_path=shapefile,
                                     reference_dataset=reference_dataset,
                                     output_path=out_dir)

    raster_path = rasterizer.reproject_and_mask(no_data=-999)
    final_mask = rasterizer.add_bbox_to_mask(raster_path, side_length_multiple=side_multiple)

    rasterizer.write_to_tif(filename=".".join([os.path.join(out_dir, rasterizer.shapefile_name), "tif"]),
                            data_set=final_mask)


def main():
    args = parse_args(sys.argv[1:])
    reference_dataset = gdal.Open(args.ref_file)
    rasterize_shapefile_to_disk(reference_dataset, args.shapefile, args.out_dir, args.side_multiple)


if __name__ == '__main__':
    main()

