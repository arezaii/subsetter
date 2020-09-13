import unittest
from parflow.subset.tools import bulk_clipper
from parflow.subset.tests import test_files
from parflow.subset.utils.io import read_file
import numpy as np
import os


class BulkClipperArgParseTests(unittest.TestCase):

    def setUp(self) -> None:
        self.good_mask_file = test_files.huc10190004.get('conus1_mask').as_posix()
        self.bad_mask_file = './mask_file_no_exists.tif'
        self.good_input_file_list = [test_files.conus1_dem.as_posix(), test_files.conus1_mask.as_posix()]
        self.bad_input_file_list = './input_file_to_clip_no_exists.pfb'
        self.good_bbox_file = test_files.test_bbox_input.as_posix()

    def test_cli_no_args(self):
        with self.assertRaises(SystemExit):
            bulk_clipper.parse_args([])

    def test_cli_mask_without_data_args(self):
        with self.assertRaises(SystemExit):
            bulk_clipper.parse_args(['-m', self.good_mask_file])

    def test_cli_mask_and_dims_specified(self):
        with self.assertRaises(SystemExit):
            bulk_clipper.parse_args(
                ['-m', self.good_mask_file, '-i', '1', '1', '10', '10', '-d', self.good_input_file_list[0]])

    def test_cli_mask_and_box_specified(self):
        with self.assertRaises(SystemExit):
            bulk_clipper.parse_args(
                ['-m', self.good_mask_file, '-b', self.good_bbox_file, '-d', self.good_input_file_list[0]])

    def test_cli_mask_and_bbox_and_dims_specified(self):
        with self.assertRaises(SystemExit):
            bulk_clipper.parse_args(
                ['-m', self.good_mask_file, '-b', self.good_bbox_file, '-i', '1', '1', '10', '10', '-d',
                 self.good_input_file_list[0]])

    def test_cli_mask_and_bad_input_file(self):
        with self.assertRaises(SystemExit):
            bulk_clipper.parse_args(['-m', self.good_mask_file, '-d', self.bad_input_file_list])

    def test_cli_bad_mask_file(self):
        with self.assertRaises(SystemExit):
            bulk_clipper.parse_args(['-m', self.bad_mask_file, '-d', self.good_input_file_list])

    def test_cli_no_mask_bbox_dims(self):
        with self.assertRaises(SystemExit):
            bulk_clipper.parse_args(['-d', self.good_input_file_list[0]])

    def test_cli_good_mask_and_input_defaults(self):
        args = bulk_clipper.parse_args(['-m', self.good_mask_file, '-d', self.good_input_file_list[0]])
        self.assertTrue(args.mask_file)
        self.assertFalse(args.bbox_file)
        self.assertFalse(args.bbox_def)
        self.assertTrue(args.data_files)
        self.assertEqual(args.out_dir, '.')
        self.assertFalse(args.ref_file)
        self.assertFalse(args.write_tifs)
        self.assertTrue(args.write_pfbs)

    def test_cli_good_dims_and_input_defaults(self):
        args = bulk_clipper.parse_args(['-i', '10', '20', '30', '40', '-d', self.good_input_file_list[0]])
        self.assertFalse(args.mask_file)
        self.assertFalse(args.bbox_file)
        self.assertTrue(args.bbox_def)
        self.assertTrue(args.data_files)
        self.assertEqual(args.out_dir, '.')
        self.assertFalse(args.ref_file)
        self.assertFalse(args.write_tifs)
        self.assertTrue(args.write_pfbs)
        self.assertSequenceEqual(args.bbox_def, (10, 20, 30, 40))

    def test_cli_good_bbox_file_and_input_defaults(self):
        args = bulk_clipper.parse_args(['-b', self.good_bbox_file, '-d', self.good_input_file_list[0]])
        self.assertFalse(args.mask_file)
        self.assertTrue(args.bbox_file)
        self.assertFalse(args.bbox_def)
        self.assertTrue(args.data_files)
        self.assertEqual(args.out_dir, '.')
        self.assertFalse(args.ref_file)
        self.assertFalse(args.write_tifs)
        self.assertTrue(args.write_pfbs)


class BulkClipperRegressionTests(unittest.TestCase):

    def setUp(self) -> None:
        self.good_mask_file = test_files.huc10190004.get('conus1_mask').as_posix()
        self.bad_mask_file = './mask_file_no_exists.tif'
        self.good_input_file_list = [test_files.conus1_dem.as_posix(), test_files.conus1_mask.as_posix()]
        self.bad_input_file_list = './input_file_to_clip_no_exists.pfb'
        self.good_bbox_file = test_files.test_bbox_input.as_posix()

    def test_box_clip_default(self):
        bulk_clipper.box_clip((1040, 717, 85, 30), self.good_input_file_list[:1])
        ref_data = read_file(test_files.huc10190004.get('conus1_dem_box').as_posix())
        written_data = read_file('./CONUS2.0_RawDEM_CONUS1clip_clip.pfb')
        self.assertIsNone(np.testing.assert_array_equal(ref_data, written_data))
        os.remove('./CONUS2.0_RawDEM_CONUS1clip_clip.pfb')

    def test_mask_clip_default(self):
        mask = test_files.huc10190004.get('conus1_mask').as_posix()
        bulk_clipper.mask_clip(mask, self.good_input_file_list[:1])
        ref_data = read_file(test_files.huc10190004.get('conus1_dem').as_posix())
        written_data = read_file('./CONUS2.0_RawDEM_CONUS1clip_clip.pfb')
        self.assertIsNone(np.testing.assert_array_equal(ref_data, written_data))
        os.remove('./CONUS2.0_RawDEM_CONUS1clip_clip.pfb')


if __name__ == '__main__':
    unittest.main()
