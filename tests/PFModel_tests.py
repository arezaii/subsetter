import unittest
from src.PFModel import PFModel
from tests.test_files import test_domain_manifest
import numpy as np


class PFModelClassTests(unittest.TestCase):

    def test_normal_startup(self):
        model1 = PFModel('test_model', 'test_inputs/testdom_inputs', manifest_path=test_domain_manifest, version=1)
        model2 = PFModel('test_model', 'test_inputs/testdom_inputs', manifest_path=test_domain_manifest, version=2)
        model3 = PFModel('test_model', 'test_inputs/testdom_inputs', manifest_path=test_domain_manifest, version=3)

        # keys which should exist and be assigned
        self.assertEqual(model1.required_files.get('DOMAIN_MASK'), 'Domain_Blank_Mask.tif')
        self.assertEqual(model2.required_files.get('SLOPE_X'), 'testdom_slope_x.sa')
        self.assertEqual(model2.optional_files.get('DEM'), 'testdom_dem.sa')
        self.assertEqual(model3.required_files.get('PME'), 'testdom_pme.sa')
        self.assertEqual(model3.optional_files.get('DEM'), 'testdom_dem.sa')

        # keys which should not exist
        self.assertIsNone(model1.optional_files.get('DEM'))
        self.assertIsNone(model2.optional_files.get('LAT_LON'))

    def test_required_files_definition_missing(self):
        with self.assertRaises(AttributeError):
            PFModel('test_model', 'test_inputs/testdom_inputs', manifest_path=test_domain_manifest, version=4)

    def test_folder_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            PFModel('test_model', 'test_inputs/testdom_noexists_inputs', version=1, manifest_path=test_domain_manifest)

    def test_required_file_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            PFModel('test_model', 'test_inputs/testdom_inputs', version=5, manifest_path=test_domain_manifest)

    def test_file_optional_file_not_exists(self):
        model = PFModel('test_model', 'test_inputs/testdom_inputs', manifest_path=test_domain_manifest, version=6)
        self.assertEqual(model.optional_files.get('DEM'), 'testdom_noexists_dem.sa')

    def test_get_mask_files(self):
        model = PFModel('test_model', 'test_inputs/testdom_inputs', manifest_path=test_domain_manifest, version=1)
        self.assertIsNone(model.mask_tif)
        self.assertIsNone(model.mask_array)
        mask_tif = model.get_domain_tif()
        self.assertIsNotNone(model.mask_array)
        self.assertIsNotNone(model.mask_tif)
        self.assertEqual(mask_tif, model.mask_tif)
        mask_array = model.get_domain_mask()
        self.assertIsNone(np.testing.assert_array_equal(mask_array, model.mask_array))
        print(model)

