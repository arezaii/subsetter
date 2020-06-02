import os
import logging
import src.file_io_tools as file_io_tools


class Conus:

    def __init__(self, local_path, version=1):
        """ Information about the CONUS dataset we are working with

        @param local_path: path on system where conus inputs live
        @param version: the conus version to create
        """
        self.version = version
        if self.version == 1:
            self.files = {
                'CONUS_MASK': 'Domain_Blank_Mask.tif',
                'SUBSURFACE_DATA': 'grid3d.v3.pfb',
                'PME': 'PmE.flux.pfb',
                'SLOPE_X': 'slopex.pfb',
                'SLOPE_Y': 'slopey.pfb',
                'DEM': 'CONUS2.0_RawDEM_CONUS1clip.tif'
            }
            self.clm = {'LAND_COVER': 'conus1_landcover.sa',
                        'LAT_LON': 'conus1_Grid_Centers_Short_Deg.format.sa'}

            self.cyverse_path = '/iplant/home/shared/avra/CONUS_1.0/SteadyState_Final/Other_Domain_Files/'
            self.local_path = local_path
        elif self.version == 2:
            self.files = {
                'CONUS_MASK': 'conus_1km_PFmask2.tif',
                'SUBSURFACE_DATA': '3d-grid.v3.tif',
                'PME': 'PME.tif',
                'SLOPE_X': 'Str3Ep0_smth.rvth_1500.mx0.5.mn5.sec0.up_slopex.tif',
                'SLOPE_Y': 'Str3Ep0_smth.rvth_1500.mx0.5.mn5.sec0.up_slopey.tif',
                'SINKS': 'conus_1km_PFmask_manualsinks.tif',
                'RESERVOIRS': 'conus_1km_PFmask_reservoirs.tif',
                'LAKE_BORDER': 'conus_1km_PFmask_selectLakesborder.tif',
                'LAKE_MASK': 'conus_1km_PFmask_selectLakesmask.tif',
                'CHANNELS': '1km_upscaledNWM_ChannelOrder5_mod2.tif',
                'CELL_TYPES': '1km_PF_BorderCellType.tif',
                'DEM': 'CONUS2.0_RawDEM.tif'
            }
            self.clm = {'LAND_COVER': '1km_CONUS2_landcover_IGBP.tif',
                        'LAT_LON': 'latlonCONUS2.sa'}
            # TODO: Remove cyverse path?
            self.cyverse_path = '/iplant/home/shared/avra/CONUS2.0/Inputs/domain/'
            self.local_path = local_path
        self.conus_mask_tif = file_io_tools.read_geotiff(os.path.join(self.local_path, self.files.get("CONUS_MASK")))
        self.conus_mask_array = self.conus_mask_tif.ReadAsArray()
        # had to do this because conus1 mask is all 0's
        if self.version == 1:
            self.conus_mask_array += 1

        self.check_inputs_exist()
        self.check_destination()

    def check_inputs_exist(self):
        """ Look for each input file to see if it exists

        @return: the list of missing input files
        """
        missing = []
        for name, file in self.files.items():
            if not os.path.isfile(os.path.join(self.local_path, file)):
                missing.append(file)
                logging.error(f'CONUS sources did not find {name} at {os.path.join(self.local_path, file)}')
        return missing

    def check_destination(self):
        """ make sure the local folder to store inputs exists

        @return: True if folder exists, raises Exception if local destination folder not found
        """
        if not os.path.isdir(self.local_path):
            msg = f'Destination {self.local_path} for CONUS{self.version} input file does not exist'
            logging.exception(msg)
            raise Exception(msg)
        return True
