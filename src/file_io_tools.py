import os
import sys
import pandas as pd
import pfio
import gdal
import numpy as np
from src.global_const import TIF_NO_DATA_VALUE_OUT as NO_DATA
import logging

"""
Common disk I/O operations
"""


def read_file(infile):
    """ read an input file and return a 3d numpy array

    @param infile: file to open (.pfb, .sa, .tif, .tiff)
    @return: a 3d numpy array with data from file in (z,y,x) format
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


def read_geotiff(infile):
    """ wrapper for reading geotifs with gdal

    @param infile: the geotif to open
    @return: gdal dataset
    """
    return gdal.Open(infile)


def write_pfb(data, outfile, x0=0, y0=0, z0=0, dx=1000, dz=1000):
    """ Write a 3d numpy array to a PFB output file

    @param data: 3d numpy data array to write to pfb !(x,y,z)!
    @param outfile: filename and path to write output
    @param x0: initial x location
    @param y0: initial y location
    @param z0: initial z location
    @param dx: horizontal resolution
    @param dz: vertical resolution
    @return: None
    """
    # TODO: why do other datatypes (float32) cause invalid pfb files?
    logging.info(f'wrote pfb file {outfile}, (z,y,x)={data.shape}')
    pfio.pfwrite(data.astype(np.float64), outfile, float(x0), float(y0), float(z0), float(dx), float(dx), float(dz))


def write_bbox(bbox, outfile):
    """ Write bounding box values to tab separated text file

    @param bbox: array of bounding box values [top, bot, left, right]
    @param outfile: where to write the file
    @return: None
    """
    logging.info(f'wrote bbox file {outfile}, {bbox}')
    with open(outfile, 'w') as fp:
        fp.write('y1\ty2\tx1\tx2\n')
        fp.write('\t'.join('%d' % x for x in bbox))


def read_bbox(bbox_file):
    """ Parse a tab separated bounding box text file and return the array of values as integers

    @param bbox_file: the file to read
    @return: an array of integers representing the bounding box [top, bot, left, right]
    """
    # TODO: Handle human readable format before handing back to system
    with open(bbox_file, 'r') as bbox:
        lines = bbox.readlines()
        return [int(s) for s in lines[1].split('\t')]


def write_array_to_geotiff(out_raster_path, data, geo_transform, projection, dtype=gdal.GDT_Int32, no_data=NO_DATA):
    """ write a numpy array to a geotiff

    @param out_raster_path: where to write the output file
    @param data: 3d array of data to write
    @param geo_transform: gdal formatted geoTransform to use for the geoTif
    @param projection: gdal formatted Projection to use for the geoTif
    @param dtype: gdal datatype to use for the geoTif
    @param no_data: no data value to encode in the geoTif
    @return: None
    """
    # flip the z axis for proper orientation
    np.flip(data, axis=0)
    driver = gdal.GetDriverByName('GTiff')
    no_bands, rows, cols = data.shape
    data_set = driver.Create(out_raster_path, xsize=cols, ysize=rows, bands=no_bands, eType=dtype,
                             options=['COMPRESS=LZW', 'NUM_THREADS=ALL_CPUS'])
    data_set.SetGeoTransform(geo_transform)
    data_set.SetProjection(projection)
    for i, image in enumerate(data, 1):
        data_set.GetRasterBand(i).WriteArray(image)
        data_set.GetRasterBand(i).SetNoDataValue(no_data)
    logging.info(f'wrote geotif {out_raster_path}, (bands,rows,cols)=({no_bands}, {rows}, {cols})')
    # noinspection PyUnusedLocal
    data_set = None


def write_array_to_simple_ascii(data, out_file, header, fmt, delimiter=' ', comments=''):
    """ write an array to ParFlow simple ascii (.sa) format

    @param data: the 3d numpy array of data to write
    @param out_file: where to write the data
    @param header: the header to use in the file
    @param fmt: the python string format to use for printing each element of the array
    @param delimiter: the delimiter character to use when writing the elements (optional)
    @param comments: the comment character to write for header (optional)
    @return: None
    """
    np.savetxt(fname=out_file, X=data, delimiter=delimiter, comments=comments, header=header, fmt=fmt)
