import unittest
from src.shapefile_utils import ShapefileUtilities
import gdal
import numpy as np
import os


class ShapefileReprojectCase(unittest.TestCase):
    def test_reproject_conus1(self):
        utils = ShapefileUtilities()
        reference_dataset = gdal.Open("../CONUS1_Inputs/Domain_Blank_Mask.tif")
        utils.reproject("../test_inputs/WBDHU8.shp", reference_dataset)
        utils.write_to_tif(gdal.Open("/vsimem/out.tif"), 'testout.tif')
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('../test_inputs/test_truth.tif').ReadAsArray(),
                                gdal.Open('testout.tif').ReadAsArray()))
        os.remove('testout.tif')


if __name__ == '__main__':
    unittest.main()
