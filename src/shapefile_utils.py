import gdal
import ogr
import os
import logging
from src.global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA
from src.mask_utils import MaskUtils, calculate_buffer_edges, get_human_bbox
import numpy as np
import src.file_io_tools as file_io_tools

# TODO: Do we start with 0,0 or 1,1?
# TODO: Invert BBOX output values for Y axis so that 0,0 is lower left instead of upper left.


class ShapefileRasterizer:

    def __init__(self, input_path, shapefile_name, reference_dataset, no_data=NO_DATA, output_path='.'):
        """ Class for converting shapefiles to rasters for use as masks

        @param input_path: path to input files (shapefile set)
        @param shapefile_name: name of shapefile dataset
        @param reference_dataset: gdal dataset defining the overall domain
        @param no_data: value to write for no_data cells
        @param output_path: where to write the outputs
        """
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
        shape_parts = [".".join((self.shapefile_name, ext)) for ext in ['shp', 'dbf', 'prj', 'shx']]
        for shp_component_file in shape_parts:
            if not os.path.isfile(os.path.join(self.shapefile_path, shp_component_file)):
                logging.warning(f'Shapefile path missing {shp_component_file}')

    def reproject_and_mask(self, dtype=gdal.GDT_Int32, no_data=None, attribute_name='OBJECTID', attribute_ids=None):
        """
        @param attribute_ids: list of attribute ID values to select
        @param dtype: the datatype to write
        @param no_data: no_data value to use
        @param attribute_name: field in the shapefile to trace
        @return: path (virtual mem) to the reprojected mask
        """
        if attribute_ids is None:
            attribute_ids = [1]
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
        target_ds.GetRasterBand(1).SetNoDataValue(no_data)
        target_ds.GetRasterBand(1).Fill(no_data)
        # shapefile
        shp_source = ogr.Open(self.full_shapefile_path)
        shp_layer = shp_source.GetLayer()
        # TODO: How to detect if the shape geometries extend beyond our reference bounds?
        # Filter by the shapefile attribute IDs we want
        shp_layer.SetAttributeFilter(f'{attribute_name} in ({",".join([str(i) for i in attribute_ids])})')
        # Rasterize layer
        rtn_code = gdal.RasterizeLayer(target_ds, [1], shp_layer, burn_values=[1])
        if rtn_code == 0:
            target_ds.FlushCache()
            logging.info(f'reprojected shapefile from {str(shp_layer.GetSpatialRef()).replace(chr(10), "")} '
                         f'with extents {shp_layer.GetExtent()} '
                         f'to {self.ds_ref.GetProjectionRef()} with transform {self.ds_ref.GetGeoTransform()}')
        else:
            msg = f'error rasterizing layer: {shp_layer}, gdal returned non-zero value: {rtn_code}'
            logging.exception(msg)
            raise Exception(msg)
        return tif_path

    def add_bbox_to_mask(self, tiff_path, side_length_multiple=1):
        """ add the inner bounding box of 0's to the reprojected mask

        @param tiff_path: path to the tiff file that defines the mask with no_data and 1
        @param side_length_multiple: optional multiple to expand bounding box to
        @return: 3d array with no data outside the bbox, 0 inside bbox, and 1 in mask area, bounding box values
        """
        dataset = file_io_tools.read_geotiff(tiff_path)
        mask_array = dataset.ReadAsArray()
        mask_shape = mask_array.shape
        if len(mask_shape) == 2:
            mask_array = mask_array[np.newaxis, ...]
            logging.info(f'added z-axis to 2d mask_array, old shape (y,x)={mask_shape}, '
                         f'new shape (z,y,x)={mask_array.shape}')
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
        # Check if shape bbox aligns with any of our reference dataset edges
        if 0 in new_edges or mask_array.shape[1] - 1 == [bottom_edge] or mask_array.shape[2] - 1 == right_edge:
            logging.warning(f'edge of bounding box aligns with edge of reference dataset! Check extents!')
        logging.info(f'added bbox to mask: mask_va=1, bbox_val=0, no_data_val={self.no_data}, '
                     f'slice_data(top,bot,left,right)='
                     f'{",".join([str(i) for i in get_human_bbox(new_edges, new_mask.shape)])}')
        return new_mask, new_edges

    def write_to_tif(self, data_set, filename):
        """ write the mask data to geotif

        @param data_set: mask data to write
        @param filename: output path and filename
        @return: None
        """
        file_io_tools.write_array_to_geotiff(filename, data_set, self.ds_ref.GetGeoTransform(),
                                             self.ds_ref.GetProjection(), no_data=self.no_data)

    def rasterize_shapefile_to_disk(self, out_dir=None, out_name=None, side_multiple=1, attribute_name='OBJECTID',
                                    attribute_ids=None):
        """ rasterize a shapefile to disk in the projection and extents of the reference dataset

        @param out_dir: directory to write outputs
        @param out_name: filename for outputs
        @param side_multiple: optional side length multiple to expand bounding box to
        @param attribute_name: optional name of shapefile attribute to select on
        @param attribute_ids: optional list of attribute ids in shapefile to select for mask
        @return: 3d array with no_data to extents, 0 in bounding box, 1 in mask region
        """
        if attribute_ids is None:
            attribute_ids = [1]
        if out_name is None:
            out_name = f'{self.shapefile_name}.tif'
        if out_dir is None:
            out_dir = self.output_path
        raster_path = self.reproject_and_mask(attribute_ids=attribute_ids, attribute_name=attribute_name)
        final_mask, bbox = self.add_bbox_to_mask(raster_path, side_length_multiple=side_multiple)
        self.write_to_tif(filename=os.path.join(out_dir, out_name), data_set=final_mask)
        file_io_tools.write_bbox(get_human_bbox(bbox, final_mask.shape), os.path.join(out_dir, 'bbox.txt'))
        return final_mask
