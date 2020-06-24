import unittest
import os
import numpy as np
import gdal
import src.file_io_tools as file_io_tools
import tests.test_files as test_files


class FileIOToolBasicTestCase(unittest.TestCase):

    def test_read_sa(self):
        results = file_io_tools.read_file(test_files.forcings_sa)
        self.assertEqual((24, 41, 41), results.shape)
        self.assertEqual(290.4338, results[0, 40, 0])
        self.assertEqual(292.9594, results[-1, 0, 40])

    def test_read_pfb(self):
        results = file_io_tools.read_file(test_files.forcings_pfb)
        self.assertEqual((24, 41, 41), results.shape)
        self.assertEqual(290.4337549299417, results[0, 40, 0])
        self.assertEqual(292.95937295652664, results[-1, 0, 40])

    def test_read_tif(self):
        results = file_io_tools.read_file("test_inputs/test_truth.tif")
        self.assertEqual(3, len(results.shape), 'read a 2d tiff always returns a 3d array')
        results3d = file_io_tools.read_file("test_inputs/subsurface_data.tif")
        self.assertEqual(3, len(results3d.shape), 'read a 3d tiff always returns a 3d array')

    def test_write_read_bbox(self):
        bbox = [10, 15, 20, 25]
        file_io_tools.write_bbox(bbox, 'bbox_test.txt')
        self.assertListEqual(bbox, file_io_tools.read_bbox('bbox_test.txt'),
                             'writing and reading a bbox does not change values')
        os.remove('bbox_test.txt')

    def test_write_tiff(self):
        ds_ref = gdal.Open('test_inputs/test_truth.tif')
        file_io_tools.write_array_to_geotiff('test_write_tif_out.tif',
                                             file_io_tools.read_file('test_inputs/test_truth.tif'),
                                             ds_ref.GetGeoTransform(), ds_ref.GetProjection())
        data_array = file_io_tools.read_file('test_write_tif_out.tif')
        self.assertIsNone(np.testing.assert_array_equal(data_array,
                                                        file_io_tools.read_file('test_inputs/test_truth.tif')),
                          'writing and reading a tif gives back the same array values')
        os.remove('test_write_tif_out.tif')

    def test_write_pfb(self):
        forcings_data = file_io_tools.read_file(test_files.forcings_pfb)
        file_io_tools.write_pfb(forcings_data, 'test_pfb_out.pfb')
        read_data = file_io_tools.read_file('test_pfb_out.pfb')
        self.assertIsNone(np.testing.assert_array_equal(forcings_data, read_data),
                          'writing and reading a pfb gives back the same array values')
        os.remove('test_pfb_out.pfb')

    def test_read_sa(self):
        sa_array = file_io_tools.read_file(test_files.forcings_sa)
        pfb_array = file_io_tools.read_file(test_files.forcings_pfb)
        self.assertIsNone(np.testing.assert_array_almost_equal(sa_array, pfb_array, decimal=3),
                          'reading a .sa file and a .pfb file result in same array values')


if __name__ == '__main__':
    unittest.main()
