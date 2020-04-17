import unittest
from subset_tools import CyVerseDownloader, Conus
import os
import shutil


class CyVerseDownloaderTests(unittest.TestCase):
    readme_filesize = 2680

    def test_connect(self):
        user = os.environ.get('CYVERSE_USERNAME')
        password = os.environ.get('CYVERSE_PASSWORD')
        cs = CyVerseDownloader(user, password)
        cs.get_conus_data('/iplant/home/shared/avra/CONUS_1.0/SteadyState_Final/Other_Domain_Files/ReadMe_Files.txt')
        self.assertEqual(self.readme_filesize, os.path.getsize('ReadMe_Files.txt'))


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
