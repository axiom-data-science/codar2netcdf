import os
from decimal import Decimal
from datetime import datetime

import pytz
import netCDF4
import numpy as np
import pandas as pd
from dateutil.parser import parse

import logging
logger = logging.getLogger('codar2netcdf')
logger.addHandler(logging.NullHandler())


class CodarAsciiTotals(object):

    def __init__(self, ascii_file):

        headers = None  # row index of the headers
        units = None  # row index of units
        self.grid_spacing = None

        with open(ascii_file, 'r') as f:
            for i, line in enumerate(f):
                if '%TimeStamp' in line:
                    line = [ int(x.strip()) for x in line.split(' ')[1:] if x ]
                    timestamp = datetime(*line)
                elif '%TimeZone' in line:
                    line = [ x.strip() for x in line.split(' ')[1:] if x ]
                    timezone = line[0].replace('"', '')
                elif '%Origin' in line:
                    line = [ x.strip() for x in line.split(' ')[1:] if x ]
                    self.origin_x = Decimal(line[1])
                    self.origin_y = Decimal(line[0])
                elif '%GridSpacing' in line:
                    self.grid_spacing = float([ x.strip() for x in line.split(' ')[1:] if x ][0]) * 1000.
                elif '%TableStart' in line:
                    headers = i + 1
                    units = headers + 1
                elif i == headers:
                    self.headers = [ x.strip() for x in line.split('  ')[1:] if x ]
                    self.headers += ['', '']  # Site Contributors
                elif i == units:
                    self.units = [ x.strip().replace('(', '').replace(')', '') for x in line.split('  ')[1:] if x ]
                    break

        try:
            self.origin_time = parse('{} {}'.format(timestamp, timezone))
            self.data = pd.read_csv(ascii_file, comment='%', sep=' ', header=None, names=self.headers, na_values=['999.000'], skipinitialspace=True)
        except BaseException:
            logger.error("Could not parse ASCII Totals file")
            self.origin_time = None
            self.data = pd.DataFrame()

    def is_valid(self):
        return not self.data.empty

    def export(self, output_file, ascii_grid):

        if not self.is_valid():
            raise ValueError("Could not export ASCII data, the input file was invalid.")

        if os.path.isfile(output_file):
            os.remove(output_file)

        with netCDF4.Dataset(output_file, 'w', clobber=True) as nc:

            x_dist, y_dist = self.make_i_j_grid(nc, ascii_grid)

            fillvalue = -999.9

            nc.createDimension('time', 1)
            time = nc.createVariable('time', int, ('time',), fill_value=int(fillvalue))
            time.setncatts({
                'units' : 'seconds since 1970-01-01 00:00:00',
                'standard_name' : 'time',
                'long_name': 'time',
                'calendar': 'gregorian'
            })
            time[:] = netCDF4.date2num(self.origin_time.astimezone(pytz.utc).replace(tzinfo=None), units=time.units, calendar=time.calendar)

            nc.createDimension('z', 1)
            z = nc.createVariable('z', int, ('z',), fill_value=int(fillvalue))
            z.setncatts({
                'units' : 'm',
                'standard_name' : 'depth',
                'long_name' : 'depth',
                'positive': 'down',
                'axis': 'Z'
            })
            z[:] = 0

            u_values = np.ma.masked_all((self.size_x, self.size_y))
            v_values = np.ma.masked_all((self.size_x, self.size_y))
            for i, r in self.data.iterrows():
                xi = np.where(x_dist==r['X Distance'])  # noqa
                yi = np.where(y_dist==r['Y Distance'])  # noqa
                u_values[xi, yi] = r['U comp']
                v_values[xi, yi] = r['V comp']

            # U
            u = nc.createVariable('u', 'f8', ('time', 'x', 'y'), fill_value=fillvalue, zlib=True)
            u[:] = u_values
            u_units = self.units[self.data.columns.tolist().index('U comp')]
            u.setncatts({
                'long_name': 'Eastward Surface Current ({})'.format(u_units),
                'standard_name': 'eastward_sea_water_velocity',
                'coordinates': 'time lon lat',
                'units': u_units,
            })

            # V
            v = nc.createVariable('v', 'f8', ('time', 'x', 'y'), fill_value=fillvalue, zlib=True)
            v[:] = v_values
            v_units = self.units[self.data.columns.tolist().index('V comp')]
            v.setncatts({
                'long_name': 'Northward Surface Current ({})'.format(v_units),
                'standard_name': 'northward_sea_water_velocity',
                'coordinates': 'time lon lat',
                'units': v_units
            })

            crs = nc.createVariable('crs', 'i4')
            crs.setncatts({
                'long_name' : 'http://www.opengis.net/def/crs/EPSG/0/4326',
                'grid_mapping_name' : 'latitude_longitude',
                'epsg_code' : 'EPSG:4326',
                'semi_major_axis' : float(6378137.0),
                'inverse_flattening' : float(298.257223563)
            })

            gas = {
                'time_coverage_start': self.origin_time.strftime("%Y-%m-%dT%H:%M:00Z"),
                'time_coverage_end': self.origin_time.strftime("%Y-%m-%dT%H:%M:00Z"),
                'date_created': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z"),
                'Conventions': 'CF-1.6',
                'Metadata_conventions': 'Unidata Dataset Discovery v1.0',
                'cdm_data_type': 'Grid',
                'geospatial_vertical_min': 0,
                'geospatial_vertical_max': 0,
                'geospatial_vertical_positive': 'down',
            }
            nc.setncatts(gas)

    def make_i_j_grid(self, nc, ascii_grid):

        with open(ascii_grid, 'r') as f:
            for i, line in enumerate(f):
                if 'max x index' in line:
                    grid_x = [ int(x) for x in line.split(' ')[0:2] ]
                elif 'max y index' in line:
                    grid_y = [ int(x) for x in line.split(' ')[0:2] ]
                elif 'Number of grid points' in line:
                    headers = [ x.strip() for x in line.split('(')[-1].replace('Columns:', '').replace(')', '').split(',') ]
                    nrows = int(line.split(' ')[0])
                    data = i + 1

        # Extract current data
        grid = pd.read_csv(ascii_grid, sep=' ', skipinitialspace=True, header=None, names=headers, skiprows=data, nrows=nrows)

        self.size_x = len(range(grid_x[0], grid_x[1] + 1))
        self.size_y = len(range(grid_y[0], grid_y[1] + 1))

        lat_values = grid['lat'].values.reshape(self.size_y, self.size_x).T
        lon_values = grid['lon'].values.reshape(self.size_y, self.size_x).T

        x_dist = np.unique(grid['x'].values)
        y_dist = np.unique(grid['y'].values)

        assert len(x_dist) == self.size_x
        assert len(y_dist) == self.size_y

        nc.createDimension('x', self.size_x)
        nc.createDimension('y', self.size_y)
        lat = nc.createVariable('lat', 'f8', ('x', 'y',), zlib=True)
        lat.setncatts({
            'units' : 'degrees_north',
            'standard_name' : 'latitude',
            'long_name' : 'latitude',
            'axis': 'Y'
        })
        lat[:] = lat_values

        lon = nc.createVariable('lon', 'f8', ('x', 'y',), zlib=True)
        lon.setncatts({
            'units' : 'degrees_east',
            'standard_name' : 'longitude',
            'long_name' : 'longitude',
            'axis': 'X'
        })
        lon[:] = lon_values

        nc.setncatts({
            'geospatial_lat_min': lat_values.min(),
            'geospatial_lat_max': lat_values.max(),
            'geospatial_lon_min': lon_values.min(),
            'geospatial_lon_max': lon_values.max(),
        })
        nc.sync()

        return x_dist, y_dist
