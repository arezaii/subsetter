import gdal
import ogr
import os
import logging
from pf_subsetter import TIF_NO_DATA_VALUE_OUT as NO_DATA
from pf_subsetter.mask import SubsetMask

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
        self.subset_mask = None

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
        self.subset_mask = SubsetMask(tif_path)
        return tif_path

    def rasterize_shapefile_to_disk(self, out_dir=None, out_name=None, x_pad=0, y_pad=0, attribute_name='OBJECTID',
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
        self.reproject_and_mask(attribute_ids=attribute_ids, attribute_name=attribute_name)
        self.subset_mask.add_bbox_to_mask(x_pad=x_pad, y_pad=y_pad)
        self.subset_mask.write_mask_to_tif(filename=os.path.join(out_dir, out_name))
        self.subset_mask.write_bbox(os.path.join(out_dir, 'bbox.txt'))
        return self.subset_mask.mask_array
