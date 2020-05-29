import os
import unittest
import numpy as np
import src.file_io_tools as file_io_tools
import tests.test_files as test_files
from src.clm_utils import ClmClipper


class ClmUtilsClipperRegressionTests(unittest.TestCase):

    def test_clm_clip_land_cover(self):
        mask_array = file_io_tools.read_file(test_files.huc10190004.get('conus1_mask'))
        ds_ref = file_io_tools.read_geotiff(test_files.conus1_mask)
        clm_clipper = ClmClipper(mask_array, ds_ref)
        latlon_data, _ = clm_clipper.clip_latlon(test_files.conus1_latlon)
        land_cover_data, vegm_data = clm_clipper.clip_land_cover(lat_lon_array=latlon_data,
                                                                 land_cover_file=test_files.conus1_landcover)
        clm_clipper.write_land_cover(vegm_data, 'WBDHU8_vegm_test.dat')
        with open('WBDHU8_vegm_test.dat', 'r') as test_file:
            with open('test_inputs/WBDHU8_vegm_test.dat', 'r') as ref_file:
                self.assertEqual(test_file.read().split('\n'), ref_file.read().split('\n'),
                                 'Writing vegm file matches reference for conus1')

        os.remove('WBDHU8_vegm_test.dat')

    def test_clm_clip_latlon(self):
        mask_array = file_io_tools.read_file(test_files.huc10190004.get('conus1_mask'))
        ds_ref = file_io_tools.read_geotiff(test_files.conus1_mask)
        clm_clipper = ClmClipper(mask_array, ds_ref)
        latlon_formatted, latlon_data = clm_clipper.clip_latlon(test_files.conus1_latlon)
        clm_clipper.write_lat_lon(latlon_formatted, 'WBDHU8_latlon_test.sa', x=latlon_data.shape[2],
                                  y=latlon_data.shape[1], z=latlon_data.shape[0])
        self.assertIsNone(np.testing.assert_array_equal(file_io_tools.read_file('WBDHU8_latlon_test.sa'),
                                                        file_io_tools.read_file('test_inputs/WBDHU8_latlon_orig.sa')),
                          'writing and reading a tif gives back the same array values')
        os.remove('WBDHU8_latlon_test.sa')


if __name__ == '__main__':
    unittest.main()
