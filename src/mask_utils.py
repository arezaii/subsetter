import logging
import numpy as np
import numpy.ma as ma
from src.global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA


def find_mask_edges(mask, mask_val=1):
    """
    Identify the edges of the mask
    :param:
    """
    _, yy, xx = np.where(~mask.mask == mask_val)
    min_x = min(xx)
    min_y = min(yy)
    max_x = max(xx)
    max_y = max(yy)
    logging.info(
        f'located mask edges at (top,bot,left,right)='
        f'{",".join([str(i) for i in get_human_bbox([min_y, max_y, min_x, max_x], mask.shape)])}')
    return max_x, max_y, min_x, min_y


def calculate_buffer_edges(min_x, min_y, max_x, max_y, padding):
    top_edge = min_y - padding[0]
    bottom_edge = max_y + padding[1] + 1
    left_edge = min_x - padding[2]
    right_edge = max_x + padding[3] + 1
    logging.info(f'calculated new mask edges original (top,bot,left,right)='
                 f'{",".join([str(i) for i in [min_y, max_y, min_x, max_x]])} padding={padding}, '
                 f'new edges={",".join([str(i) for i in [top_edge, bottom_edge, left_edge, right_edge]])}')
    if left_edge < 0 or top_edge < 0:
        logging.warning(f'found a negative minimum edge! Unxpected behavior ahead!')
    return [top_edge, bottom_edge, left_edge, right_edge]


def get_human_bbox(bbox, shape):
    return [shape[1] - bbox[0], shape[1] - bbox[1], bbox[2], bbox[3]]


class MaskUtils:
    def __init__(self, mask_data_array, bbox_val=0, no_data_threshold=NO_DATA):
        """

        """
        if not bbox_val > no_data_threshold:
            raise Exception("bbox identifier value should be > no data threshold")

        self.mask_data_array = mask_data_array
        self.bbox_val = bbox_val
        self.no_data_threshold = no_data_threshold
        self.bbox_crop = self._find_bbox()
        self.bbox_crop_edges = find_mask_edges(self.bbox_crop)
        self.inner_crop = self._find_inner_object()
        self.inner_crop_edges = find_mask_edges(self.inner_crop)

    def get_bbox_print(self):
        return get_human_bbox(self.bbox_crop_edges, self.mask_data_array.shape)

    def get_bbox_print_inner(self):
        return get_human_bbox(self.inner_crop_edges, self.mask_data_array.shape)

    def _find_bbox(self):
        mx = ma.masked_where(self.mask_data_array < self.bbox_val, self.mask_data_array)
        logging.info(f'located outer bbox in mask array')
        return mx

    def _find_inner_object(self):
        mx = ma.masked_where(self.mask_data_array <= self.bbox_val, self.mask_data_array)
        logging.info(f'located inner mask in mask array')
        return mx

    def calculate_new_geom(self, min_x, min_y, old_geom):
        # TODO: Why old code had (min_x +1) ? Seemed to shift the tif geo location by 1 in each direction?
        new_x = old_geom[0] + (old_geom[1] * min_x)
        new_y = old_geom[3] + (old_geom[5] * min_y)
        new_geom = (new_x, old_geom[1], old_geom[2], new_y, old_geom[4], old_geom[5])
        logging.info(f'created new geometry from edge position and old geometry:'
                     f'old_geom={old_geom}, x_edge={min_x}, y_edge={min_y},'
                     f'new_geom={new_geom}')
        return new_geom

    def calculate_new_dimensions(self, len_x, len_y, side_multiple=32):
        # add grid cell to make dimensions as multiple of 32 (nicer PxQxR)
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
