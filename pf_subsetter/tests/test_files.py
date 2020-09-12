from pathlib import Path

local_dir = Path(__file__).parent

conus1_dem = local_dir / 'test_inputs/CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip.tif'
conus1_dem_pfb = local_dir / 'test_inputs/CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip.pfb'
conus2_dem = local_dir / 'test_inputs/CONUS2_Inputs/CONUS2.0_RawDEM.tif'
conus1_mask = local_dir / 'test_inputs/CONUS1_Inputs/Domain_Blank_Mask.tif'
conus2_mask = local_dir / 'test_inputs/CONUS2_Inputs/conus_1km_PFmask2.tif'
forcings_pfb = local_dir / 'test_inputs/NLDAS.Temp.000001_to_000024.pfb'
forcings_sa = local_dir / 'test_inputs/NLDAS.Temp.000001_to_000024.sa'
forcings_tif = local_dir / 'test_inputs/NLDAS.Temp.000001_to_000024.tif'
conus1_latlon = local_dir / 'test_inputs/CONUS1_Inputs/conus1_Grid_Centers_Short_Deg.format.sa'
conus1_landcover = local_dir / 'test_inputs/CONUS1_Inputs/conus1_landcover.sa'
conus2_landcover = local_dir / 'test_inputs/CONUS2_Inputs/1km_CONUS2_landcover_IGBP.tif'
conus2_subsurface = local_dir / 'test_inputs/CONUS2_Inputs/3d-grid.v3.tif'
test_bbox_input = local_dir / 'test_inputs/bbox_test_file.txt'


regression_truth_tif = local_dir / 'test_inputs/test_truth.tif'

huc10190004 = {'conus1_mask': local_dir / 'test_inputs/WBDHU8_conus1_mask.tif',
               'conus1_sol': local_dir / 'test_inputs/WBDHU8_conus1.pfsol',
               'conus1_vtk': local_dir / 'test_inputs/WBDHU8_conus1_ref.vtk',
               'conus2_mask': local_dir / 'test_inputs/WBDHU8_conus2_mask.tif',
               'conus2_sol': local_dir / 'test_inputs/WBDHU8_conus2.pfsol',
               'conus2_vtk': local_dir / 'test_inputs/WBDHU8_conus2_ref.vtk',
               'conus1_dem': local_dir / 'test_inputs/WBDHU8_conus1_dem.tif',
               'conus1_dem_box': local_dir / 'test_inputs/WBDHU8_conus1_dem_box.pfb',
               'conus1_inset': local_dir / 'test_inputs/WBDHU8_conus1_mask_crop.tif',
               'conus1_bbox': [1040, 717, 85, 30],
               'conus2_dem': local_dir / 'test_inputs/WBDHU8_conus2_dem.tif',
               'conus2_inset': local_dir / 'test_inputs/WBDHU8_conus2_mask_crop.tif',
               'conus2_bbox': [1469, 1666, 82, 29],
               'shapefile': local_dir / 'test_inputs/WBDHU8.shp',
               'conus1_mask_-9999999': local_dir / 'test_inputs/WBDHU8_conus1_mask_-9999999.tif',
               'conus1_vegm': local_dir / 'test_inputs/WBDHU8_conus1_vegm.dat',
               'conus1_latlon': local_dir / 'test_inputs/WBDHU8_conus1_latlon.sa'}

test_domain_manifest = local_dir / 'test_inputs/test_domain_manifest.yaml'

test_domain_inputs = local_dir / 'test_inputs/testdom_inputs'

