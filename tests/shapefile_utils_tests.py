import os
import unittest
from pathlib import Path
import numpy as np
import parflow.subset.utils.io as file_io_tools
import tests.test_files as test_files
from parflow.subset.rasterizer import ShapefileRasterizer


class ShapefileReprojectCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.conus1_mask_datset = file_io_tools.read_geotiff(test_files.conus1_mask.as_posix())
        cls.conus2_mask_dataset = file_io_tools.read_geotiff(test_files.conus2_mask.as_posix())
        cls.shape_path = Path(test_files.huc10190004.get('shapefile')).parent
        cls.shape_name = Path(test_files.huc10190004.get('shapefile')).stem

    def test_reproject_conus1(self):
        rasterizer = ShapefileRasterizer(self.shape_path, self.shape_name, self.conus1_mask_datset)
        rasterizer.reproject_and_mask()
        subset_mask = rasterizer.subset_mask
        subset_mask.add_bbox_to_mask()
        subset_mask.write_mask_to_tif(filename='testout.tif')
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus1_mask').as_posix()),
                                          file_io_tools.read_file('testout.tif')),
            'Should create a mask from CONUS1 with 1/0s')
        os.remove('testout.tif')

    def test_reproject_conus2(self):
        rasterizer = ShapefileRasterizer(self.shape_path, self.shape_name, self.conus2_mask_dataset)
        rasterizer.reproject_and_mask()
        subset_mask = rasterizer.subset_mask
        subset_mask.add_bbox_to_mask()
        subset_mask.write_mask_to_tif(filename='testout.tif')
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus2_mask').as_posix()),
                                          file_io_tools.read_file('testout.tif')),
            'Should create a mask from CONUS2 with 1/0s')
        os.remove('testout.tif')

    # def test_reproject_conus2_w_padding(self):
    # CUAHSI Subset reference does not match subset tool from repo
    #     rasterizer = ShapefileRasterizer(self.shape_path, self.shape_name, self.conus2_mask_dataset,no_data=-99)
    #     rasterizer.reproject_and_mask()
    #     subset_mask = rasterizer.subset_mask
    #     subset_mask.add_bbox_to_mask(padding=(1, 6, 1, 5))
    #     subset_mask.write_mask_to_tif(filename='testout.tif')
    #     test_ref_array = file_io_tools.read_file(test_files.cuahsi_ref_10190004.get('conus2_mask').as_posix())
    #     test_out_array = file_io_tools.read_file('testout.tif')
    #     test_ref_array = (test_ref_array > 0).astype(int)
    #     test_out_array = (test_out_array > 0).astype(int)
    #     self.assertIsNone(
    #         np.testing.assert_array_equal(test_ref_array, test_out_array),
    #         'Should create a mask from CONUS2 with 1/0s')
    #     #os.remove('testout.tif')

    def test_rasterize_no_data_values(self):
        rasterizer = ShapefileRasterizer(self.shape_path, shapefile_name=self.shape_name,
                                         reference_dataset=self.conus1_mask_datset, no_data=-9999999)
        rasterizer.reproject_and_mask()
        rasterizer.subset_mask.write_mask_to_tif(filename='testout.tif')
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(
                test_files.huc10190004.get('conus1_mask_-9999999').as_posix()),
                                          file_io_tools.read_file('testout.tif')),
            'Should create a mask from CONUS1 with 1/-9999999')
        os.remove('testout.tif')


if __name__ == '__main__':
    unittest.main()
