import gdal
import ogr
from pathlib import Path
import os


class ShapefileUtilities:

    def check_shapefile_parts(self, shapefile_path):
        shape_parts = [Path(shapefile_path).stem + x for x in ['.shp', '.dbf', '.prj', '.shx', '.sbx', '.sbn']]
        for shp_component_file in shape_parts:
            if not os.path.isfile(os.path.join(Path(shapefile_path).anchor, shp_component_file)):
                print(f'warning: Missing {shp_component_file}')

    def reproject(self, shapefile, ds_ref, dtype=gdal.GDT_Int16, no_data=-99):
        """
        Given an input shapefile, convert to an array in the same projection as the reference datasource
        :param shapefile: the ERSI shapefile as input
        :param ds_ref: the reference datasource to project to
        :param dtype: datatype for gdal
        :param no_data: no data value for cells
        :return: the path (virtual) to the tif file
        """
        geom_ref = ds_ref.GetGeoTransform()
        shape_name = Path(shapefile).stem
        tif_path = f'/vsimem/{shape_name}.tif'
        target_ds = gdal.GetDriverByName('GTiff').Create(tif_path,
                                                         ds_ref.RasterXSize,
                                                         ds_ref.RasterYSize,
                                                         1, dtype)
        target_ds.SetProjection(ds_ref.GetProjection())
        target_ds.SetGeoTransform(geom_ref)
        target_ds.GetRasterBand(1).SetNoDataValue(no_data)
        # shapefile
        shp_source = ogr.Open(shapefile)
        shp_layer = shp_source.GetLayer()
        # Rasterize layer
        if gdal.RasterizeLayer(target_ds, [1],
                               shp_layer,
                               options=["ATTRIBUTE=OBJECTID"]) != 0:
            raise Exception("error rasterizing layer: %s" % shp_layer)
        else:
            target_ds.FlushCache()
        return tif_path

    def write_to_tif(self, data_set, filename):
        dest_ds = gdal.GetDriverByName('GTiff').CreateCopy(filename, data_set, 0)
        dest_ds.FlushCache()