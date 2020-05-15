import unittest
import gdal
from src.clipper import Clipper
from src.file_io_tools import read_file
from src.file_io_tools import write_array_to_geotiff
from src.file_io_tools import write_bbox
import numpy as np
from file_io_tools import read_bbox
import os


class MyTestCase(unittest.TestCase):
    def test_calculate_new_dims(self):
        mask = read_file('test_inputs/test_truth.tif')
        ref_ds = gdal.Open('CONUS1_Inputs/Domain_Blank_Mask.tif')
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds)
        """
        Test Odd Split
        """
        x = 7
        y = 31
        new_dims = clipper.calculate_new_dimensions(x, y)
        self.assertEqual(new_dims[4], 32, 'New x length is 32 when less than 32')
        self.assertEqual(new_dims[5], 32, 'New y length is 32 when less than 32')
        self.assertEqual(new_dims[0], 0, 'New top padding validation')
        self.assertEqual(new_dims[1], 1, 'New bottom padding validation')
        self.assertEqual(new_dims[2], 12, 'New left padding validation')
        self.assertEqual(new_dims[3], 13, 'New right padding validation')
        """
        Test Even Split
        """
        x = 32
        y = 32
        new_dims = clipper.calculate_new_dimensions(x, y)
        self.assertEqual(new_dims[4], 64)
        self.assertEqual(new_dims[5], 64)
        self.assertEqual(new_dims[0], 16, 'New top padding validation')
        self.assertEqual(new_dims[1], 16, 'New bottom padding validation')
        self.assertEqual(new_dims[2], 16, 'New left padding validation')
        self.assertEqual(new_dims[3], 16, 'New right padding validation')

    def test_create_new_geometry(self):
        mask = read_file('test_inputs/test_truth.tif')
        ref_ds = gdal.Open('CONUS1_Inputs/Domain_Blank_Mask.tif')
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds)
        old_geom = (1000.0, 0.0, -22.0, 0.0, -1000.0, 15.0)
        new_geom = clipper.calculate_new_geom(0, 0, old_geom)
        self.assertEqual((1000.0, 0.0, -22.0, 15.0, -1000.0, 15.0), new_geom,
                         'Zero offset does not change transform')

        old_geom = (-1884563.75453, 1000.0, 0.0, 1282344.99762, 0.0, -1000.0)
        new_geom = clipper.calculate_new_geom(1039, 1142, old_geom)
        self.assertEqual((-844563.75453, 1000.0, 0.0, 139344.99762000004, 0.0, -1000.0), new_geom,
                         'Extracted values from CONUS1 tests match')

    """
    Regression tests to verify subsetting can correctly clip a data file,
    correctly produces the subset clip,
    and correctly writes the bounding box file
    """

    def test_subset_dem_to_tif_conus1(self):
        data_array = read_file('CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip.tif')
        mask = read_file('test_inputs/WBDHU8_conus1_mask.tif')
        ref_ds = gdal.Open('CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip.tif')
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=0)
        return_arr, new_geom, new_mask, bbox = clipper.subset(data_array)
        write_array_to_geotiff("conus_1_clip_dem_test.tif",
                               return_arr, new_geom, ref_ds.GetProjection())

        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus1_dem.tif').ReadAsArray(),
                                gdal.Open('conus_1_clip_dem_test.tif').ReadAsArray()), 'Clipping DEM matches reference')
        os.remove('conus_1_clip_dem_test.tif')

        write_array_to_geotiff("conus1_mask_crop.tif",
                               new_mask, new_geom, ref_ds.GetProjection())

        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus1_mask_crop.tif').ReadAsArray(),
                                gdal.Open('conus1_mask_crop.tif').ReadAsArray()),
                          'Subset results in reference inset mask')
        os.remove('conus1_mask_crop.tif')

        write_bbox(bbox, 'bbox_conus1.txt')

        self.assertListEqual(read_bbox('bbox_conus1.txt'), [1141, 1173, 1034, 1130],
                             'Subset writes correct bounding box file')
        os.remove('bbox_conus1.txt')

    def test_subset_tif_conus2(self):
        data_array = read_file('CONUS2_Inputs/CONUS2.0_RawDEM.tif')
        mask = read_file('test_inputs/WBDHU8_conus2_mask.tif')
        ref_ds = gdal.Open('CONUS2_Inputs/CONUS2.0_RawDEM.tif')
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=0)
        return_arr, new_geom, new_mask, bbox = clipper.subset(data_array)
        write_array_to_geotiff("conus_2_clip_dem_test.tif",
                               return_arr, new_geom, ref_ds.GetProjection())
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus2_dem.tif').ReadAsArray(),
                                                        gdal.Open('conus_2_clip_dem_test.tif').ReadAsArray()),
                          'Clipping DEM matches reference')
        os.remove('conus_2_clip_dem_test.tif')

        write_array_to_geotiff("conus2_mask_crop.tif",
                               new_mask, new_geom, ref_ds.GetProjection())
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open('test_inputs/WBDHU8_conus2_mask_crop.tif').ReadAsArray(),
                                gdal.Open('conus2_mask_crop.tif').ReadAsArray()),
                          'Subset results in reference inset mask')
        os.remove('conus2_mask_crop.tif')
        write_bbox(bbox, 'bbox_conus2_full.txt')
        self.assertListEqual(read_bbox('bbox_conus2_full.txt'), [1561, 1593, 1461, 1557],
                             'Subset writes correct bounding box file')
        os.remove('bbox_conus2_full.txt')

    """
    Regression tests to verify clipper creates solid file correctly from mask
    """

    def test_create_solid_file_conus1(self):
        mask = read_file('test_inputs/WBDHU8_conus1_mask.tif')
        ref_ds = gdal.Open('CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip.tif')
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=0)
        batches = clipper.make_solid_file('conus1_solid')
        self.assertEqual(batches, '0 3 6 ')
        with open('conus1_solid.pfsol', 'r') as test_file:
            with open('test_inputs/WBDHU8_conus1.pfsol', 'r') as ref_file:
                self.assertEqual(test_file.read(), ref_file.read(),
                                 'Writing PFSOL file matches reference for conus1')
        """
        make sure the vtk files match as well. skip the first two lines as they contain a version and filename that
        may vary
        """
        with open('conus1_solid.vtk', 'r') as test_file:
            with open('test_inputs/WBDHU8_conus1_ref.vtk', 'r') as ref_file:
                self.assertEqual(test_file.read().split('\n')[2:], ref_file.read().split('\n')[2:],
                                 'Writing vtk file matches reference for conus1')

    def test_create_solid_file_conus2(self):
        mask = read_file('test_inputs/WBDHU8_conus2_mask.tif')
        ref_ds = gdal.Open('CONUS2_Inputs/CONUS2.0_RawDEM.tif')
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=0)
        batches = clipper.make_solid_file('conus2_solid')
        self.assertEqual(batches, '0 3 6 ')
        with open('conus2_solid.pfsol','r') as test_file:
            with open('test_inputs/WBDHU8_conus2.pfsol','r') as ref_file:
                self.assertEqual(test_file.read(), ref_file.read(),
                         'Writing PFSOL file matches reference for conus2')
        """
        make sure the vtk files match as well. skip the first two lines as they contain a version and filename that
        may vary
        """
        with open('conus2_solid.vtk','r') as test_file:
            with open('test_inputs/WBDHU8_conus2_ref.vtk','r') as ref_file:
                self.assertEqual(test_file.read().split('\n')[2:], ref_file.read().split('\n')[2:],
                         'Writing vtk file matches reference for conus2')


if __name__ == '__main__':
    unittest.main()
