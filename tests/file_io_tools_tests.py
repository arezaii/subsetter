import unittest
import os
import numpy as np
import gdal
import src.file_io_tools as file_reader
import tests.test_files as test_files


class FileIOToolBasicTestCase(unittest.TestCase):

    def test_read_sa(self):
        results = file_reader.read_file(test_files.forcings_sa)
        self.assertEqual((24, 41, 41), results.shape)
        self.assertEqual(290.4338, results[0, 40, 0])
        self.assertEqual(292.9594, results[-1, 0, 40])

    def test_read_pfb(self):
        results = file_reader.read_file(test_files.forcings_pfb)
        self.assertEqual((24, 41, 41), results.shape)
        self.assertEqual(290.4337549299417, results[0, 40, 0])
        self.assertEqual(292.95937295652664, results[-1, 0, 40])

    def test_read_tif(self):
        results = file_reader.read_file("test_inputs/test_truth.tif")
        self.assertEqual(3, len(results.shape), 'read a 2d tiff always returns a 3d array')
        results3d = file_reader.read_file("test_inputs/subsurface_data.tif")
        self.assertEqual(3, len(results3d.shape), 'read a 3d tiff always returns a 3d array')

    def test_write_read_bbox(self):
        bbox = [10, 15, 20, 25]
        file_reader.write_bbox(bbox, 'bbox_test.txt')
        self.assertListEqual(bbox, file_reader.read_bbox('bbox_test.txt'),
                             'writing and reading a bbox does not change values')
        os.remove('bbox_test.txt')

    def test_write_tiff(self):
        ds_ref = gdal.Open('test_inputs/test_truth.tif')
        file_reader.write_array_to_geotiff('test_write_tif_out.tif',
                                           file_reader.read_file('test_inputs/test_truth.tif'),
                                           ds_ref.GetGeoTransform(), ds_ref.GetProjection())
        data_array = file_reader.read_file('test_write_tif_out.tif')
        self.assertIsNone(np.testing.assert_array_equal(data_array,
                                                        file_reader.read_file('test_inputs/test_truth.tif')),
                          'writing and reading a tif gives back the same array values')
        os.remove('test_write_tif_out.tif')



    def test_write_pfb(self):
        forcings_data = file_reader.read_file(test_files.forcings_pfb)
        file_reader.write_pfb(forcings_data, 'test_pfb_out.pfb')
        self.assertIsNone(np.testing.assert_array_equal(forcings_data,
                                                        file_reader.read_file(test_files.forcings_pfb)),
                          'writing and reading a pfb gives back the same array values')
        os.remove('test_pfb_out.pfb')


if __name__ == '__main__':
    unittest.main()
