from pf_subsetter.utils.io import read_geotiff, write_array_to_geotiff, write_bbox
import numpy as np
import numpy.ma as ma
import logging


class SubsetMask:

    def __init__(self, tif_file, bbox_val=0):
        self.mask_tif = read_geotiff(tif_file)
        self.mask_array = self._get_mask_array()
        self.bbox_val = bbox_val
        self.inner_mask = self._find_inner_object()
        self.bbox_mask = self._find_bbox()
        self.no_data_value = self.mask_tif.GetRasterBand(1).GetNoDataValue()
        self.inner_mask_edges = self.find_mask_edges(self.inner_mask)
        self.bbox_edges = self.find_mask_edges(self.bbox_mask)

    def _get_mask_array(self):
        mask_array = self.mask_tif.ReadAsArray()
        mask_shape = mask_array.shape
        if len(mask_shape) == 2:
            mask_array = mask_array[np.newaxis, ...]
            logging.info(f'added z-axis to 2d mask_array, old shape (y,x)={mask_shape}, '
                         f'new shape (z,y,x)={mask_array.shape}')
        return mask_array

    def _find_bbox(self):
        """ locate the outer bbox area

        @return: masked numpy array with mask edges at outer area
        """
        mx = ma.masked_where(self.mask_array < self.bbox_val, self.mask_array)
        logging.info(f'SubsetMask located outer bbox in mask array')
        return mx

    def _find_inner_object(self):
        """ locate the inner object

        @return: masked numpy array with tight mask along shape border
        """
        mx = ma.masked_where(self.mask_array <= self.bbox_val, self.mask_array)
        logging.info(f'SubsetMask located inner mask in mask array')
        return mx

    @property
    def bbox_shape(self):
        return tuple([(self.bbox_edges[1]-self.bbox_edges[0]) + 1, (self.bbox_edges[3]-self.bbox_edges[2]) + 1])

    @property
    def inner_mask_shape(self):
        return tuple([(self.inner_mask_edges[1]-self.inner_mask_edges[0]) + 1,
                      (self.inner_mask_edges[3]-self.inner_mask_edges[2]) + 1])

    @property
    def mask_shape(self):
        return self.mask_array.shape

    def add_bbox_to_mask(self, side_length_multiple=1):
        """ add the inner bounding box of 0's to the reprojected mask. This will expand the bounding box of the
        clip so that the mask is centered in the bbox and the bbox edges expand proportionally in each direction
        to make the final bbox edges a multiple of the side_length_multiple argument

        @param tiff_path: path to the tiff file that defines the mask with no_data and 1
        @param side_length_multiple: optional multiple to expand bounding box to
        @return: 3d array with no data outside the bbox, 0 inside bbox, and 1 in mask area, bounding box values
        """

        min_y, max_y, min_x, max_x = self.inner_mask_edges
        new_dims = self.calculate_new_dimensions(len_x=(max_x - min_x) + 1,
                                                       len_y=(max_y - min_y) + 1,
                                                       side_multiple=side_length_multiple)
        top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y = new_dims
        new_mask = self.inner_mask.filled(fill_value=self.no_data_value)
        new_edges = self.calculate_buffer_edges(min_x, min_y, max_x, max_y, [top_pad, bottom_pad, left_pad, right_pad])
        top_edge, bottom_edge, left_edge, right_edge = new_edges
        new_mask[:, top_edge: bottom_edge, left_edge: right_edge] =\
            self.inner_mask[:, top_edge: bottom_edge, left_edge: right_edge].filled(fill_value=0.0)
        # Check if shape bbox aligns with any of our reference dataset edges
        # if 0 in new_edges or new_mask.shape[1] - 1 == [bottom_edge] or new_mask.shape[2] - 1 == right_edge:
        #     logging.warning(f'edge of bounding box aligns with edge of reference dataset! Check extents!')
        # # logging.info(f'added bbox to mask: mask_va=1, bbox_val=0, no_data_val={self.no_data_value}, '
        # #              f'slice_data(top,bot,left,right)='
        # #              f'{",".join([str(i) for i in get_human_bbox(new_edges, new_mask.shape)])}')
        self.mask_array = new_mask
        self.bbox_mask = self._find_bbox()
        self.bbox_edges = self.find_mask_edges(self.bbox_mask)
        return new_mask, new_edges

    def calculate_new_dimensions(self, len_x, len_y, side_multiple=32):
        """ adjust the dimensions of an existing bbox to make it a multiple of side_multiple

        @param len_x: existing length in x direction
        @param len_y: existing length in y direction
        @param side_multiple: integer that final x and y should be a multiple of
        @return: new padding values and new overall dimensions for the bbox
        """
        # add computational grid cell to make dimensions as multiple of side_multiple (nicer PxQxR)
        new_len_y = ((len_y // side_multiple) + 1) * side_multiple
        top_pad = (new_len_y - len_y) // 2
        bottom_pad = new_len_y - len_y - top_pad
        new_len_x = ((len_x // side_multiple) + 1) * side_multiple
        left_pad = (new_len_x - len_x) // 2
        right_pad = new_len_x - len_x - left_pad
        logging.info(f'calculated new dimensions with side_multiple={str(side_multiple)},'
                     f' old x_len={len_x}, old y_len={len_y}. '
                     f'New dims(x,y) = {",".join([str(new_len_x), str(new_len_y)])}, '
                     f'padding(top,bot,left,right)='
                     f'{",".join([str(top_pad), str(bottom_pad), str(left_pad), str(right_pad)])}')
        return top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y

    def calculate_buffer_edges(self, min_x, min_y, max_x, max_y, padding):
        """ add a buffer/padding to the given dimensions

        @param min_x: left edge of box
        @param min_y: top edge of box
        @param max_x: right edge of box
        @param max_y: bottom edge of box
        @param padding: array of padding values to add to each dimension
        @return: array of expanded bounding box dimensions [top, bot, left, right]
        """
        # TODO These max_y and max_x +1's, why?
        top_edge = min_y - padding[0]
        bottom_edge = max_y + padding[1] + 1
        left_edge = min_x - padding[2]
        right_edge = max_x + padding[3] + 1
        logging.info(f'calculated new mask edges original (top,bot,left,right)='
                     f'{",".join([str(i) for i in [min_y, max_y, min_x, max_x]])} padding={padding}, '
                     f'new edges={",".join([str(i) for i in [top_edge, bottom_edge, left_edge, right_edge]])}')
        if left_edge < 0 or top_edge < 0:
            logging.warning(f'found a negative minimum edge! Undefined behavior ahead!')
        return [top_edge, bottom_edge, left_edge, right_edge]

    def find_mask_edges(self, mask, mask_val=1):
        """ Identify the edges of the mask

        @param mask: numpy mask array representing full domain mask
        @param mask_val: value to match in the mask
        @return: bounding box of the mask inside the larger area
        """
        _, yy, xx = np.where(~mask.mask == mask_val)
        min_x = min(xx)
        min_y = min(yy)
        max_x = max(xx)
        max_y = max(yy)
        logging.info(
            f'located mask edges at (top,bot,left,right)='
            f'{",".join([str(i) for i in self.get_human_bbox([min_y, max_y, min_x, max_x], mask.shape)])}')
        return min_y, max_y, min_x, max_x

    def get_human_bbox(self, bbox, shape):
        """ convert from 0,0 in upper left to 0,0 in lower left, as a human would expect when visualizing

        @param bbox: array specifying the bounding box [top, bot, left, right]
        @param shape: tuple describing the shape of the larger domain (z, y, x)
        @return: array of edges [top, bot, left, right]
        """
        human_bbox = [shape[1] - bbox[0], shape[1] - bbox[1], bbox[2], bbox[3]]
        human_bbox = [human_bbox[1], human_bbox[0] + 1, human_bbox[2] + 1, human_bbox[3] + 2]
        logging.info(f'converted system bbox {bbox} inside shape {shape} to human bbox {human_bbox}')
        human_bbox = [human_bbox[3], human_bbox[0], human_bbox[3]-human_bbox[2], human_bbox[1] - human_bbox[0]]
        return human_bbox

    def calculate_new_geom(self, min_x, min_y, old_geom):
        """ calculate a new geometry based on an old geometry and new minimum point

        @param min_x: the minimum x value of the new geometry
        @param min_y: the minimum y value of the new geometry
        @param old_geom: array formatted for gdal geometry definitions
        @return: array formatted for gdal geometry with new extents
        """
        # TODO: Why old code had (min_x +1) ? Seemed to shift the tif geo location by 1 in each direction?
        new_x = old_geom[0] + (old_geom[1] * min_x)
        new_y = old_geom[3] + (old_geom[5] * min_y)
        new_geom = (new_x, old_geom[1], old_geom[2], new_y, old_geom[4], old_geom[5])
        logging.info(f'created new geometry from edge position and old geometry:'
                     f'old_geom={old_geom}, x_edge={min_x}, y_edge={min_y},'
                     f'new_geom={new_geom}')
        return new_geom

    def write_mask_to_tif(self, filename):
        write_array_to_geotiff(filename, self.mask_array, self.mask_tif.GetGeoTransform(),
                               self.mask_tif.GetProjection(), no_data=self.no_data_value)

    def write_bbox(self, filename):
        write_bbox(self.get_human_bbox(self.bbox_edges, self.mask_shape), filename)
