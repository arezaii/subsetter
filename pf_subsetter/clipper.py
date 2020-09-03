import logging
import numpy as np
import numpy.ma as ma
from pf_subsetter import TIF_NO_DATA_VALUE_OUT as NO_DATA


class BoxClipper:
    """
    @param x: the starting x value (1 based index)
    @param y: the starting y value (1 based index)
    @param z:
    @param nx: the number of x cells to clip
    @param ny: the number of y cells to clip
    @param nz:
    @param no_data:  the no data value to use
    """
    def __init__(self, ref_array, x=1, y=1, z=1, nx=None, ny=None, nz=None, no_data=NO_DATA):
        self.ref_array = ref_array
        if nx is None:
            nx = self.ref_array.shape[2]
        if ny is None:
            ny = self.ref_array.shape[1]
        if nz is None:
            nz = self.ref_array.shape[0]
        if nx < 1 or ny < 1 or nz < 1 or x < 1 or y < 1 or z < 1:
            raise Exception("Error: invalid dimension, x,y,z nx, ny, nz must be >=1")
        self.y_len = self.ref_array.shape[1]
        self._translate_bbox(x,y,z,nx,ny,nz)

    def _translate_bbox(self, x, y, z, nx, ny, nz):
        # update the x,y,z, nx, ny, nz values if desired
        if nx is not None:
            self.nx = nx
        if ny is not None:
            self.ny = ny
        if nz is not None:
            self.nz = nz
        if x is not None:
            self.x_0 = x - 1
            self.x_end = self.x_0 + nx
        if z is not None:
            self.z_0 = z - 1
            self.z_end = self.z_0 + nz
        if y is not None:
            self.y_0 = self.y_len - ny - y + 1
            self.y_end = self.y_len - y + 1

    def update_bbox(self, x=None, y=None, z=None, nx=None, ny=None, nz=None):
        self._translate_bbox(x,y,z,nx,ny,nz)

    def clip_ref_array(self):
        """

        @return: an ndarray clip of the reference array
        """
        return self.ref_array[self.z_0:self.z_end, self.y_0:self.y_end, self.x_0:self.x_end]

    def clip_array(self, data_array):
        """

        @return: an ndarray clip of the data array
        """
        return data_array[self.z_0:self.z_end, self.y_0:self.y_end, self.x_0:self.x_end]


class MaskClipper:

    def __init__(self, subset_mask, no_data_threshold=NO_DATA):
        """ Assumes input mask_array has 1's written to valid data, 0's for bounding box,
         and <=no_data_threshold for no_data val, no_data_threshold must be < 0 or bounding box will
         not be identifiable

        @param subset_mask: subset_mask object
        @param no_data_threshold: value which all values less than are treated as no data
        """
        self.subset_mask = subset_mask
        min_y, max_y, min_x, max_x = self.subset_mask.bbox_edges
        self.bbox = [min_y, max_y + 1, min_x, max_x + 1]
        self.clipped_geom = self.subset_mask.calculate_new_geom(min_x, min_y, self.subset_mask.mask_tif.GetGeoTransform())
        self.clipped_mask = (self.subset_mask.bbox_mask.filled(fill_value=no_data_threshold) == 1)[:, min_y:max_y + 1,
                            min_x:max_x + 1]

    def subset(self, data_array, no_data=NO_DATA, crop_inner=1):
        """subset the data from data_array in the shape and extents of the clipper's clipped subset_mask

        @param data_array: 3d array of data to subset
        @param no_data: no data value for outputs
        @param crop_inner: crop the data to the inner subset_mask (1) or the outer bounding box (0) *option for CLM clips
        @return: the subset data as a 3d array, gdal geometry for the clip, subset_mask of 1/0 of clipped area, bounding box
        """
        full_mask = self.subset_mask.bbox_mask.mask
        clip_mask = ~self.clipped_mask
        # Handle multi-layered files, such as subsurface or forcings
        if data_array.shape[0] > 1:
            full_mask = np.broadcast_to(full_mask, data_array.shape)
            clip_mask = np.broadcast_to(clip_mask, (data_array.shape[0], clip_mask.shape[1], clip_mask.shape[2]))
            logging.info(f'clipper: broadcast subset_mask to match input data z layers: {data_array.shape[0]}')
        # mask the input data using numpy masked array module (True=InvalidData, False=ValidData)
        masked_data = ma.masked_array(data=data_array, mask=full_mask)

        if crop_inner:
            # return an array that includes all of the z data, and x and y no_data outside of the mask area
            return_arr = ma.masked_array(masked_data[:,
                                         self.bbox[0]: self.bbox[1],
                                         self.bbox[2]: self.bbox[3]].filled(fill_value=no_data),
                                         mask=clip_mask).filled(fill_value=no_data)
            # logging.info(f'clipped data with (z,y,x) shape {data_array.shape} to {return_arr.shape} '
            #              f'using bbox (top, bot, left, right) {self.printable_bbox}')
        else:
            # return an array that includes all of the z data, and x and y inside the bounding box
            return_arr = ma.masked_array(masked_data[:,
                                         self.bbox[0]: self.bbox[1],
                                         self.bbox[2]: self.bbox[3]],
                                         mask=np.zeros(clip_mask.shape)).filled()
            # logging.info(f'clipped data with (z,y,x) shape {data_array.shape} to {return_arr.shape} '
            #              f'using bbox (top, bot, left, right) {self.printable_bbox}')

        return return_arr, self.clipped_geom, self.clipped_mask, self.bbox
