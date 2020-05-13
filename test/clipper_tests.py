import unittest
import gdal
from src.clipper import Clipper
from src.file_io_tools import read_file
from src.file_io_tools import write_array_to_geotiff
from src.file_io_tools import write_bbox


class MyTestCase(unittest.TestCase):
    def test_calculate_new_dims(self):
        clipper = Clipper()
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
        clipper = Clipper()
        old_geom = (1000.0, 0.0, -22.0, 0.0, -1000.0, 15.0)
        new_geom = clipper.calculate_new_geom(0, 0, old_geom)
        self.assertEqual((1000.0, 0.0, -22.0, 15.0, -1000.0, 15.0), new_geom,
                         'Zero offset does not change transform')

        old_geom = (-1884563.75453, 1000.0, 0.0, 1282344.99762, 0.0, -1000.0)
        new_geom = clipper.calculate_new_geom(1039, 1142, old_geom)
        self.assertEqual((-844563.75453, 1000.0, 0.0, 139344.99762000004, 0.0, -1000.0), new_geom,
                         'Extracted values from CONUS1 tests match')

    def test_subset_tif_with_crop(self):
        clipper = Clipper()
        arr = read_file('CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip.tif')
        mask = read_file('test_inputs/test_truth.tif')
        ref_ds = gdal.Open('CONUS1_Inputs/Domain_Blank_Mask.tif')
        return_arr, new_geom, new_mask, bbox = clipper.subset(arr, mask, ref_ds, 1)
        write_array_to_geotiff("CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip_subset.tif",
                               return_arr, new_geom, ref_ds.GetProjection())
        write_array_to_geotiff("CONUS1_Inputs/conus1_mask_crop.tif",
                               new_mask, new_geom, ref_ds.GetProjection())
        write_bbox(bbox, 'CONUS1_Inputs/bbox_conus1.txt')

    def test_subset_tif_no_crop(self):
        clipper = Clipper()
        arr = read_file('CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip.tif')
        mask = read_file('test_inputs/test_truth.tif')
        ref_ds = gdal.Open('CONUS1_Inputs/Domain_Blank_Mask.tif')
        return_arr, new_geom, new_mask, bbox = clipper.subset(arr, mask, ref_ds)
        write_array_to_geotiff("CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip_subset_full.tif",
                               return_arr, new_geom, ref_ds.GetProjection())
        write_array_to_geotiff("CONUS1_Inputs/conus1_mask_full.tif",
                               new_mask, new_geom, ref_ds.GetProjection())
        write_bbox(bbox, 'CONUS1_Inputs/bbox_conus1_full.txt')


if __name__ == '__main__':
    unittest.main()
