import unittest
import data
import os
from src.conus import Conus


class ConusClassTests(unittest.TestCase):
    testDir = 'TestDirectory'
    # Can't perform this positive test case without all the required_files present
    # def test_folder_exists(self):
    #     os.mkdir(self.testDir)
    #     try:
    #         Conus(1, self.testDir)
    #     except:
    #         self.fail("Conus(1, self.testDir) raised an exception unexpectedly!")
    #     shutil.rmtree(self.testDir)

    def test_folder_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            Conus(1, self.testDir)

    def test_manifest_provided(self):
        with self.assertRaises(FileNotFoundError):
            Conus(os.path.join('test_inputs','CONUS1_Inputs'), data.conus_manifest, 1)


if __name__ == '__main__':
    unittest.main()
