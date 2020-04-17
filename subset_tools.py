import os


class Conus:
    """
    Class to hold the information about the CONUS dataset we are working with
    """
    def __init__(self, version, local_path):
        self.version = version
        if self.version == 1:
            self.files = {
                'CONUS_MASK': 'Domain_Blank_Mask.tif',
                'SUBSURFACE_DATA': 'grid3d.v3.pfb',
                'PME': 'PmE.flux.pfb',
                'SLOPE_X': 'slopex.pfb',
                'SLOPE_Y': 'slopey.pfb'
            }
            self.cyverse_path = '/iplant/home/shared/avra/CONUS_1.0/SteadyState_Final/Other_Domain_Files/'
            self.local_path = local_path
        if self.version == 2:
            self.files = {
                'CONUS_MASK': 'conus_1km_PFmask2.tif',
                'SUBSURFACE_DATA': '3d-grid.v3.tif',
                'PME': 'PME.tif',
                'SLOPE_X': 'Str3Ep0_smth.rvth_1500.mx0.5.mn5.sec0.up_slopex.tif',
                'SLOPE_Y': 'sStr3Ep0_smth.rvth_1500.mx0.5.mn5.sec0.up_slopey.tif',
                'SINKS': 'conus_1km_PFmask_manualsinks.tif',
                'RESERVOIRS': 'conus_1km_PFmask_reservoirs.tif',
                'LAKE_BORDER': 'conus_1km_PFmask_selectLakesborder.tif',
                'LAKE_MASK': 'conus_1km_PFmask_selectLakesmask.tif',
                'CHANNELS': '1km_upscaledNWM_ChannelOrder5_mod2.tif',
                'CELL_TYPES': '1km_PF_BorderCellType.tif'
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


class CyVerseDownloader:
    from irods.session import iRODSSession
    from irods.exception import DataObjectDoesNotExist
    from pathlib import Path
    import os

    def __init__(self, username=os.environ.get('CYVERSE_USERNAME'),
                 password=os.environ.get('CYVERSE_PASSWORD'),
                 dest='.'):
        self.username = username
        self.password = password
        self.destination = dest

    def get_conus_data(self, file):
        with self.iRODSSession(host='data.cyverse.org',
                               port=1247,
                               user=self.username,
                               password=self.password,
                               zone='iplant') as session:
            try:
                obj = session.data_objects.get(file)
                # open(self.Path(file).name, 'wb').write(obj.open().read())
                with open(self.os.path.join(self.destination, self.Path(file).name), 'wb') as f:
                    with obj.open() as f_obj:
                        f.write(f_obj.read())
            except self.DataObjectDoesNotExist:
                print(f'could not locate {file}')


def main():
    #conus2 = Conus(2, 'CONUS2_Inputs')
    conus1 = Conus(1, 'CONUS1_Inputs')
    cdl = CyVerseDownloader(dest=conus1.local_path)
    for file in conus1.files.values():
        cdl.get_conus_data(f'{conus1.cyverse_path}{file}')
    missing_files = conus1.check_inputs_exist()
    if len(missing_files) > 0:
        print(f'Missing the following files {missing_files}')


if __name__ == '__main__':
    main()
