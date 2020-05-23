import logging
import os
import subprocess
from shutil import which
import numpy as np
import numpy.ma as ma
from src.global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA
from src.mask_utils import MaskUtils
import src.file_io_tools as file_io_tools


class Clipper:

    def __init__(self, mask_array, reference_dataset, no_data_threshold=NO_DATA):
        """
        Assumes input mask_array has 1's written to valid data, 0's for bounding box,
         and <=no_data_threshold for no_data val, no_data_threshold must be < 0 or bounding box will
         not be identifiable
        """
        self.ds_ref = reference_dataset
        mask_utils = MaskUtils(mask_array, bbox_val=0, no_data_threshold=no_data_threshold)
        self.inverted_zero_one_mask = mask_utils.bbox_crop
        max_x, max_y, min_x, min_y = mask_utils.bbox_crop_edges
        self.bbox = [min_y, max_y + 1, min_x, max_x + 1]
        self.clipped_geom = mask_utils.calculate_new_geom(min_x, min_y, self.ds_ref.GetGeoTransform())
        self.clipped_mask = (self.inverted_zero_one_mask.filled(fill_value=no_data_threshold) == 1)[:,
                            min_y:max_y + 1, min_x:max_x + 1]

    def write_bbox_file(self, bbox_path):
        file_io_tools.write_bbox(self.bbox, bbox_path)

    def subset(self, data_array, no_data=NO_DATA):
        """
        clip the data from data_array in the shape and extents of the clipper's clipped mask
        """
        full_mask = self.inverted_zero_one_mask.mask
        clip_mask = ~self.clipped_mask
        # Handle multi-layered files, such as subsurface or forcings
        if data_array.shape[0] > 1:
            full_mask = np.broadcast_to(full_mask, data_array.shape)
            clip_mask = np.broadcast_to(clip_mask, (data_array.shape[0], clip_mask.shape[1], clip_mask.shape[2]))

        # mask the input data using numpy masked array module (True=InvalidData, False=ValidData)
        masked_data = ma.masked_array(data=data_array, mask=full_mask)

        # return an array that includes all of the z data, and x and y no_data outside of the mask area
        return_arr = ma.masked_array(masked_data[:,
                                     self.bbox[0]: self.bbox[1],
                                     self.bbox[2]: self.bbox[3]].filled(fill_value=no_data),
                                     mask=clip_mask).filled(fill_value=no_data)

        return return_arr, self.clipped_geom, self.clipped_mask, self.bbox

    # TODO: move solid file generation to somewhere else...maybe it's own class
    def make_solid_file(self, out_name, dx=1000, dz=1000):
        pf_mask_to_sol_path = self.find_mask_to_sol_exe()
        if pf_mask_to_sol_path is None:
            msg = 'Could not locate pfmask-to-pfsol utility needed to generate solid file (.pfsol)' \
                  ' ensure PARFLOW_DIR environment variable is set'
            logging.exception(msg)
            raise Exception(msg)

        mask_mat = self.clipped_mask
        if len(mask_mat.shape) == 3:
            mask_mat = np.squeeze(mask_mat, axis=0)
        # create back borders
        # Back borders occur where mask[y+1]-mask[y] is negative
        # (i.e. the cell above is a zero and the cell is inside the mask, i.e. a 1)
        back_mat = np.zeros(mask_mat.shape)

        # create front borders
        # Front borders occur where mask[y-1]-mask[y] is negative
        # (i.e. the cell above is a zero and the cell is inside the mask, i.e. a 1)
        front_mat = np.zeros(mask_mat.shape)

        # create left borders
        # Left borders occur where mask[x-1]-mask[x] is negative
        left_mat = np.zeros(mask_mat.shape)

        # create right borders
        # Right borders occur where mask[x+1]-mask[x] is negative
        right_mat = np.zeros(mask_mat.shape)

        # deal with top and bottom patches
        # 3 = regular overland boundary
        # 4 = Lake
        # 5 = Sink
        # 6 = bottom
        # 8 = Stream
        # 9 = Reservoir

        top_mat = mask_mat * 3

        bottom_mat = mask_mat * 6

        # create header and write ascii files
        header = 'ncols ' + str(mask_mat.shape[1]) + '\n'
        header += 'nrows ' + str(mask_mat.shape[0]) + '\n'
        header += 'xllcorner 0.0\n'
        header += 'yllcorner 0.0\n'
        header += 'cellsize ' + str(dx) + '\n'
        header += 'NODATA_value 0.0\n'

        patches = {os.path.join(os.path.dirname(out_name), 'Back_Border.asc'): back_mat,
                   os.path.join(os.path.dirname(out_name), 'Front_Border.asc'): front_mat,
                   os.path.join(os.path.dirname(out_name), 'Right_Border.asc'): right_mat,
                   os.path.join(os.path.dirname(out_name), 'Left_Border.asc'): left_mat,
                   os.path.join(os.path.dirname(out_name), 'Bottom_Border.asc'): bottom_mat,
                   os.path.join(os.path.dirname(out_name), 'Top_Border.asc'): top_mat}

        list_patches = list(patches.keys())
        for patch in patches:
            with open(patch, 'w') as fo:
                fo.write(header)
                np.savetxt(fo, patches[patch].reshape([-1, 1]), '%.3f', ' ')

        # Create solid domain file
        # This part assumes that you have installed pf-mask-utilities or ParFlow with PARFLOW_DIR set
        out_vtk = out_name + '.vtk'
        out_pfsol = out_name + '.pfsol'

        if os.path.isfile(out_vtk):
            os.remove(out_vtk)

        if os.path.isfile(out_pfsol):
            os.remove(out_pfsol)

        sub_cmd_str = [pf_mask_to_sol_path[0],
                       '--mask-back', list_patches[0],
                       '--mask-front', list_patches[1],
                       '--mask-right', list_patches[2],
                       '--mask-left ' + list_patches[3],
                       '--mask-bottom ' + list_patches[4],
                       '--mask-top ' + list_patches[5],
                       '--vtk', out_vtk,
                       '--pfsol', out_pfsol,
                       pf_mask_to_sol_path[1], str(dz)]
        logging.info(f'begin mask_to_sol subprocess, command executed: {sub_cmd_str}')
        create_sub = subprocess.run(sub_cmd_str, stdout=subprocess.PIPE)
        temp_list = create_sub.stdout.decode('utf-8').split('\n')
        batches = ''
        for line in temp_list:
            if 'Number of triangles in patch' in line:
                line = line.strip()
                batches += line.split()[-3] + ' '
        logging.info(f'identified batches in domain {batches}')
        return batches

    def find_mask_to_sol_exe(self):
        """
        look for the pf_mask_to_pfsol utility on the system, then verify the file we think exists does exist
        """
        pf_mask_to_sol_path = None
        possible_paths = {('mask-to-pfsol', '--depth'): [os.environ.get('PFMASKUTILS'), which('mask-to-pfsol')],
                          ('pfmask-to-pfsol', '--z-bottom'):
                              [f'{os.environ["PARFLOW_DIR"]}/bin', which('pfmask-to-pfsol')]}
        for executable, possible_paths in possible_paths.items():
            executable_path = next((path for path in possible_paths if path is not None), None)
            if executable_path is not None:
                if os.path.isfile(os.path.join(executable_path, executable[0])):
                    pf_mask_to_sol_path = (os.path.join(executable_path, executable[0]), executable[1])
                    break
        logging.info(f'searching for mask_to_sol executable resulted in: {pf_mask_to_sol_path[0]}')
        return pf_mask_to_sol_path
