from pf_subsetter.clipper import Clipper
import sys
import argparse
from pf_subsetter.argparse_utils import is_valid_file, is_valid_path
from pf_subsetter import TIF_NO_DATA_VALUE_OUT as NO_DATA
import os
from pathlib import Path
import pf_subsetter.file_io_tools as file_io_tools
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
                        type=int)

    parser.add_argument("--tif_outs", "-t", dest="write_tifs", required=False,
                        default=0,
                        help="write tif output files",
                        type=int)

    return parser.parse_args(args)


def bulk_clip(mask_file, data_files, ref_file, out_dir='.', pfb_outs=1, tif_outs=0):
    """ clip a list of files using a mask and a domain reference tif

    @param mask_file: mask file generated from shapefile to mask utility no_data,0's=bbox,1's=mask
    @param data_files: list of data files (tif, pfb) to clip from
    @param ref_file: reference geotif file with proper projection and transform information
    @param out_dir: output directory (optional)
    @param pfb_outs: write pfb files as outputs (optional)
    @param tif_outs: write tif files as outputs (optional)
    @return: None
    """
    if not ref_file:
        if 'tif' not in mask_file.lower():
            input_tifs = locate_tifs(data_files)
            if len(input_tifs) < 1:
                raise Exception('Must include at least one geotif input or a ref_file when tif_outs is selected')
            else:
                ref_ds = file_io_tools.read_geotiff(input_tifs[0])
        else:
            ref_ds = file_io_tools.read_geotiff(mask_file)
    else:
        ref_ds = file_io_tools.read_geotiff(ref_file)
    # read the mask file
    mask = file_io_tools.read_file(mask_file)
    # create clipper with mask
    clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=-1)
    # clip all inputs and write outputs
    clip_inputs(clipper, input_list=data_files, out_dir=out_dir, pfb_outs=pfb_outs,
                tif_outs=tif_outs)


def locate_tifs(file_list):
    """ identify the .tif files in a list of files

    @param file_list: list of files to parse
    @return: array of files where the extension is .tif
    """
    return [s for s in file_list if '.tif' in s.lower()]


def clip_inputs(clipper, input_list, out_dir='.', pfb_outs=1, tif_outs=0, no_data=NO_DATA):
    """ clip a list of files using a clipper object

    @param clipper: clipper object loaded prepared with mask and reference dataset
    @param input_list: list of data files (tif, pfb) to clip from
    @param out_dir: output directory (optional)
    @param pfb_outs: write pfb files as outputs (optional)
    @param tif_outs: write tif files as outputs (optional)
    @param no_data: no_data value for tifs (optional)
    @return:
    """
    ref_proj = None
    if tif_outs:
        # identify projection
        ref_proj = clipper.ds_ref.GetProjection()

    # loop over and clip
    for data_file in input_list:
        filename = Path(data_file).stem
        return_arr, new_geom, new_mask, bbox = clipper.subset(file_io_tools.read_file(data_file))
        if pfb_outs:
            file_io_tools.write_pfb(return_arr, os.path.join(out_dir, f'{filename}_clip.pfb'))
        if tif_outs:
            file_io_tools.write_array_to_geotiff(os.path.join(out_dir, f'{filename}_clip.tif'),
                                                 return_arr, new_geom, ref_proj, no_data=no_data)


def main():
    # setup logging
    logging.basicConfig(filename='bulk_clipper.log', filemode='w', level=logging.INFO)
    start_date = datetime.utcnow()
    logging.info(f'start process at {start_date} from command {" ".join(sys.argv[:])}')
    args = parse_args(sys.argv[1:])
    # If tif out specified, look for a reference tif
    bulk_clip(args.mask_file, args.data_files, args.ref_file, args.out_dir, args.write_pfbs, args.write_tifs)
    end_date = datetime.utcnow()
    logging.info(f'completed process at {end_date} for a runtime of {end_date-start_date}')


if __name__ == '__main__':
    main()
