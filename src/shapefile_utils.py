import gdal
import ogr


class ShapefileUtilities:

    def reproject(self, shapefile, ds_ref, dtype=gdal.GDT_Int16, no_data=-99):
        """
        Given an input shapefile, convert to an array in the same projection as the reference datasource
        :param shapefile: the ERSI shapefile as input
        :param ds_ref: the reference datasource to project to
        :param dtype: datatype for gdal
        :param no_data: no data value for cells
        :return:
        """
        geom_ref = ds_ref.GetGeoTransform()
        target_ds = gdal.GetDriverByName('GTiff').Create('/vsimem/out.tif',
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

    def write_to_tif(self, data_set, filename):
        dest_ds = gdal.GetDriverByName('GTiff').CreateCopy(filename, data_set, 0)
        dest_ds.FlushCache()