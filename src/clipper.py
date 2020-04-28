import os
import subprocess

import numpy as np


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
    Code from Hoang's subset_domain.py
    """

    def subset(self, arr, mask_arr, ds_ref, crop_to_domain=1, no_data=0):
        arr1 = arr.copy()
        # create new geom
        old_geom = ds_ref.GetGeoTransform()
        # find new up left index
        yy, xx = np.where(mask_arr == 1)
        new_x = old_geom[0] + old_geom[1] * (min(xx) + 1)
        new_y = old_geom[3] + old_geom[5] * (min(yy) + 1)
        new_geom = (new_x, old_geom[1], old_geom[2], new_y, old_geom[4], old_geom[5])
        # start subsetting
        if len(arr.shape) == 2:
            arr1[mask_arr != 1] = no_data
            new_arr = arr1[min(yy):max(yy) + 1, min(xx):max(xx) + 1]
            # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
            len_y, len_x = new_arr.shape
            new_len_y = ((len_y // 32) + 1) * 32
            n1 = (new_len_y - len_y) // 2
            n2 = new_len_y - len_y - n1
            new_len_x = ((len_x // 32) + 1) * 32
            n3 = (new_len_x - len_x) // 2
            n4 = new_len_x - len_x - n3
            return_arr = np.zeros((new_len_y, new_len_x))
            return_arr[n1:-n2, n3:-n4] = new_arr
        else:
            arr1[:, mask_arr != 1] = no_data
            new_arr = arr1[:, min(yy):max(yy) + 1, min(xx):max(xx) + 1]
            # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
            _, len_y, len_x = new_arr.shape
            new_len_y = ((len_y // 32) + 1) * 32
            n1 = (new_len_y - len_y) // 2
            n2 = new_len_y - len_y - n1
            new_len_x = ((len_x // 32) + 1) * 32
            n3 = (new_len_x - len_x) // 2
            n4 = new_len_x - len_x - n3
            return_arr = np.zeros((new_arr.shape[0], new_len_y, new_len_x))
            return_arr[:, n1:-n2, n3:-n4] = new_arr
        bbox = (min(yy) - n1, max(yy) + n2 + 1, min(xx) - n3, max(xx) + n4 + 1)
        return return_arr, new_geom, bbox

    """
    Code from Hoang's clip_inputs.py
    """

    # def subset(self, arr, mask_arr, ds_ref, crop_to_domain=1, no_data=0):
    #     arr1 = arr.copy()
    #     # create new geom
    #     old_geom = ds_ref.GetGeoTransform()
    #     # find new up left index
    #     yy, xx = np.where(mask_arr == 1)
    #     len_y = max(yy) - min(yy) + 1
    #     len_x = max(xx) - min(xx) + 1
    #     # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
    #     new_len_y = ((len_y // 32) + 1) * 32
    #     n1 = (new_len_y - len_y) // 2
    #     n2 = new_len_y - len_y - n1
    #     new_len_x = ((len_x // 32) + 1) * 32
    #     n3 = (new_len_x - len_x) // 2
    #     n4 = new_len_x - len_x - n3
    #     # create new geom
    #     new_x = old_geom[0] + old_geom[1] * (min(xx) + 1)
    #     new_y = old_geom[3] + old_geom[5] * (min(yy) + 1)
    #     new_geom = (new_x, old_geom[1], old_geom[2], new_y, old_geom[4], old_geom[5])
    #     new_mask = mask_arr[min(yy) - n1:max(yy) + n2 + 1, min(xx) - n3:max(xx) + n4 + 1]
    #     # start clipping
    #     # 2d array
    #     if len(arr.shape) == 2:
    #         if crop_to_domain:
    #             arr1[mask_arr != 1] = no_data
    #             return_arr = np.zeros((new_len_y, new_len_x))
    #             return_arr[n1:-n2, n3:-n4] = arr1[min(yy):max(yy) + 1, min(xx):max(xx) + 1]
    #         else:
    #             return_arr = arr1[min(yy) - n1:max(yy) + n2 + 1, min(xx) - n3:max(xx) + n4 + 1]
    #         return_arr = return_arr[np.newaxis, ...]
    #     else:
    #         if crop_to_domain:
    #             arr1[:, mask_arr != 1] = no_data
    #             return_arr = np.zeros((arr1.shape[0], new_len_y, new_len_x))
    #             return_arr[:, n1:-n2, n3:-n4] = arr1[:, min(yy):max(yy) + 1, min(xx):max(xx) + 1]
    #         else:
    #             return_arr = arr1[:, min(yy) - n1:max(yy) + n2 + 1, min(xx) - n3:max(xx) + n4 + 1]
    #     bbox = (min(yy) - n1, max(yy) + n2 + 1, min(xx) - n3, max(xx) + n4 + 1)
    #     return return_arr, new_geom, new_mask, bbox

    def make_solid_file(self, mask_mat, out_name, dx=1000, dz=1000):

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
        # cmd_create_sol = 'pf-mask-utilities/mask-to-pfsol --mask-back ' + list_patches[0] + \
        #                  ' --mask-front ' + list_patches[1] + \
        #                  ' --mask-right ' + list_patches[2] + \
        #                  ' --mask-left ' + list_patches[3] + \
        #                  ' --mask-bottom ' + list_patches[4] + \
        #                  ' --mask-top ' + list_patches[5] + \
        #                  ' --vtk ' + out_vtk + \
        #                  ' --pfsol ' + out_pfsol + \
        #                  ' --depth ' + str(dz)
        #
        # os.system(cmd_create_sol)
        #
        # temp_list = cmd_create_sol.stdout.decode('utf-8').split('\n')
        # batches = ''
        # for line in temp_list:
        #     if 'Number of triangles in patch' in line:
        #         line = line.strip()
        #         batches += line.split()[-3] + ' '
