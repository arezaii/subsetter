import unittest
from pf_subsetter.clipper import Clipper
import pf_subsetter.file_io_tools as file_io_tools
from pf_subsetter.subset_mask import SubsetMask
import numpy as np
import tests.test_files as test_files
import os


class RegressionClipTests(unittest.TestCase):
    """
    Regression tests to verify subsetting can correctly clip a data file,
    correctly produces the subset clip,
    and correctly writes the bounding box file
    """

    def test_subset_dem_to_tif_conus1(self):
        data_array = file_io_tools.read_file(test_files.conus1_dem)
        my_mask = SubsetMask(test_files.huc10190004.get('conus1_mask'))
        clipper = Clipper(subset_mask=my_mask, no_data_threshold=-1)
        return_arr, new_geom, new_mask, bbox = clipper.subset(data_array)
        file_io_tools.write_array_to_geotiff("conus_1_clip_dem_test.tif",
                                             return_arr, new_geom, my_mask.mask_tif.GetProjection())

        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus1_dem')),
                                          file_io_tools.read_file('conus_1_clip_dem_test.tif')),
            'Clipping DEM matches reference')
        os.remove('conus_1_clip_dem_test.tif')

        file_io_tools.write_array_to_geotiff("conus1_mask_crop.tif",
                                             new_mask, new_geom, my_mask.mask_tif.GetProjection())

        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus1_inset')),
                                          file_io_tools.read_file('conus1_mask_crop.tif')),
            'Subset results in reference inset mask')
        os.remove('conus1_mask_crop.tif')

        file_io_tools.write_bbox(bbox, 'bbox_conus1.txt')

        self.assertListEqual(file_io_tools.read_bbox('bbox_conus1.txt'), test_files.huc10190004.get('conus1_bbox'),
                             'Subset writes correct bounding box file')
        os.remove('bbox_conus1.txt')

    def test_subset_tif_conus2(self):
        data_array = file_io_tools.read_file(test_files.conus2_dem)
        my_mask = SubsetMask(test_files.huc10190004.get('conus2_mask'))
        clipper = Clipper(subset_mask=my_mask, no_data_threshold=-1)
        return_arr, new_geom, new_mask, bbox = clipper.subset(data_array)
        file_io_tools.write_array_to_geotiff("conus_2_clip_dem_test.tif",
                                             return_arr, new_geom, my_mask.mask_tif.GetProjection())
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus2_dem')),
                                          file_io_tools.read_file('conus_2_clip_dem_test.tif')),
            'Clipping DEM matches reference')
        os.remove('conus_2_clip_dem_test.tif')

        file_io_tools.write_array_to_geotiff("conus2_mask_crop.tif",
                                             new_mask, new_geom, my_mask.mask_tif.GetProjection())
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus2_inset')),
                                          file_io_tools.read_file('conus2_mask_crop.tif')),
            'Subset results in reference inset mask')
        os.remove('conus2_mask_crop.tif')
        file_io_tools.write_bbox(bbox, 'bbox_conus2_full.txt')
        self.assertListEqual(file_io_tools.read_bbox('bbox_conus2_full.txt'), test_files.huc10190004.get('conus2_bbox'),
                             'Subset writes correct bounding box file')
        os.remove('bbox_conus2_full.txt')


if __name__ == '__main__':
    unittest.main()
