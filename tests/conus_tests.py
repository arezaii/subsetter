import unittest
import data
from src.conus import Conus
import os


class ConusClassTests(unittest.TestCase):

    # Can't perform positive test case without all the required_files present
    def test_normal_startup(self):
        if os.environ.get('TRAVIS'):
            pass
        else:
            conus1 = Conus(local_path='../subset_1/CONUS1_inputs')
            self.assertEqual(conus1.manifest_path, data.conus_manifest)


if __name__ == '__main__':
    unittest.main()
