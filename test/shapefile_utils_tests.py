import unittest
from src.shapefile_utils import ShapefileRasterizer
import gdal
import numpy as np
import os


class ShapefileReprojectCase(unittest.TestCase):

    def test_reproject_conus1(self):
        utils = ShapefileRasterizer("test_inputs/WBDHU8.shp")
        reference_dataset = gdal.Open("CONUS1_Inputs/Domain_Blank_Mask.tif")
        tif_path = utils.reproject_and_mask(reference_dataset, no_data=0)
        utils.write_to_tif(gdal.Open(tif_path), 'testout.tif')
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus1_mask.tif').ReadAsArray(),
                                gdal.Open('testout.tif').ReadAsArray()))
        os.remove('testout.tif')

    def test_reproject_conus2(self):
        utils = ShapefileRasterizer("test_inputs/WBDHU8.shp")
        reference_dataset = gdal.Open("CONUS2_Inputs/conus_1km_PFmask2.tif")
        tif_path = utils.reproject_and_mask(reference_dataset, no_data=0)
        utils.write_to_tif(gdal.Open(tif_path), 'testout.tif')
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus2_mask.tif').ReadAsArray(),
                                gdal.Open('testout.tif').ReadAsArray()))
        os.remove('testout.tif')


if __name__ == '__main__':
    unittest.main()
