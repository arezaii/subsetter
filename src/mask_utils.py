import numpy as np
import numpy.ma as ma
from src.global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA


def find_mask_edges(mask):
    _, yy, xx = np.where(~mask.mask == 1)
    min_x = min(xx)
    min_y = min(yy)
    max_x = max(xx)
    max_y = max(yy)
    return max_x, max_y, min_x, min_y


class MaskUtils:
    def __init__(self, mask_data_array, bbox_val=0, no_data_threshold=NO_DATA):
        """
        assumed that bbox_val is greater than or equal to no_data_threshold
        """
        if not bbox_val > no_data_threshold:
            raise Exception("bbox identifier value should be > no data threshold")

        self.mask_data_array = mask_data_array
        self.bbox_val = bbox_val
        self.no_data_threshold = no_data_threshold
        self.bbox_crop = self.find_bbox()
        self.inner_crop = self.find_inner_object()

    def find_bbox(self):
        return ma.masked_where(self.mask_data_array < self.bbox_val, self.mask_data_array)

    def find_inner_object(self):
        return ma.masked_where(self.mask_data_array <= self.bbox_val, self.mask_data_array)

    # def clip_mask(self, side_multiple=1):
    #     """
    #     clip the input mask (full extents) to extents of masked data plus an edge buffer
    #     creates a mask of 1 for valid data and 0 for no_data
    #     """
    #     max_x, max_y, min_x, min_y = find_mask_edges(self.inner_crop)
    #     len_y = max_y - min_y + 1
    #     len_x = max_x - min_x + 1
    #     # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
    #     top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y = self.calculate_new_dimensions(len_x, len_y,
    #                                                                                                    side_multiple)
    #     new_mask = self.inner_crop[:, min_y - top_pad:max_y + bottom_pad + 1, min_x - left_pad:max_x + right_pad + 1]
    #     return new_mask.filled(fill_value=0), min_x, min_y, max_x, max_y, top_pad, bottom_pad, left_pad, right_pad

    def calculate_new_geom(self, min_x, min_y, old_geom):
        new_x = old_geom[0] + old_geom[1] * (min_x + 1)
        new_y = old_geom[3] + old_geom[5] * (min_y + 1)
        new_geom = (new_x, old_geom[1], old_geom[2], new_y, old_geom[4], old_geom[5])
        return new_geom

    # def calculate_buffer_edges(self):
    #     top_edge = self.min_y - self.top_pad
    #     bottom_edge = self.max_y + self.bottom_pad + 1
    #     left_edge = self.min_x - self.left_pad
    #     right_edge = self.max_x + self.right_pad + 1
    #     return [top_edge, bottom_edge, left_edge, right_edge]

    def calculate_new_dimensions(self, len_x, len_y, side_multiple=32):
        # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
        new_len_y = ((len_y // side_multiple) + 1) * side_multiple
        top_pad = (new_len_y - len_y) // 2
        bottom_pad = new_len_y - len_y - top_pad
        new_len_x = ((len_x // side_multiple) + 1) * side_multiple
        left_pad = (new_len_x - len_x) // 2
        right_pad = new_len_x - len_x - left_pad
        return top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y



