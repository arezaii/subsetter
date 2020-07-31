import os
import unittest
from pathlib import Path
import gdal
import numpy as np
import src.file_io_tools as file_io_tools
import tests.test_files as test_files
from src.shapefile_utils import ShapefileRasterizer


class ShapefileReprojectCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.conus1_mask_datset = gdal.Open(test_files.conus1_mask)
        cls.conus2_mask_dataset = gdal.Open(test_files.conus2_mask)
        cls.shape_path = Path(test_files.huc10190004.get('shapefile')).parent
        cls.shape_name = Path(test_files.huc10190004.get('shapefile')).stem

    def test_reproject_conus1(self):
        utils = ShapefileRasterizer(self.shape_path, self.shape_name, self.conus1_mask_datset)
        tif_path = utils.reproject_and_mask()
        subset_mask = utils.subset_mask
        subset_mask.add_bbox_to_mask(side_length_multiple=32)
        subset_mask.write_mask_to_tif(filename='testout.tif')
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus1_mask')),
                                          file_io_tools.read_file('testout.tif')),
            'Should create a mask from CONUS1 with 1/0s')
        os.remove('testout.tif')

    def test_reproject_conus2(self):
        utils = ShapefileRasterizer(self.shape_path, self.shape_name, self.conus2_mask_dataset)
        tif_path = utils.reproject_and_mask()
        subset_mask = utils.subset_mask
        subset_mask.add_bbox_to_mask(side_length_multiple=32)
        subset_mask.write_mask_to_tif(filename='testout.tif')
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus2_mask')),
                                          file_io_tools.read_file('testout.tif')),
            'Should create a mask from CONUS2 with 1/0s')
        os.remove('testout.tif')

    def test_rasterize_no_data_values(self):
        rasterizer = ShapefileRasterizer(self.shape_path, shapefile_name=self.shape_name,
                                         reference_dataset=self.conus1_mask_datset, no_data=-9999999)
        rasterizer.reproject_and_mask()
        rasterizer.subset_mask.write_mask_to_tif(filename='testout.tif')
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus1_mask_-9999999')),
                                          file_io_tools.read_file('testout.tif')),
            'Should create a mask from CONUS1 with 1/-9999999')
        os.remove('testout.tif')


if __name__ == '__main__':
    unittest.main()
