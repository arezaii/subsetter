import os
import sys
import pandas as pd
import pfio
import gdal
import numpy as np


def read_file(infile):
    # get extension
    ext = os.path.splitext(os.path.basename(infile))[1]
    if ext in ['.tif', '.tiff']:
        res_arr = gdal.Open(infile).ReadAsArray()
    elif ext == '.sa':  # parflow ascii file
        with open(infile, 'r') as fi:
            header = fi.readline()
        nx, ny, nz = [int(x) for x in header.strip().split(' ')]
        arr = pd.read_csv(infile, skiprows=1, header=None).values
        res_arr = np.reshape(arr, (nz, ny, nx))[:, ::-1, :]
    elif ext == '.pfb':  # parflow binary file
        res_arr = pfio.pfread(infile)
    else:
        print('can not read file type ' + ext)
        sys.exit()
    return res_arr
