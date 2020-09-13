from parflow.subset.utils.io import read_geotiff, write_array_to_geotiff, write_bbox, read_file
import numpy as np
import numpy.ma as ma
import logging
from parflow.subset.bbox import BBox


class SubsetMask:

    def __init__(self, tif_file, bbox_val=0):
        self.mask_tif = read_geotiff(tif_file)
        self.mask_array = read_file(tif_file)
        self.bbox_val = bbox_val
        self.inner_mask = self._find_inner_object() #tight crop
        self.bbox_mask = self._find_bbox() #bbox crop
        self.no_data_value = self.mask_tif.GetRasterBand(1).GetNoDataValue()
        self.inner_mask_edges = self.find_mask_edges(self.inner_mask) #edges
        self.bbox_edges = self.find_mask_edges(self.bbox_mask) #edges

    def _find_bbox(self):
        """ locate the outer bbox area

        @return: masked numpy array with full_dim_mask edges at outer area
        """
        mx = ma.masked_where(self.mask_array < self.bbox_val, self.mask_array)
        logging.info(f'SubsetMask located outer bbox in full_dim_mask array')
        return mx

    def _find_inner_object(self):
        """ locate the inner object

        @return: masked numpy array with tight full_dim_mask along shape border
        """
        mx = ma.masked_where(self.mask_array <= self.bbox_val, self.mask_array)
        logging.info(f'SubsetMask located inner full_dim_mask in full_dim_mask array')
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

    def add_bbox_to_mask(self, padding=(0, 0, 0, 0)):
        """ add the inner bounding box of 0's to the reprojected full_dim_mask. This will expand the bounding box of the
        clip so that the full_dim_mask is centered in the bbox and the bbox edges expand proportionally in each direction
        to make the final bbox edges a multiple of the side_length_multiple argument

        @param tiff_path: path to the tiff file that defines the full_dim_mask with no_data and 1
        @param padding: optional padding to add as 0's around full_dim_mask. css style (top,right,bottom,left)
        @return: 3d array with no data outside the bbox, 0 inside bbox, and 1 in full_dim_mask area, bounding box values
        """

        min_y, max_y, min_x, max_x = self.inner_mask_edges

        new_mask = self.inner_mask.filled(fill_value=self.no_data_value)

        new_edges = [max(min_y - padding[2], 0), min(max_y + padding[0] + 1, self.mask_array.shape[1]),
                     max(min_x - padding[3], 0), min(max_x + padding[1] + 1, self.mask_array.shape[2])]
        bottom_edge, top_edge, left_edge, right_edge = new_edges
        new_mask[:, bottom_edge: top_edge, left_edge: right_edge] =\
            self.inner_mask[:, bottom_edge: top_edge, left_edge: right_edge].filled(fill_value=0.0)
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

    def find_mask_edges(self, full_dim_mask, mask_val=1):
        """ Identify the edges of the mask

        @param full_dim_mask: numpy mask array representing full domain mask
        @param mask_val: value to match in the mask
        @return: bounding box of the mask inside the larger area
        """
        _, yy, xx = np.where(~full_dim_mask.mask == mask_val)
        min_x = min(xx)
        min_y = min(yy)
        max_x = max(xx)
        max_y = max(yy)
        # logging.info(
        #     f'located full_dim_mask edges at (top,bot,left,right)='
        #     f'{",".join([str(i) for i in self.get_human_bbox([min_y, max_y, min_x, max_x], full_dim_mask.shape)])}')
        return min_y, max_y, min_x, max_x

    def get_bbox(self):
        return BBox(self.inner_mask_edges[2] + 1, self.inner_mask_edges[0] + 1,
                    self.inner_mask_shape[1], self.inner_mask_shape[0])

    def get_human_bbox(self):
        """ return the x1, y1, nx, ny as you would see in bbox.txt
        @return: array of edges [x1, y1, nx, ny]
        """
        return self.get_bbox().get_human_bbox()

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
        write_bbox(self.get_human_bbox(), filename)