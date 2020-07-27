conus1_dem = 'test_inputs/CONUS1_Inputs/CONUS2.0_RawDEM_CONUS1clip.tif'
conus2_dem = 'test_inputs/CONUS2_Inputs/CONUS2.0_RawDEM.tif'
conus1_mask = 'test_inputs/CONUS1_Inputs/Domain_Blank_Mask.tif'
conus2_mask = 'test_inputs/CONUS2_Inputs/conus_1km_PFmask2.tif'
forcings_pfb = 'test_inputs/NLDAS.Temp.000001_to_000024.pfb'
forcings_sa = 'test_inputs/NLDAS.Temp.000001_to_000024.sa'
conus1_latlon = 'test_inputs/CONUS1_Inputs/conus1_Grid_Centers_Short_Deg.format.sa'
conus1_landcover = 'test_inputs/CONUS1_Inputs/conus1_landcover.sa'
conus2_landcover = 'test_inputs/CONUS2_Inputs/1km_CONUS2_landcover_IGBP.tif'

huc10190004 = {'conus1_mask': 'test_inputs/WBDHU8_conus1_mask.tif',
               'conus1_sol': 'test_inputs/WBDHU8_conus1.pfsol',
               'conus1_vtk': 'test_inputs/WBDHU8_conus1_ref.vtk',
               'conus2_mask': 'test_inputs/WBDHU8_conus2_mask.tif',
               'conus2_sol': 'test_inputs/WBDHU8_conus2.pfsol',
               'conus2_vtk': 'test_inputs/WBDHU8_conus2_ref.vtk',
               'conus1_dem': 'test_inputs/WBDHU8_conus1_dem.tif',
               'conus1_inset': 'test_inputs/WBDHU8_conus1_mask_crop.tif',
               'conus1_bbox': [1141, 1173, 1034, 1130],
               'conus2_dem': 'test_inputs/WBDHU8_conus2_dem.tif',
               'conus2_inset': 'test_inputs/WBDHU8_conus2_mask_crop.tif',
               'conus2_bbox': [1561, 1593, 1461, 1557],
               'shapefile': 'test_inputs/WBDHU8.shp',
               'conus1_mask_-9999999': 'test_inputs/WBDHU8_conus1_mask_-9999999.tif'
               }

test_domain_manifest = 'test_inputs/test_domain_manifest.yaml'
