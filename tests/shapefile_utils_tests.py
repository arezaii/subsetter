import os
import unittest
import gdal
import numpy as np
from src.file_io_tools import read_file
from src.shapefile_utils import ShapefileRasterizer
import tests.test_files as test_files
from pathlib import Path


class ShapefileReprojectCase(unittest.TestCase):

    def test_reproject_conus1(self):
        reference_dataset = gdal.Open(test_files.conus1_mask)
        shape_path = Path(test_files.huc10190004.get('shapefile')).parent
        shape_name = Path(test_files.huc10190004.get('shapefile')).stem
        utils = ShapefileRasterizer(shape_path, shape_name, reference_dataset)
        tif_path = utils.reproject_and_mask()
        mask_array, bbox = utils.add_bbox_to_mask(tif_path, side_length_multiple=32)
        utils.write_to_tif(data_set=mask_array, filename='testout.tif')
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open(test_files.huc10190004.get('conus1_mask')).ReadAsArray(),
                                                        gdal.Open('testout.tif').ReadAsArray()),
                          'Should create a mask from CONUS1 with 1/0s')
        os.remove('testout.tif')

    def test_reproject_conus2(self):
        reference_dataset = gdal.Open(test_files.conus2_mask)
        shape_path = Path(test_files.huc10190004.get('shapefile')).parent
        shape_name = Path(test_files.huc10190004.get('shapefile')).stem
        utils = ShapefileRasterizer(shape_path, shape_name, reference_dataset)
        tif_path = utils.reproject_and_mask()
        mask_array, bbox = utils.add_bbox_to_mask(tif_path, side_length_multiple=32)
        utils.write_to_tif(data_set=mask_array, filename='testout.tif')
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open(test_files.huc10190004.get('conus2_mask')).ReadAsArray(),
                                                        gdal.Open('testout.tif').ReadAsArray()),
                          'Should create a mask from CONUS2 with 1/0s')
        os.remove('testout.tif')

    def test_rasterize_no_data_values(self):
        reference_dataset = gdal.Open(test_files.conus1_mask)
        shape_path = Path(test_files.huc10190004.get('shapefile')).parent
        shape_name = Path(test_files.huc10190004.get('shapefile')).stem
        rasterizer = ShapefileRasterizer(shape_path, shapefile_name=shape_name, reference_dataset=reference_dataset,
                                         no_data=-9999999)
        raster_path = rasterizer.reproject_and_mask()
        rasterizer.write_to_tif(data_set=read_file(raster_path), filename='testout.tif')
        self.assertIsNone(
            np.testing.assert_array_equal(gdal.Open(test_files.huc10190004.get('conus1_mask_-9999999')).ReadAsArray(),
                                          gdal.Open('testout.tif').ReadAsArray()),
            'Should create a mask from CONUS1 with 1/-9999999')
        os.remove('testout.tif')


if __name__ == '__main__':
    unittest.main()
