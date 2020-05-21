import os
import subprocess
import numpy.ma as ma
import numpy as np
from src.global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA
from src.mask_utils import MaskUtils
import logging


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
        self.bbox = [min_y, max_y+1, min_x, max_x+1]
        self.new_geom = mask_utils.calculate_new_geom(min_x, min_y, self.ds_ref.GetGeoTransform())
        self.new_mask = (self.inverted_zero_one_mask.filled(fill_value=no_data_threshold) == 1)[:,
                        min_y:max_y+1, min_x:max_x+1]

    def subset(self, data_array, no_data=NO_DATA):
        """
        clip the data from data_array in the shape and extents of the clipper's clipped mask
        """
        full_mask = self.inverted_zero_one_mask.mask
        clip_mask = ~self.new_mask
        # Handle multi-layered files, such as subsurface or forcings or pme
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

        return return_arr, self.new_geom, self.new_mask, self.bbox

    def make_solid_file(self, out_name, dx=1000, dz=1000):
        mask_mat = self.new_mask
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
        # This part assumes that you have installed pf-mask-utilities
        out_vtk = out_name + '.vtk'
        out_pfsol = out_name + '.pfsol'

        if os.path.isfile(out_vtk):
            os.remove(out_vtk)

        if os.path.isfile(out_pfsol):
            os.remove(out_pfsol)

        create_sub = subprocess.run(['pf-mask-utilities/mask-to-pfsol', '--mask-back', list_patches[0],
                                     '--mask-front', list_patches[1],
                                     '--mask-right', list_patches[2],
                                     '--mask-left ' + list_patches[3],
                                     '--mask-bottom ' + list_patches[4],
                                     '--mask-top ' + list_patches[5],
                                     '--vtk', out_vtk,
                                     '--pfsol', out_pfsol,
                                     '--depth', str(dz)], stdout=subprocess.PIPE)
        temp_list = create_sub.stdout.decode('utf-8').split('\n')
        batches = ''
        for line in temp_list:
            if 'Number of triangles in patch' in line:
                line = line.strip()
                batches += line.split()[-3] + ' '
        logging.info(f'identified batches in domain {batches}')
        return batches
