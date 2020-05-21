import os
import unittest
import gdal
import numpy as np
from src.file_io_tools import read_file
from src.shapefile_utils import ShapefileRasterizer


class ShapefileReprojectCase(unittest.TestCase):

    def test_reproject_conus1(self):
        reference_dataset = gdal.Open("test_inputs/Domain_Blank_Mask.tif")
        utils = ShapefileRasterizer("test_inputs/WBDHU8.shp", reference_dataset)
        tif_path = utils.reproject_and_mask()
        mask_array = utils.add_bbox_to_mask(tif_path, side_length_multiple=32)
        utils.write_to_tif(data_set=mask_array, filename='testout.tif')
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus1_mask.tif').ReadAsArray(),
                                                        gdal.Open('testout.tif').ReadAsArray()),
                          'Should create a mask from CONUS1 with 1/0s')
        os.remove('testout.tif')

    def test_reproject_conus2(self):
        reference_dataset = gdal.Open("test_inputs/conus_1km_PFmask2.tif")
        utils = ShapefileRasterizer("test_inputs/WBDHU8.shp", reference_dataset)
        tif_path = utils.reproject_and_mask()
        mask_array = utils.add_bbox_to_mask(tif_path, side_length_multiple=32)
        utils.write_to_tif(data_set=mask_array, filename='testout.tif')
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus2_mask.tif').ReadAsArray(),
                                                        gdal.Open('testout.tif').ReadAsArray()),
                          'Should create a mask from CONUS2 with 1/0s')
        os.remove('testout.tif')

    def test_rasterize_no_data_values(self):
        reference_dataset = gdal.Open("test_inputs/Domain_Blank_Mask.tif")
        shapefile = 'test_inputs/WBDHU8.shp'
        rasterizer = ShapefileRasterizer(shapefile_path=shapefile,
                                         reference_dataset=reference_dataset)
        raster_path = rasterizer.reproject_and_mask()
        rasterizer.write_to_tif(data_set=read_file(raster_path), filename='testout.tif')
        self.assertIsNone(
            np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus_1_mask_999.tif').ReadAsArray(),
                                          gdal.Open('testout.tif').ReadAsArray()),
            'Should create a mask from CONUS1 with 1/-999')
        os.remove('testout.tif')


if __name__ == '__main__':
    unittest.main()
