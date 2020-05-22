import unittest
from src.file_io_tools import read_file
from src.mask_utils import MaskUtils


class MaskUtilsCalculationUnitTests(unittest.TestCase):
    def test_calculate_new_dims(self):
        mask = read_file('test_inputs/test_truth.tif')
        utils = MaskUtils(mask)
        """
        Test Odd Split
        """
        x = 7
        y = 31
        new_dims = utils.calculate_new_dimensions(x, y, 32)
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
        new_dims = utils.calculate_new_dimensions(x, y, 32)
        self.assertEqual(new_dims[4], 64)
        self.assertEqual(new_dims[5], 64)
        self.assertEqual(new_dims[0], 16, 'New top padding validation')
        self.assertEqual(new_dims[1], 16, 'New bottom padding validation')
        self.assertEqual(new_dims[2], 16, 'New left padding validation')
        self.assertEqual(new_dims[3], 16, 'New right padding validation')

        """
        Test Even Size, Multiple of 2
        """
        x = 4
        y = 4
        new_dims = utils.calculate_new_dimensions(x, y, 2)
        self.assertEqual(new_dims[4], 6)
        self.assertEqual(new_dims[5], 6)
        self.assertEqual(new_dims[0], 1, 'New top padding validation')
        self.assertEqual(new_dims[1], 1, 'New bottom padding validation')
        self.assertEqual(new_dims[2], 1, 'New left padding validation')
        self.assertEqual(new_dims[3], 1, 'New right padding validation')

        """
        Test Odd Size, Multiple of 2
        """
        x = 3
        y = 3
        new_dims = utils.calculate_new_dimensions(x, y, 2)
        self.assertEqual(new_dims[4], 4)
        self.assertEqual(new_dims[5], 4)
        self.assertEqual(new_dims[0], 0, 'New top padding validation')
        self.assertEqual(new_dims[1], 1, 'New bottom padding validation')
        self.assertEqual(new_dims[2], 0, 'New left padding validation')
        self.assertEqual(new_dims[3], 1, 'New right padding validation')

        """
        Test Even Size, Multiple of 1
        """
        x = 4
        y = 4
        new_dims = utils.calculate_new_dimensions(x, y, 1)
        self.assertEqual(new_dims[4], 5)
        self.assertEqual(new_dims[5], 5)
        self.assertEqual(new_dims[0], 0, 'New top padding validation')
        self.assertEqual(new_dims[1], 1, 'New bottom padding validation')
        self.assertEqual(new_dims[2], 0, 'New left padding validation')
        self.assertEqual(new_dims[3], 1, 'New right padding validation')

        """
        Test Odd Size, Multiple of 1
        """
        x = 3
        y = 3
        new_dims = utils.calculate_new_dimensions(x, y, 1)
        self.assertEqual(new_dims[4], 4)
        self.assertEqual(new_dims[5], 4)
        self.assertEqual(new_dims[0], 0, 'New top padding validation')
        self.assertEqual(new_dims[1], 1, 'New bottom padding validation')
        self.assertEqual(new_dims[2], 0, 'New left padding validation')
        self.assertEqual(new_dims[3], 1, 'New right padding validation')

    def test_create_new_geometry(self):
        mask = read_file('test_inputs/test_truth.tif')
        utils = MaskUtils(mask)
        old_geom = (1000.0, 0.0, -22.0, 0.0, -1000.0, 15.0)
        new_geom = utils.calculate_new_geom(0, 0, old_geom)
        self.assertEqual((1000.0, 0.0, -22.0, 0.0, -1000.0, 15.0), new_geom,
                         'Zero offset does not change transform')

        old_geom = (-1884563.75453, 1000.0, 0.0, 1282344.99762, 0.0, -1000.0)
        new_geom = utils.calculate_new_geom(1039, 1142, old_geom)
        self.assertEqual((-845563.75453, 1000.0, 0.0, 140344.99762000004, 0.0, -1000.0), new_geom,
                         'Extracted values from CONUS1 tests match')


if __name__ == '__main__':
    unittest.main()
