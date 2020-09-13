import sys
import argparse
import os
from pathlib import Path
import logging
from datetime import datetime
from parflow.subset.clipper import MaskClipper, BoxClipper
from parflow.subset.utils.arguments import is_valid_file, is_valid_path
from parflow.subset import TIF_NO_DATA_VALUE_OUT as NO_DATA
from parflow.subset.mask import SubsetMask
import parflow.subset.utils.io as file_io_tools


def parse_args(args):
    parser = argparse.ArgumentParser('Clip a list of identically gridded files and extract the data within the mask')

    exclusive_group = parser.add_mutually_exclusive_group(required=True)

    exclusive_group.add_argument("--maskfile", "-m", dest="mask_file", required=False,
                        type=lambda x: is_valid_file(parser, x),
                        help="gridded full_dim_mask file to full extent of files to be clipped")

    exclusive_group.add_argument("--bboxfile", "-b", dest="bbox_file", required=False,
                        type=lambda x: is_valid_file(parser, x),
                        help="a tab separated text file indicating x1,y1,nx,ny of the files to be clipped")

    exclusive_group.add_argument("--inline-bbox", "-i", dest="bbox_def", nargs=4, metavar=('X1', 'Y1', 'NX', 'NY'),
                                 required=False, type=int, help="bbox defined by x1 y1 nx ny")

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


def mask_clip(mask_file, data_files, out_dir='.', pfb_outs=1, tif_outs=0):
    """ clip a list of files using a full_dim_mask and a domain reference tif

    @param mask_file: full_dim_mask file generated from shapefile to mask utility no_data,0's=bbox,1's=mask
    @param data_files: list of data files (tif, pfb) to clip from
    @param out_dir: output directory (optional)
    @param pfb_outs: write pfb files as outputs (optional)
    @param tif_outs: write tif files as outputs (optional)
    @return: None
    """
    # read the full_dim_mask file
    mask = SubsetMask(mask_file)

    # create clipper with full_dim_mask
    clipper = MaskClipper(subset_mask=mask, no_data_threshold=-1)
    # clip all inputs and write outputs
    clip_inputs(clipper, input_list=data_files, out_dir=out_dir, pfb_outs=pfb_outs,
                tif_outs=tif_outs)


def box_clip(bbox, data_files, out_dir='.', pfb_outs=1, tif_outs=0):

    # create clipper with bbox
    clipper = BoxClipper(ref_array=file_io_tools.read_file(data_files[0]), x=bbox[0], y=bbox[1], nx=bbox[2], ny=bbox[3])
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

    @param clipper: clipper object prepared with full_dim_mask and reference dataset
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
        ref_proj = clipper.subset_mask.mask_tif.GetProjection()

    # loop over and clip
    for data_file in input_list:
        filename = Path(data_file).stem
        return_arr, new_geom, _, _ = clipper.subset(file_io_tools.read_file(data_file))
        if pfb_outs:
            file_io_tools.write_pfb(return_arr, os.path.join(out_dir, f'{filename}_clip.pfb'))
        if tif_outs and new_geom is not None and ref_proj is not None:
            file_io_tools.write_array_to_geotiff(os.path.join(out_dir, f'{filename}_clip.tif'),
                                                 return_arr, new_geom, ref_proj, no_data=no_data)


def main():
    # setup logging
    logging.basicConfig(filename='bulk_clipper.log', filemode='w', level=logging.INFO)
    start_date = datetime.utcnow()
    logging.info(f'start process at {start_date} from command {" ".join(sys.argv[:])}')
    args = parse_args(sys.argv[1:])
    # If tif out specified, look for a reference tif
    if args.write_tifs and not args.ref_file:
        if 'tif' not in args.mask_file.lower():
            input_tifs = locate_tifs(args.data_files)
            if len(input_tifs) < 1:
                raise Exception('Must include at least one geotif input or a ref_file when tif_outs is selected')
    if args.mask_file:
        mask_clip(args.mask_file, args.data_files, args.out_dir, args.write_pfbs, args.write_tifs)
    elif args.bbox_file:
        box_clip(file_io_tools.read_bbox(args.bbox_file), args.data_files, args.out_dir, args.write_pfbs, args.write_tifs)
    elif args.bbox_def:
        box_clip(args.bbox_def, args.data_files, args.out_dir, args.write_pfbs, args.write_tifs)
    end_date = datetime.utcnow()
    logging.info(f'completed process at {end_date} for a runtime of {end_date-start_date}')


if __name__ == '__main__':
    main()
