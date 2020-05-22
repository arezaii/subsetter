import unittest
import gdal
from src.clipper import Clipper
from src.file_io_tools import read_file
from src.file_io_tools import write_array_to_geotiff
from src.file_io_tools import write_bbox
import numpy as np
from src.file_io_tools import read_bbox
import tests.test_files as test_files
import os


class RegressionClipTests(unittest.TestCase):
    """
    Regression tests to verify subsetting can correctly clip a data file,
    correctly produces the subset clip,
    and correctly writes the bounding box file
    """

    def test_subset_dem_to_tif_conus1(self):
        data_array = read_file(test_files.conus1_dem)
        mask = read_file(test_files.huc10190004.get('conus1_mask'))
        ref_ds = gdal.Open(test_files.conus1_dem)
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=-1)
        return_arr, new_geom, new_mask, bbox = clipper.subset(data_array)
        write_array_to_geotiff("conus_1_clip_dem_test.tif",
                               return_arr, new_geom, ref_ds.GetProjection())

        self.assertIsNone(np.testing.assert_array_equal(gdal.Open(test_files.huc10190004.get('conus1_dem')).ReadAsArray(),
                                gdal.Open('conus_1_clip_dem_test.tif').ReadAsArray()), 'Clipping DEM matches reference')
        os.remove('conus_1_clip_dem_test.tif')

        write_array_to_geotiff("conus1_mask_crop.tif",
                               new_mask, new_geom, ref_ds.GetProjection())

        self.assertIsNone(np.testing.assert_array_equal(gdal.Open(test_files.huc10190004.get('conus1_inset')).ReadAsArray(),
                                gdal.Open('conus1_mask_crop.tif').ReadAsArray()),
                          'Subset results in reference inset mask')
        os.remove('conus1_mask_crop.tif')

        write_bbox(bbox, 'bbox_conus1.txt')

        self.assertListEqual(read_bbox('bbox_conus1.txt'), test_files.huc10190004.get('conus1_bbox'),
                             'Subset writes correct bounding box file')
        os.remove('bbox_conus1.txt')

    def test_subset_tif_conus2(self):
        data_array = read_file(test_files.conus2_dem)
        mask = read_file(test_files.huc10190004.get('conus2_mask'))
        ref_ds = gdal.Open(test_files.conus2_dem)
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=-1)
        return_arr, new_geom, new_mask, bbox = clipper.subset(data_array)
        write_array_to_geotiff("conus_2_clip_dem_test.tif",
                               return_arr, new_geom, ref_ds.GetProjection())
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open(test_files.huc10190004.get('conus2_dem')).ReadAsArray(),
                                                        gdal.Open('conus_2_clip_dem_test.tif').ReadAsArray()),
                          'Clipping DEM matches reference')
        os.remove('conus_2_clip_dem_test.tif')

        write_array_to_geotiff("conus2_mask_crop.tif",
                               new_mask, new_geom, ref_ds.GetProjection())
        self.assertIsNone(np.testing.assert_array_equal(gdal.Open(test_files.huc10190004.get('conus2_inset')).ReadAsArray(),
                                gdal.Open('conus2_mask_crop.tif').ReadAsArray()),
                          'Subset results in reference inset mask')
        os.remove('conus2_mask_crop.tif')
        write_bbox(bbox, 'bbox_conus2_full.txt')
        self.assertListEqual(read_bbox('bbox_conus2_full.txt'), test_files.huc10190004.get('conus2_bbox'),
                             'Subset writes correct bounding box file')
        os.remove('bbox_conus2_full.txt')


class RegressionSolidFileTests(unittest.TestCase):
    """
    Regression tests to verify clipper creates solid file correctly from mask
    """

    asc_filenames = ['Back_Border.asc', 'Bottom_Border.asc', 'Front_Border.asc',
                     'Left_Border.asc', 'Right_Border.asc', 'Top_Border.asc']

    def tearDown(self):
        for f in self.asc_filenames:
            try:
                os.remove(f)
            except OSError:
                pass

    def test_create_solid_file_conus1(self):
        mask = read_file(test_files.huc10190004.get('conus1_mask'))
        ref_ds = gdal.Open(test_files.conus1_dem)
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=-1)
        batches = clipper.make_solid_file('conus1_solid')
        self.assertEqual(batches, '0 3 6 ')
        with open('conus1_solid.pfsol', 'r') as test_file:
            with open(test_files.huc10190004.get('conus1_sol'), 'r') as ref_file:
                self.assertEqual(test_file.read(), ref_file.read(),
                                 'Writing PFSOL file matches reference for conus1')
        """
        make sure the vtk files match as well. skip the first two lines as they contain a version and filename that
        may vary
        """
        with open('conus1_solid.vtk', 'r') as test_file:
            with open(test_files.huc10190004.get('conus1_vtk'), 'r') as ref_file:
                self.assertEqual(test_file.read().split('\n')[2:], ref_file.read().split('\n')[2:],
                                 'Writing vtk file matches reference for conus1')
        os.remove('conus1_solid.vtk')
        os.remove('conus1_solid.pfsol')

    def test_create_solid_file_conus2(self):
        mask = read_file(test_files.huc10190004.get('conus2_mask'))
        ref_ds = gdal.Open(test_files.conus2_dem)
        clipper = Clipper(mask_array=mask, reference_dataset=ref_ds, no_data_threshold=-1)
        batches = clipper.make_solid_file('conus2_solid')
        self.assertEqual(batches, '0 3 6 ')
        with open('conus2_solid.pfsol','r') as test_file:
            with open(test_files.huc10190004.get('conus2_sol'), 'r') as ref_file:
                self.assertEqual(test_file.read(), ref_file.read(),
                         'Writing PFSOL file matches reference for conus2')
        """
        make sure the vtk files match as well. skip the first two lines as they contain a version and filename that
        may vary
        """
        with open('conus2_solid.vtk','r') as test_file:
            with open(test_files.huc10190004.get('conus2_vtk'), 'r') as ref_file:
                self.assertEqual(test_file.read().split('\n')[2:], ref_file.read().split('\n')[2:],
                                 'Writing vtk file matches reference for conus2')
        for f in self.asc_filenames:
            os.remove(f)
        os.remove('conus2_solid.vtk')
        os.remove('conus2_solid.pfsol')


if __name__ == '__main__':
    unittest.main()
