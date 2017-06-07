import os
import tempfile

from netCDF4 import Dataset, date2num
from dateutil import parser
import pytest
import pytz

from pynwm import nwm_data, constants


def test_time_from_variable():
    '''Should read date from time variable.'''

    tempdir = tempfile.gettempdir()
    nc_file = os.path.join(tempdir, 'test_time_from_variable.nc')
    date_obj = parser.parse('2017-04-29 04:00:00')
    units = 'minutes since 1970-01-01 00:00:00 UTC'
    nc_date = round(date2num(date_obj, units))
    with Dataset(nc_file, 'w') as nc:
        dim = nc.createDimension('time', 1)
        time_var = nc.createVariable('time', 'i', ('time',))
        time_var[:] = [nc_date]
        time_var.units = units
    with Dataset(nc_file, 'r') as nc:
        expected = date_obj.replace(tzinfo=pytz.utc)
        returned = nwm_data.time_from_dataset(nc)
        assert expected == returned
    os.remove(nc_file)


def test_time_from_attribute():
    '''Should read date from global attribute.'''

    tempdir = tempfile.gettempdir()
    nc_file = os.path.join(tempdir, 'test_time_from_attribute.nc')
    date = '2017-04-29_04:00:00'
    date_obj = parser.parse(date.replace('_', ' ') + '-00')
    with Dataset(nc_file, 'w') as nc:
        nc.model_output_valid_time = date
    with Dataset(nc_file, 'r') as nc:
        expected = date_obj
        returned = nwm_data.time_from_dataset(nc)
        assert expected == returned
    os.remove(nc_file)

def test_no_time_found():
    '''Should throw ValueError if no time information found.'''

    tempdir = tempfile.gettempdir()
    nc_file = os.path.join(tempdir, 'test_no_time_found.nc')
    with Dataset(nc_file, 'w') as nc:
        nc.not_looking_for_this_attribute = '2017-04-29_04:00:00'
    with pytest.raises(ValueError):
        with Dataset(nc_file, 'r') as nc:
            returned = nwm_data.time_from_dataset(nc)
    os.remove(nc_file)
