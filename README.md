# codar2netcdf  [![Build Status](https://travis-ci.org/axiom-data-science/codar2netcdf.svg?branch=master)](https://travis-ci.org/axiom-data-science/codar2netcdf)

Converting CODAR Total ASCII files (the final total current speed and direction
of the combined radial data) into CF NetCDF files.

## Installation

```
# pip
$ pip install codar2netcdf

# conda
$ conda install -c ioos codar2netcdf
```

## Usage

```python
In [1]: from codar2netcdf import CodarAsciiTotals
In [2]: w = CodarAsciiTotals('totals.txt')

# Pandas dataframe of the data
In [3]: w.data.head()
Out[3]:
   Longitude   Latitude  U comp  V comp  VectorFlag  U StdDev  V StdDev
0 -83.004520  25.569613 -14.822  43.085           0     12.89     23.04
1 -82.905005  25.569578 -19.047  45.790           0     14.71     24.21
2 -82.805491  25.569473   1.059   9.831           0     12.31     18.06
3 -83.104110  25.659845  -7.531  38.266           0      9.61     22.19
4 -83.004520  25.659880 -17.075  44.413           0     11.82     23.51
...

# Export to netCDF file
In [4]: w.export('out.nc', ascii_grid='grid.txt')

In [5]: import netCDF4
In [6]: netCDF4.Dataset('out.nc').variables
Out[6]:
OrderedDict([('time', <class 'netCDF4._netCDF4.Variable'>
              int64 time(time)
                  _FillValue: -999
                  units: seconds since 1970-01-01 00:00:00
                  standard_name: time
                  calendar: gregorian
                  long_name: time
              unlimited dimensions:
              current shape = (1,)
              filling on),

              ('lat', <class 'netCDF4._netCDF4.Variable'>
              float64 lat(x, y)
                  _FillValue: -999.9
                  units: degrees_north
                  standard_name: latitude
                  axis: Y
                  long_name: latitude
              unlimited dimensions:
              current shape = (130, 210)
              filling on),

              ('lon', <class 'netCDF4._netCDF4.Variable'>
              float64 lon(x, y)
                  _FillValue: -999.9
                  units: degrees_east
                  standard_name: longitude
                  axis: X
                  long_name: longitude
              unlimited dimensions:
              current shape = (130, 210)
              filling on),

              ('z', <class 'netCDF4._netCDF4.Variable'>
              int64 z(z)
                  _FillValue: -999
                  units: m
                  standard_name: depth
                  positive: down
                  axis: Z
                  long_name: depth
              unlimited dimensions:
              current shape = (1,)
              filling on),

              ('u', <class 'netCDF4._netCDF4.Variable'>
              float64 u(time, x, y)
                  _FillValue: -999.9
                  standard_name: eastward_sea_water_velocity
                  long_name: Eastward Surface Current (cm/s)
                  units: cm/s
                  coordinates: time lon lat
              unlimited dimensions:
              current shape = (1, 130, 210)
              filling on),

              ('v', <class 'netCDF4._netCDF4.Variable'>
              float64 v(time, x, y)
                  _FillValue: -999.9
                  standard_name: northward_sea_water_velocity
                  long_name: Northward Surface Current (cm/s)
                  units: cm/s
                  coordinates: time lon lat
              unlimited dimensions:
              current shape = (1, 130, 210)
              filling on),

              ('crs', <class 'netCDF4._netCDF4.Variable'>
              int32 crs()
                  long_name: http://www.opengis.net/def/crs/EPSG/0/4326
                  grid_mapping_name: latitude_longitude
                  epsg_code: EPSG:4326
                  inverse_flattening: 298.257223563
                  semi_major_axis: 6378137.0
              unlimited dimensions:
              current shape = ()
              filling on, default _FillValue of -2147483647 used)
])
```
