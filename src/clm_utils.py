import os

import numpy as np

import src.file_io_tools as file_io_tools
from src.clipper import Clipper


class ClmClipper:

    def __init__(self, mask_array, ds_ref):
        self.mask_array = mask_array
        self.ds_ref = ds_ref
        self.clipper = Clipper(mask_array, ds_ref)

    def clip_latlon(self, lat_lon_file):
        data = file_io_tools.read_file(lat_lon_file)
        clipped_data, clipped_geom, clipped_mask, bbox = self.clipper.subset(data_array=data, crop_inner=0)
        sa_formatted = np.flip(clipped_data, axis=1).flatten()
        return sa_formatted, clipped_data

    def clip_land_cover(self, lat_lon_array, land_cover_file):
        lat_lon_proper = np.char.split(lat_lon_array.astype(str), ' ')
        data = file_io_tools.read_file(land_cover_file)
        clipped_data, clipped_geom, clipped_mask, bbox = self.clipper.subset(data_array=data, crop_inner=0)
        sa_formatted = np.flip(clipped_data, axis=1).flatten()
        sand = 0.16
        clay = 0.26
        color = 2
        # get value of land cover for each coordinate
        npoints = sa_formatted.shape[0]
        ## make output matrix
        output = np.zeros((npoints, 25))
        output[:, 4] = sand
        output[:, 5] = clay
        output[:, 6] = color
        # assign x values, looping from 1 to x extent, holding y constant
        output[:, 0] = list(range(1, clipped_data.shape[2] + 1)) * clipped_data.shape[1]
        # assign y values, repeating each y value from 1 to y extent for every x
        output[:, 1] = np.repeat(range(1, clipped_data.shape[1] + 1), clipped_data.shape[2])
        # assign lat values
        output[:, 2] = [latlon[0] for latlon in lat_lon_proper]
        # assign lon values
        output[:, 3] = [latlon[1] for latlon in lat_lon_proper]
        cols = sa_formatted + 6
        rows = list(range(npoints))
        output[rows, cols] = 1
        return sa_formatted, output

    def write_land_cover(self, land_cover_data, out_file):
        heading = "x y lat lon sand clay color fractional coverage of grid, by vegetation class (Must/Should Add to " \
                  "1.0) "
        col_names = ['', '', '(Deg)', '(Deg)', '(%/100)', '', 'index', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                     '10', '11',
                     '12', '13', '14', '15', '16', '17', '18']
        header = '\n'.join([heading, ' '.join(col_names)])
        file_io_tools.write_array_to_simple_ascii(out_file=out_file, data=land_cover_data, header=header,
                   fmt=['%d'] * 2 + ['%.6f'] * 2 + ['%.2f'] * 2 + ['%d'] * 19)

    def write_lat_lon(self, lat_lon_data, out_file, x=0, y=0, z=0):
        file_io_tools.write_array_to_simple_ascii(out_file=out_file, data=lat_lon_data, fmt='%s', header=f'{x} {y} {z}')
