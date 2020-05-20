import gdal
import ogr
import osr
from pathlib import Path
import os
import logging
from pyproj import Proj, transform
from global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA
from src.mask_utils import MaskUtils, find_mask_edges
import numpy as np
from src.file_io_tools import write_array_to_geotiff


class ShapefileRasterizer:

    def __init__(self, shapefile_path, reference_dataset, no_data=NO_DATA, output_path='.'):
        self.shapefile_path = shapefile_path
        self.check_shapefile_parts()
        self.output_path = output_path
        self.shapefile_name = Path(shapefile_path).stem
        self.ds_ref = reference_dataset
        self.no_data = no_data

    def check_shapefile_parts(self):
        shape_parts = [Path(self.shapefile_path).stem + x for x in ['.shp', '.dbf', '.prj', '.shx', '.sbx', '.sbn']]
        for shp_component_file in shape_parts:
            if not os.path.isfile(os.path.join(Path(self.shapefile_path).parent, shp_component_file)):
                print(f'warning: Missing {shp_component_file}')

    def reproject_and_mask(self, dtype=gdal.GDT_Int32, no_data=NO_DATA, shape_field='OBJECTID'):
        """
        Given an input shapefile, convert to an array in the same projection as the reference datasource
        :param dtype: datatype for gdal
        :param no_data: no data value for cells
        :param shape_field: attribute name to extract from shapefile
        :return: the path (virtual) to the tif file
        """
        geom_ref = self.ds_ref.GetGeoTransform()
        shape_name = self.shapefile_name
        tif_path = f'/vsimem/{shape_name}.tif'
        target_ds = gdal.GetDriverByName('GTiff').Create(tif_path,
                                                         self.ds_ref.RasterXSize,
                                                         self.ds_ref.RasterYSize,
                                                         1, dtype)
        target_ds.SetProjection(self.ds_ref.GetProjection())
        target_ds.SetGeoTransform(geom_ref)
        # TODO: Fix the no_data here to be from the class
        target_ds.GetRasterBand(1).SetNoDataValue(no_data)
        # shapefile
        shp_source = ogr.Open(self.shapefile_path)
        shp_layer = shp_source.GetLayer()
        # Rasterize layer
        if gdal.RasterizeLayer(target_ds, [1],
                               shp_layer,
                               options=[f'ATTRIBUTE={shape_field}'],
                               burn_values=[1.0]) != 0:
            raise Exception("error rasterizing layer: %s" % shp_layer)
        else:
            target_ds.FlushCache()
            logging.info(f'reprojected shapefile input from '
                         f'{shp_layer.GetSpatialRef()} \n '
                         f'to \n {self.ds_ref.GetProjectionRef()}')
        return tif_path

    def add_bbox_to_mask(self, tiff_path, side_length_multiple=1):
        dataset = gdal.Open(tiff_path)
        mask_array = dataset.ReadAsArray()
        if len(mask_array.shape) == 2:
            mask_array = mask_array[np.newaxis, ...]
        mask_utils = MaskUtils(mask_array)
        numpy_mask = mask_utils.find_inner_object()
        max_x, max_y, min_x, min_y = find_mask_edges(numpy_mask)
        new_dims = mask_utils.calculate_new_dimensions(len_x=(max_x - min_x) + 1,
                                                       len_y=(max_y - min_y) + 1,
                                                       side_multiple=side_length_multiple)
        top_pad, bottom_pad, left_pad, right_pad, new_len_x, new_len_y = new_dims
        new_mask = numpy_mask.filled(fill_value=NO_DATA)
        new_mask[:, min_y - top_pad: max_y + bottom_pad + 1, min_x - left_pad: max_x + right_pad + 1] =\
            numpy_mask[:, min_y - top_pad: max_y + bottom_pad + 1, min_x - left_pad: max_x + right_pad + 1].\
                filled(fill_value=0.0)
        return new_mask

    def write_to_tif(self, data_set, filename):
        write_array_to_geotiff(filename, data_set, self.ds_ref.GetGeoTransform(), self.ds_ref.GetProjection(),
                               no_data=self.no_data)

    def pixzone2latlon(self, xul, yul, dx, dy, x0, y0):
        lat = yul - dy*y0
        lon = xul + dx*x0
        return lat, lon

    def write_clm_lat_lon(self):
        inSRS_converter = osr.SpatialReference()  # makes an empty spatial ref object
        inSRS_converter.ImportFromWkt(self.ds_ref.GetProjection())  # populates the spatial ref object with our WKT SRS
        inSRS_forPyProj = inSRS_converter.ExportToProj4()  # Exports an SRS ref as a Proj4 string usable by PyProj
        inProj = Proj(inSRS_forPyProj)
        outProj = Proj(init='epsg:4326')
