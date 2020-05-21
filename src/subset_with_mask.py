import argparse
import sys
from src.argparse_utils import is_valid_file, is_valid_path


def parse_args(args):
    parser = argparse.ArgumentParser('Clip files using a raster mask')
    parser.add_argument("--mask_file", "-m", dest="mask_file", required=True,
                        type=lambda x: is_valid_file(parser, x),
                        help="the mask file to use")

    parser.add_argument("--bbox_file", "-b", dest="bbox_file", required=True,
                        type=lambda x: is_valid_file(parser, x),
                        help="the bounding box file for the mask")

    parser.add_argument("--files", "-f", dest="input_files", required=True,
                        type=lambda x: is_valid_file(parser, x),
                        help="the bounding box file for the mask")

    parser.add_argument("--out_dir", "-o", dest="out_dir", required=False,
                        default='.',
                        help="the directory to write outputs to",
                        type=lambda x: is_valid_path(parser, x))

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])



if __name__ == '__main__':
    main()
