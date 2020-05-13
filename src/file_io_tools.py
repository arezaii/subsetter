import os
import sys
import pandas as pd
import pfio
import gdal
import numpy as np
from global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA

"""
Common disk I/O operations
"""


def read_file(infile):
    """
    read an input file and return a 3d numpy array
    in (z,y,x) format
    """
    # get extension
    ext = os.path.splitext(os.path.basename(infile))[1]
    if ext in ['.tif', '.tiff']:
        res_arr = gdal.Open(infile).ReadAsArray()
        if len(res_arr.shape) == 2:
            res_arr = res_arr[np.newaxis, ...]
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


def write_pfb(data, outfile, x0, y0, z0, dx, dz):
    """
    Write a 3d numpy array to a PFB output file
    """
    pfio.pfwrite(data, outfile, float(x0), float(y0), float(z0), float(dx), float(dx), float(dz))


def write_bbox(bbox, outfile):
    """
    Write bounding box values to tab separated text file
    """
    with open(outfile, 'w') as fp:
        fp.write('y1\ty2\tx1\tx2\n')
        fp.write('\t'.join('%d' % x for x in bbox))


def read_bbox(bbox_file):
    """
    Parse a tab separated bounding box text file and return the array of values as integers
    """
    with open(bbox_file, 'r') as bbox:
        lines = bbox.readlines()
        return [int(s) for s in lines[1].split('\t')]


def write_array_to_geotiff(out_raster_path, data, geo_transform, projection, dtype=gdal.GDT_Int32, no_data=NO_DATA):
    """
    write a numpy array to a geotiff

    """
    np.flip(data, axis=0)
    driver = gdal.GetDriverByName('GTiff')
    no_bands, rows, cols = data.shape
    data_set = driver.Create(out_raster_path, xsize=cols, ysize=rows, bands=no_bands, eType=dtype,
                             options=['COMPRESS=LZW'])
    data_set.SetGeoTransform(geo_transform)
    data_set.SetProjection(projection)
    for i, image in enumerate(data, 1):
        data_set.GetRasterBand(i).WriteArray(image)
        data_set.GetRasterBand(i).SetNoDataValue(no_data)
    data_set = None