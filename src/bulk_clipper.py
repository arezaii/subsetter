from src.clipper import Clipper
import sys
import argparse
from src.argparse_utils import is_valid_file, is_valid_path
from src.file_io_tools import read_file, write_pfb, write_array_to_geotiff
from src.global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA
import os
from pathlib import Path
import gdal
import logging
from datetime import datetime


def parse_args(args):
    parser = argparse.ArgumentParser('Clip a list of identically gridded files and extract the data within the mask')

    parser.add_argument("--maskfile", "-m", dest="mask_file", required=True,
                        type=lambda x: is_valid_file(parser, x),
                        help="the input mask")

    parser.add_argument("--datafiles", "-d", dest="data_files", required=True,
                        nargs='+',
                        type=lambda x: is_valid_file(parser, x),
                        help="the list of gridded data files (.pfb or .tif) to clip from")

    parser.add_argument("--ref_file", "-r", dest="ref_file", required=False,
                        type=lambda x: is_valid_file(parser, x),
                        help="the reference tif, if writing TIF outputs")

    parser.add_argument("--out_dir", "-o", dest="out_dir", required=False,
                        default='.',
                        help="the directory to write outputs to",
                        type=lambda x: is_valid_path(parser, x))

    parser.add_argument("--pfb_outs", "-p", dest="write_pfbs", required=False,
                        default=1,
                        help="write pfb output files",
                        type=bool)

    parser.add_argument("--tif_outs", "-t", dest="write_tifs", required=False,
                        default=0,
                        help="write tif output files",
                        type=bool)

    return parser.parse_args(args)


def locate_tifs(file_list):
    return [s for s in file_list if 'tif' in s.lower()]


def clip_inputs(mask, ref_ds, input_list, out_dir='.', pfb_outs=1, tif_outs=0, no_data=NO_DATA):
    # create the clipper
    clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=-1)
    if tif_outs:
        # identify projection
        ref_proj = ref_ds.GetProjection()

    # loop over and clip
    for data_file in input_list:
        filename = Path(data_file).stem
        return_arr, new_geom, new_mask, bbox = clipper.subset(read_file(data_file))
        if pfb_outs:
            write_pfb(return_arr, os.path.join(out_dir, f'{filename}_clip.pfb'))
        if tif_outs:
            write_array_to_geotiff(os.path.join(out_dir, f'{filename}_clip.tif'),
                                   return_arr, new_geom, ref_proj, no_data=no_data)


def main():
    # setup logging
    logging.basicConfig(filename='bulk_clipper.log', filemode='w', level=logging.INFO)
    start_date = datetime.utcnow()
    logging.info(f'start process at {start_date}')
    args = parse_args(sys.argv[1:])
    ref_ds = None
    if args.write_tifs:
        if not args.ref_file:
            if 'tif' not in args.mask_file.lower():
                input_tifs = locate_tifs(args.data_files)
                if len(input_tifs) < 1:
                    raise Exception('Must include at least one geotif input or a ref_file when tif_outs is selected')
                else:
                    ref_ds = gdal.Open(input_tifs[0])
            else:
                ref_ds = gdal.Open(args.mask_file)
        else:
            ref_ds = gdal.Open(args.ref_file)

    clip_inputs(read_file(args.mask_file), ref_ds, args.data_files, args.out_dir, args.write_pfbs, args.write_tifs)
    end_date = datetime.utcnow()
    logging.info(f'completed process at {end_date} for a runtime of {end_date-start_date}')


if __name__ == '__main__':
    main()
