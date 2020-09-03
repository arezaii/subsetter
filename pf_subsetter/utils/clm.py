import numpy as np
import pf_subsetter.utils.io as file_io_tools
from pf_subsetter.clipper import MaskClipper


class ClmClipper:

    def __init__(self, subset_mask):
        """Clip CLM datafiles lat/lon and land cover

        @param subset_mask: SubsetMask object for the mask
        """
        self.subset_mask = subset_mask
        self.clipper = MaskClipper(subset_mask)

    def clip_latlon(self, lat_lon_file):
        """ Clip the domain lat/lon data to the bounding box of the mask

        @param lat_lon_file: lat/lon data for the domain
        @return: the formatted output (1d) and the raw clipped data array (3d)
        """
        data = file_io_tools.read_file(lat_lon_file)
        clipped_data, _, clipped_mask, bbox = self.clipper.subset(data_array=data, crop_inner=0)
        sa_formatted = np.flip(clipped_data, axis=1).flatten()
        return sa_formatted, clipped_data

    def clip_land_cover(self, lat_lon_array, land_cover_file):
        """ Clip the domain land cover data to the bounding box of the mask

        @param lat_lon_array: clipped lat/lon data for the masked area
        @param land_cover_file: land cover file for the domain
        @return: simple ascii representation (1d) of the data, vegm formatted representation of the data (2d)
        """
        lat_lon_proper = np.char.split(lat_lon_array.astype(str), ' ')
        data = file_io_tools.read_file(land_cover_file)
        clipped_data, _, clipped_mask, bbox = self.clipper.subset(data_array=data, crop_inner=0)
        sa_formatted = np.flip(clipped_data, axis=1).flatten()
        sand = 0.16
        clay = 0.26
        color = 2
        # get value of land cover for each coordinate
        npoints = sa_formatted.shape[0]
        # make output matrix
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
        cols = [int(i) + 6 for i in sa_formatted]
        rows = list(range(npoints))
        output[rows, cols] = 1
        return sa_formatted, output

    def write_land_cover(self, land_cover_data, out_file):
        """ Write the land cover file in vegm format

        @param land_cover_data: formatted vegm data (2d array)
        @param out_file: path and name to write output
        @return: None
        """
        heading = "x y lat lon sand clay color fractional coverage of grid, by vegetation class (Must/Should Add to " \
                  "1.0) "
        col_names = ['', '', '(Deg)', '(Deg)', '(%/100)', '', 'index', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                     '10', '11',
                     '12', '13', '14', '15', '16', '17', '18']
        header = '\n'.join([heading, ' '.join(col_names)])
        file_io_tools.write_array_to_simple_ascii(out_file=out_file, data=land_cover_data, header=header,
                                                  fmt=['%d'] * 2 + ['%.6f'] * 2 + ['%.2f'] * 2 + ['%d'] * 19)

    def write_lat_lon(self, lat_lon_data, out_file, x=0, y=0, z=0):
        """ Write the lat/lon data to a ParFlow simple ascii formatted file

        @param lat_lon_data: lat/lon data in formatted 1d array
        @param out_file: path and name for output file
        @param x: size of x dimension
        @param y: size of y dimension
        @param z: size of z dimension
        @return: None
        """
        file_io_tools.write_array_to_simple_ascii(out_file=out_file, data=lat_lon_data, fmt='%s', header=f'{x} {y} {z}')
