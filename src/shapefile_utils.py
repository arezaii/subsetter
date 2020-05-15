import gdal
import ogr
from pathlib import Path
import os
import logging
from global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA


class ShapefileRasterizer:

    def __init__(self, shapefile_path, output_path='.'):
        self.shapefile_path = shapefile_path
        self.check_shapefile_parts()
        self.output_path = output_path
        self.shapefile_name = Path(shapefile_path).stem

    def check_shapefile_parts(self):
        shape_parts = [Path(self.shapefile_path).stem + x for x in ['.shp', '.dbf', '.prj', '.shx', '.sbx', '.sbn']]
        for shp_component_file in shape_parts:
            if not os.path.isfile(os.path.join(Path(self.shapefile_path).parent, shp_component_file)):
                print(f'warning: Missing {shp_component_file}')

    def reproject_and_mask(self, ds_ref, dtype=gdal.GDT_Int32, no_data=NO_DATA, shape_field='OBJECTID'):
        """
        Given an input shapefile, convert to an array in the same projection as the reference datasource
        :param shapefile: the ERSI shapefile as input
        :param ds_ref: the reference datasource to project to
        :param dtype: datatype for gdal
        :param no_data: no data value for cells
        :shape_field: attribute name to extract from shapefile
        :return: the path (virtual) to the tif file
        """
        geom_ref = ds_ref.GetGeoTransform()
        shape_name = self.shapefile_name
        tif_path = f'/vsimem/{shape_name}.tif'
        target_ds = gdal.GetDriverByName('GTiff').Create(tif_path,
                                                         ds_ref.RasterXSize,
                                                         ds_ref.RasterYSize,
                                                         1, dtype)
        target_ds.SetProjection(ds_ref.GetProjection())
        target_ds.SetGeoTransform(geom_ref)
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
                         f'to \n {ds_ref.GetProjectionRef()}')
        return tif_path

    def write_to_tif(self, data_set, filename):
        dest_ds = gdal.GetDriverByName('GTiff').CreateCopy(filename, data_set, strict=1,
                                                           options=["COMPRESS=LZW", "NUM_THREADS=ALL_CPUS"])
        dest_ds.FlushCache()
