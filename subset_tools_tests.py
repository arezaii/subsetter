import unittest
from subset_tools import CyVerseDownloader
import os


class CyVerseDownloaderTests(unittest.TestCase):
    def test_connect(self):
        user = os.environ.get('CYVERSE_USERNAME')
        password = os.environ.get('CYVERSE_PASSWORD')
        cs = CyVerseDownloader(user, password)
        cs.get_conus_data('/iplant/home/shared/avra/CONUS_1.0/SteadyState_Final/Other_Domain_Files/ReadMe_Files.txt')
        self.assertEqual(2680, os.path.getsize('ReadMe_Files.txt'))

# class MyTestCase(unittest.TestCase):
#     def test_something(self):
#         self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
