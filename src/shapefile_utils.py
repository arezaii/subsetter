import gdal
import ogr
import os
import logging
from src.global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA
from src.mask_utils import MaskUtils, calculate_buffer_edges
import numpy as np
import src.file_io_tools as file_io_tools


class ShapefileRasterizer:

    def __init__(self, input_path, shapefile_name, reference_dataset, no_data=NO_DATA, output_path='.'):
        if no_data in [0, 1]:
            raise Exception(f'ShapfileRasterizer: '
                            f'Do not used reserved values 1 or 0 for no_data value: got no_data={no_data}')
        self.shapefile_path = input_path
        self.output_path = output_path
        self.shapefile_name = shapefile_name
        self.ds_ref = reference_dataset
        self.no_data = no_data
        self.full_shapefile_path = os.path.join(self.shapefile_path, '.'.join((self.shapefile_name, 'shp')))
        self.check_shapefile_parts()

    def check_shapefile_parts(self):
        shape_parts = [".".join((self.shapefile_name, ext)) for ext in ['shp', 'dbf', 'prj', 'shx', 'sbx', 'sbn']]
        for shp_component_file in shape_parts:
            if not os.path.isfile(os.path.join(self.shapefile_path, shp_component_file)):
                logging.warning(f'Shapefile path missing {shp_component_file}')

    def reproject_and_mask(self, dtype=gdal.GDT_Int32, no_data=None, shape_field='OBJECTID'):
        """
        Given an input shapefile, convert to an array in the same projection as the reference datasource
        :param dtype: datatype for gdal
        :param no_data: no data value for cells
        :param shape_field: attribute name to extract from shapefile
        :return: the path (virtual) to the tif file
        """
        if no_data is None:
            no_data = self.no_data
        geom_ref = self.ds_ref.GetGeoTransform()
        tif_path = f'/vsimem/{self.shapefile_name}.tif'
        target_ds = gdal.GetDriverByName('GTiff').Create(tif_path,
                                                         self.ds_ref.RasterXSize,
                                                         self.ds_ref.RasterYSize,
                                                         1, dtype)
        target_ds.SetProjection(self.ds_ref.GetProjection())
        target_ds.SetGeoTransform(geom_ref)
        # TODO: Fix the no_data here to be from the class
        target_ds.GetRasterBand(1).SetNoDataValue(no_data)
        # shapefile
        shp_source = ogr.Open(self.full_shapefile_path)
        shp_layer = shp_source.GetLayer()
        # Rasterize layer
        if gdal.RasterizeLayer(target_ds, [1],
                               shp_layer,
                               options=[f'ATTRIBUTE={shape_field}'],
                               burn_values=[1.0]) != 0:
            raise Exception("error rasterizing layer: %s" % shp_layer)
        else:
            target_ds.FlushCache()
            logging.info(f'reprojected shapefile from {str(shp_layer.GetSpatialRef()).replace(chr(10),"")} '
                         f'with extents {shp_layer.GetExtent()} '
                         f'to {self.ds_ref.GetProjectionRef()} with transform {self.ds_ref.GetGeoTransform()}')
        return tif_path

    def add_bbox_to_mask(self, tiff_path, side_length_multiple=1):
        dataset = file_io_tools.read_geotiff(tiff_path)
        mask_array = dataset.ReadAsArray()
        mask_shape = mask_array.shape
        if len(mask_shape) == 2:
            mask_array = mask_array[np.newaxis, ...]
            logging.info(f'added z-axis to 2d mask_array, old dims={mask_shape}, new dims={mask_array.shape}')
        mask_utils = MaskUtils(mask_array)
        numpy_mask = mask_utils.inner_crop
        max_x, max_y, min_x, min_y = mask_utils.inner_crop_edges
        new_dims = mask_utils.calculate_new_dimensions(len_x=(max_x - min_x) + 1,
                                                       len_y=(max_y - min_y) + 1,
                                                       side_multiple=side_length_multiple)
        top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y = new_dims
        new_mask = numpy_mask.filled(fill_value=self.no_data)
        new_edges = calculate_buffer_edges(min_x, min_y, max_x, max_y, [top_pad, bottom_pad, left_pad, right_pad])
        top_edge, bottom_edge, left_edge, right_edge = new_edges
        new_mask[:, top_edge: bottom_edge, left_edge: right_edge] =\
            numpy_mask[:, top_edge: bottom_edge, left_edge: right_edge].filled(fill_value=0.0)

        logging.info(f'added bbox to mask: mask_va=1, bbox_val=0, no_data_val={self.no_data}, '
                     f'slice_data(top,bot,left,right)='
                     f'{",".join([str(i) for i in [top_edge, bottom_edge, left_edge, right_edge]])}')
        return new_mask, new_edges

    def write_to_tif(self, data_set, filename):
        file_io_tools.write_array_to_geotiff(filename, data_set, self.ds_ref.GetGeoTransform(),
                                             self.ds_ref.GetProjection(), no_data=self.no_data)

    def rasterize_shapefile_to_disk(self, out_dir=None, out_name=None, side_multiple=1):
        if out_name is None:
            out_name = f'{self.shapefile_name}.tif'
        if out_dir is None:
            out_dir = self.output_path
        raster_path = self.reproject_and_mask()
        final_mask, bbox = self.add_bbox_to_mask(raster_path, side_length_multiple=side_multiple)
        self.write_to_tif(filename=os.path.join(out_dir, out_name), data_set=final_mask)
        file_io_tools.write_bbox(bbox, os.path.join(out_dir, 'bbox.txt'))
        return final_mask


