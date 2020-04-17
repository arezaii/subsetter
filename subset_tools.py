from src.conus import Conus
from src.conus_sources import CyVerseDownloader

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
