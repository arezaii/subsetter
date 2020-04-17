import unittest
from src.conus_sources import CyVerseDownloader
import os


class CyVerseDownloaderTests(unittest.TestCase):
    readme_filesize = 2680

    def test_connect(self):
        user = os.environ.get('CYVERSE_USERNAME')
        password = os.environ.get('CYVERSE_PASSWORD')
        cs = CyVerseDownloader(user, password)
        cs.get_conus_data('/iplant/home/shared/avra/CONUS_1.0/SteadyState_Final/Other_Domain_Files/ReadMe_Files.txt')
        self.assertEqual(self.readme_filesize, os.path.getsize('ReadMe_Files.txt'))
        os.remove('ReadMe_Files.txt')


if __name__ == '__main__':
    unittest.main()
