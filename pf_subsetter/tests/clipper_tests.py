import unittest
from pf_subsetter.clipper import MaskClipper, BoxClipper
import pf_subsetter.utils.io as file_io_tools
from pf_subsetter.mask import SubsetMask
import numpy as np
import pf_subsetter.tests.test_files as test_files
import os


class RegressionClipTests(unittest.TestCase):
    """
    Regression tests to verify subsetting can correctly clip a data file,
    correctly produces the subset clip,
    and correctly writes the bounding box file
    """

    def test_subset_dem_to_tif_conus1(self):
        data_array = file_io_tools.read_file(test_files.conus1_dem.as_posix())
        my_mask = SubsetMask(test_files.huc10190004.get('conus1_mask').as_posix())
        clipper = MaskClipper(subset_mask=my_mask, no_data_threshold=-1)
        return_arr, new_geom, new_mask, bbox = clipper.subset(data_array)
        file_io_tools.write_array_to_geotiff("conus_1_clip_dem_test.tif",
                                             return_arr, new_geom, my_mask.mask_tif.GetProjection())

        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus1_dem').as_posix()),
                                          file_io_tools.read_file('conus_1_clip_dem_test.tif')),
            'Clipping DEM matches reference')
        os.remove('conus_1_clip_dem_test.tif')

        file_io_tools.write_array_to_geotiff("conus1_mask_crop.tif",
                                             new_mask, new_geom, my_mask.mask_tif.GetProjection())

        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus1_inset').as_posix()),
                                          file_io_tools.read_file('conus1_mask_crop.tif')),
            'Subset results in reference inset mask')
        os.remove('conus1_mask_crop.tif')

        file_io_tools.write_bbox(bbox, 'bbox_conus1.txt')

        self.assertListEqual(file_io_tools.read_bbox('bbox_conus1.txt'), test_files.huc10190004.get('conus1_bbox'),
                             'Subset writes correct bounding box file')
        os.remove('bbox_conus1.txt')

    def test_subset_tif_conus2(self):
        data_array = file_io_tools.read_file(test_files.conus2_dem.as_posix())
        my_mask = SubsetMask(test_files.huc10190004.get('conus2_mask').as_posix())
        clipper = MaskClipper(subset_mask=my_mask, no_data_threshold=-1)
        return_arr, new_geom, new_mask, bbox = clipper.subset(data_array)
        file_io_tools.write_array_to_geotiff("conus_2_clip_dem_test.tif",
                                             return_arr, new_geom, my_mask.mask_tif.GetProjection())
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus2_dem').as_posix()),
                                          file_io_tools.read_file('conus_2_clip_dem_test.tif')),
            'Clipping DEM matches reference')
        os.remove('conus_2_clip_dem_test.tif')

        file_io_tools.write_array_to_geotiff("conus2_mask_crop.tif",
                                             new_mask, new_geom, my_mask.mask_tif.GetProjection())
        self.assertIsNone(
            np.testing.assert_array_equal(file_io_tools.read_file(test_files.huc10190004.get('conus2_inset').as_posix()),
                                          file_io_tools.read_file('conus2_mask_crop.tif')),
            'Subset results in reference inset mask')
        os.remove('conus2_mask_crop.tif')
        file_io_tools.write_bbox(bbox, 'bbox_conus2_full.txt')
        self.assertListEqual(file_io_tools.read_bbox('bbox_conus2_full.txt'), test_files.huc10190004.get('conus2_bbox'),
                             'Subset writes correct bounding box file')
        os.remove('bbox_conus2_full.txt')

    def test_box_clip(self):
        data_array = file_io_tools.read_file(test_files.conus1_dem.as_posix())
        box_clipper = BoxClipper(ref_array=data_array)
        #box_clipper.set_bbox(x=1, y=1, nx=3342, ny=1888)
        subset = box_clipper.clip_ref_array()
        self.assertEqual(1, subset.shape[0])
        self.assertEqual(3342, subset.shape[2])
        self.assertEqual(1888, subset.shape[1])
        self.assertIsNone(np.testing.assert_array_equal(data_array, subset),
                          'selecting the whole region should return exactly what you would expect')

        box_clipper.update_bbox(x=10, y=10, nx=3332, ny=1878)
        subset2 = box_clipper.clip_ref_array()
        self.assertEqual(1, subset2.shape[0])
        self.assertEqual(3332, subset2.shape[2])
        self.assertEqual(1878, subset2.shape[1])

        box_clipper.update_bbox(x=10, y=10, nx=201, ny=20)
        subset3 = box_clipper.clip_ref_array()
        self.assertEqual(1, subset3.shape[0])
        self.assertEqual(201, subset3.shape[2])
        self.assertEqual(20, subset3.shape[1])

        box_clipper.update_bbox(x=1, y=1, nx=500, ny=300)
        subset4 = box_clipper.clip_ref_array()
        self.assertEqual(1, subset4.shape[0])
        self.assertEqual(500, subset4.shape[2])
        self.assertEqual(300, subset4.shape[1])

        # create a 3d array for testing, z=4, y=3, x=2
        data_array2 = np.array([[[1,2],[3,4,],[5,6]],
                               [[7,8],[9,10],[11,12]],
                               [[13,14],[15,16],[17,18]],
                               [[19,20], [21,22],[23,24]]])

        box_clipper2 = BoxClipper(ref_array=data_array2)
        subset5 = box_clipper2.clip_ref_array()
        self.assertIsNone(np.testing.assert_array_equal(data_array2, subset5))
        self.assertEqual(1, subset5[0,0,0])
        self.assertEqual(22, subset5[3,1,1])

        box_clipper2.update_bbox(x=1, y=1, nx=1, ny=2)
        subset6 = box_clipper2.clip_ref_array()
        self.assertEqual(3, subset6[0,0,0])
        self.assertEqual(15, subset6[2,0,0])
        self.assertEqual(17, subset6[2,1,0])

        box_clipper2.update_bbox(z=1, nz=1)
        subset7 = box_clipper2.clip_ref_array()


if __name__ == '__main__':
    unittest.main()
