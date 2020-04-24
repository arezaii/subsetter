import unittest

import file_reader


class MyTestCase(unittest.TestCase):

    def test_read_sa(self):
        results = file_reader.read_file("../test_inputs/NLDAS.Temp.000001_to_000024.sa")
        self.assertEqual((24, 41, 41), results.shape)
        self.assertEqual(290.4338, results[0, 40, 0])
        self.assertEqual(292.9594, results[-1, 0, 40])

    def test_read_pfb(self):
        results = file_reader.read_file("../test_inputs/NLDAS.Temp.000001_to_000024.pfb")
        self.assertEqual((24, 41, 41), results.shape)
        self.assertEqual(290.4337549299417, results[0, 40, 0])
        self.assertEqual(292.95937295652664, results[-1, 0, 40])

    # def test_read_tif(self):


if __name__ == '__main__':
    unittest.main()
