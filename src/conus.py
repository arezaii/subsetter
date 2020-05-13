import os


class Conus:
    """
    Information about the CONUS dataset we are working with
    """
    def __init__(self, version, local_path):
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
            self.cyverse_path = '/iplant/home/shared/avra/CONUS2.0/Inputs/domain/'
            self.local_path = local_path
        self.check_destination

    def check_inputs_exist(self):
        """
        Look for each input file to see if it exists
        :return: the list of missing input files
        """
        missing = []
        for file in self.files.values():
            if not os.path.isfile(os.path.join(self.local_path, file)):
                missing.append(file)
        return missing

    @property
    def check_destination(self):
        """
        make sure the local folder to store inputs exists
        :return: True if folder exists, raises Exception if local destination folder not found
        """
        if not os.path.isdir(self.local_path):
            raise Exception(f'Destination {self.local_path} for CONUS{self.version} input file does not exist')
        return True
