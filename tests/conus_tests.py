import unittest
from src.conus import Conus
import os
import shutil


class ConusClassTests(unittest.TestCase):
    testDir = 'TestDirectory'

    def test_folder_exists(self):
        os.mkdir(self.testDir)
        try:
            Conus(1, self.testDir)
        except:
            self.fail("Conus(1, self.testDir) raised an exception unexpectedly!")
        shutil.rmtree(self.testDir)

    def test_folder_not_exists(self):
        with self.assertRaises(Exception):
            Conus(1, self.testDir)


if __name__ == '__main__':
    unittest.main()
