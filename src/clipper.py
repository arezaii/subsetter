import os
import subprocess
import numpy.ma as ma
import numpy as np
from global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA


class Clipper:

    def __init__(self, mask_array, reference_dataset, no_data_threshold=NO_DATA):
        """
        Assumes input mask_array has 1's written to valid data, and <=no_data_threshold for no_data val
        """
        self.inverse_zero_one_mask = ma.masked_where(mask_array <= no_data_threshold, mask_array)
        self.ds_ref = reference_dataset
        # crop the domain to from full extents to a small subset
        self.clipped_mask, self.clipped_geom, \
        self.min_x, self.min_y, self.max_x, self.max_y, self.top_pad, \
        self.bottom_pad, self.left_pad, self.right_pad = self.clip_mask()
        # mark the extents of the new cropped mask
        self.top_edge = self.min_y - self.top_pad
        self.bottom_edge = self.max_y + self.bottom_pad + 1
        self.left_edge = self.min_x - self.left_pad
        self.right_edge = self.max_x + self.right_pad + 1
        self.bbox = [self.top_edge, self.bottom_edge, self.left_edge, self.right_edge]

    def clip_mask(self):
        """
        clip the input mask (full extents) to extents of masked data plus an edge buffer
        creates a mask of 1 for valid data and 0 for no_data
        """
        old_geom = self.ds_ref.GetGeoTransform()
        _, yy, xx = np.where(~self.inverse_zero_one_mask.mask == 1)
        max_x, max_y, min_x, min_y = self.find_mask_edges(xx, yy)
        len_y = max_y - min_y + 1
        len_x = max_x - min_x + 1
        # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
        top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y = self.calculate_new_dimensions(len_x, len_y)
        # create new geom
        new_geom = self.calculate_new_geom(min_x, min_y, old_geom)
        new_mask = self.inverse_zero_one_mask[:, min_y - top_pad:max_y + bottom_pad + 1, min_x - left_pad:max_x + right_pad + 1]
        return new_mask.filled(fill_value=0), new_geom, min_x, min_y, max_x, max_y, top_pad, bottom_pad, left_pad, right_pad

    """
    Code from Hoang's clip_inputs.py
    """
    def subset(self, data_array, crop_to_domain=True, no_data=NO_DATA):
        """
        clip the data from data_array in the shape and extents of the clipper's clipped mask
        """
        mask = self.inverse_zero_one_mask.mask
        # Handle multi-layered files, such as subsurface or forcings
        if data_array.shape[0] > 1:
            mask = np.broadcast_to(mask, data_array.shape)

        # mask the input data using numpy masked array module (True=InvalidData, False=ValidData)
        masked_data = ma.masked_array(data=data_array, mask=mask)

        # return an array that includes all of the z data, and x and y no_data outside of the mask area
        return_arr = masked_data[:,
                     self.top_edge: self.bottom_edge,
                     self.left_edge: self.right_edge].filled(fill_value=no_data)
        return return_arr, self.clipped_geom, self.clipped_mask, self.bbox
        # TODO: Figure out if we still need the crop to domain functionality
        # if crop_to_domain:
        #     # clever use of slicing in numpy to get the data back within the mask,
        #     # adapted to write no_data values everywhere outside mask bounds
        #     # Thanks to Dr. Hoang Tran
        #     return_arr = np.ones((data_array.shape[0], self.clipped_mask.shape[1], self.clipped_mask.shape[2])) * no_data
        #     data_array[:, np.squeeze(self.inverse_zero_one_mask, axis=0) != 1] = no_data
        #     return_arr[:, top_pad:-bottom_pad, left_pad:-right_pad] = data_array[:, min_y:max_y + 1, min_x:max_x + 1]
        # else:
        #     return_arr = data_array[:, min_y - top_pad:max_y + bottom_pad + 1, min_x - left_pad:max_x + right_pad + 1]

    def calculate_new_geom(self, min_x, min_y, old_geom):
        new_x = old_geom[0] + old_geom[1] * (min_x + 1)
        new_y = old_geom[3] + old_geom[5] * (min_y + 1)
        new_geom = (new_x, old_geom[1], old_geom[2], new_y, old_geom[4], old_geom[5])
        return new_geom

    def find_mask_edges(self, xx, yy):
        min_x = min(xx)
        min_y = min(yy)
        max_x = max(xx)
        max_y = max(yy)
        return max_x, max_y, min_x, min_y

    def calculate_new_dimensions(self, len_x, len_y):
        # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
        new_len_y = ((len_y // 32) + 1) * 32
        top_pad = (new_len_y - len_y) // 2
        bottom_pad = new_len_y - len_y - top_pad
        new_len_x = ((len_x // 32) + 1) * 32
        left_pad = (new_len_x - len_x) // 2
        right_pad = new_len_x - len_x - left_pad
        return top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y

    def make_solid_file(self, out_name, dx=1000, dz=1000):
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
        return batches
