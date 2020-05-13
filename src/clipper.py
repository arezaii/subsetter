import os
import subprocess
import numpy as np
from global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA


class Clipper:

    def get_mask_array(self, subset_raster):
        """
        get the mask back as an array
        :param subset_raster: gdal dataset (typically result of rasterizing a shapefile)
        :return: array with 0's for blank and 1 for mask, representing shapefile
        """
        shp_raster_arr = subset_raster  # gdal.Open(subset_raster).ReadAsArray()
        # mask array
        mask_arr = (shp_raster_arr == 1).astype(np.int)
        return mask_arr


    """
    Code from Hoang's clip_inputs.py
    """
    def subset(self, arr, mask_arr, ds_ref, crop_to_domain=True, no_data=NO_DATA):
        arr1 = arr.copy()
        # create new geom
        old_geom = ds_ref.GetGeoTransform()
        # find new upper left index
        _, yy, xx = np.where(mask_arr == 1)
        max_x, max_y, min_x, min_y = self.find_mask_edges(xx, yy)
        len_y = max_y - min_y + 1
        len_x = max_x - min_x + 1
        # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
        top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y = self.calculate_new_dimensions(len_x, len_y)
        # create new geom
        new_geom = self.calculate_new_geom(min_x, min_y, old_geom)
        new_mask = mask_arr[:, min_y - top_pad:max_y + bottom_pad + 1, min_x - left_pad:max_x + right_pad + 1]
        if crop_to_domain:
            # clever use of slicing in numpy to get the data back within the mask, 0's everywhere else, and no_data
            # value carries over from clip input
            # Credit to Dr. Hoang Tran
            arr1[:, np.squeeze(mask_arr, axis=0) != 1] = no_data
            return_arr = np.zeros((arr1.shape[0], new_len_y, new_len_x))
            return_arr[:, top_pad:-bottom_pad, left_pad:-right_pad] = arr1[:, min_y:max_y + 1, min_x:max_x + 1]
        else:
            return_arr = arr1[:, min_y - top_pad:max_y + bottom_pad + 1, min_x - left_pad:max_x + right_pad + 1]
        bbox = (min_y - top_pad, max_y + bottom_pad + 1, min_x - left_pad, max_x + right_pad + 1)
        return return_arr, new_geom, new_mask, bbox

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

    def make_solid_file(self, mask_mat, out_name, dx=1000, dz=1000):
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
