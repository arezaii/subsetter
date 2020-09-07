import unittest
from pf_subsetter.mask import SubsetMask
from test_files import huc10190004


class SubsetMaskClassTests(unittest.TestCase):

    def test_normal_startup(self):
        my_mask = SubsetMask(huc10190004.get('conus1_mask').as_posix())
        self.assertEqual(-999, my_mask.no_data_value)
        self.assertEqual(0, my_mask.bbox_val)

    def test_resize_bbox(self):
        my_mask = SubsetMask(huc10190004.get('conus1_mask').as_posix())
        self.assertSequenceEqual((1142, 1171, 1039, 1123), my_mask.inner_mask_edges)
        self.assertSequenceEqual((1142, 1171, 1039, 1123), my_mask.bbox_edges)
        self.assertSequenceEqual((30, 85), my_mask.bbox_shape)
        self.assertSequenceEqual((30, 85), my_mask.inner_mask_shape)
        my_mask.add_bbox_to_mask(x_pad=9, y_pad=9)
        self.assertSequenceEqual((1133, 1180, 1030, 1132), my_mask.bbox_edges)
        self.assertSequenceEqual((1142, 1171, 1039, 1123), my_mask.inner_mask_edges)
        self.assertSequenceEqual((30, 85), my_mask.inner_mask_shape)
        self.assertSequenceEqual((48, 103), my_mask.bbox_shape)
        self.assertEqual(-999, my_mask.no_data_value)
        self.assertEqual(0, my_mask.bbox_val)


if __name__ == '__main__':
    unittest.main()
