import os
from os.path import join
import tempfile

from netCDF4 import Dataset, num2date
from dateutil import parser
import numpy as np
import numpy.ma as ma
import pytest

from pynwm import nwm_subset

_ids_in_order_nc = join(tempfile.gettempdir(), 'ids_in_order.nc')
_ids_not_in_order_nc = join(tempfile.gettempdir(), 'ids_not_in_order.nc')


@pytest.fixture(scope='module')
def file_to_combine_setup(request):
    file_pattern = 'combine_me_comids_{0}consistent{1}.nc'
    tempdir = tempfile.gettempdir()
    consistent_id_order = [join(tempdir, file_pattern.format('', i))
                           for i in range(3)]
    inconsistent_id_order = [join(tempdir, file_pattern.format('in', i))
                             for i in range(3)]
    ids = [2, 4, 6, 8]
    flows_template = [3.1, 2.2, 5.0, 7.1]
    date_template = '2017-04-29_0{0}:00:00'
    for i, nc_file in enumerate(consistent_id_order):
        date = date_template.format(i)
        flows = [flow * (i + 1) for flow in flows_template]
        if i == 1:
            flows[1] = -9999.0  # one way of masking data
        elif i == 2:
            flows = ma.masked_array(flows, mask=[0, 1, 0, 0])  # explicit mask
        with Dataset(nc_file, 'w') as nc:
            nc.model_output_valid_time = date
            dim = nc.createDimension('feature_id', 4)
            id_var = nc.createVariable('feature_id', 'i', ('feature_id',))
            id_var[:] = ids
            flow_var = nc.createVariable('streamflow', 'f', ('feature_id',),
                                         fill_value=-9999.0)
            flow_var[:] = flows
    nwm_subset.combine_files(consistent_id_order, _ids_in_order_nc)

    for i, nc_file in enumerate(inconsistent_id_order):
        date = date_template.format(i)
        flows = [flow * (i + 1) for flow in flows_template]
        if i == 1:
            comids = ids[::-1]
            flows = flows[::-1]
        else:
            comids = ids
        with Dataset(nc_file, 'w') as nc:
            nc.model_output_valid_time = date
            dim = nc.createDimension('feature_id', 4)
            id_var = nc.createVariable('feature_id', 'i', ('feature_id',))
            id_var[:] = comids
            flow_var = nc.createVariable('streamflow', 'f', ('feature_id',),
                                         fill_value=-9999.0)
            flow_var[:] = flows
    nwm_subset.combine_files(inconsistent_id_order, _ids_not_in_order_nc,
                             river_ids=[2], consistent_id_order=False)

    delete_me = consistent_id_order + inconsistent_id_order
    for filename in delete_me:
        os.remove(filename)
    def file_to_combine_teardown():
        os.remove(_ids_in_order_nc)
        os.remove(_ids_not_in_order_nc)
    request.addfinalizer(file_to_combine_teardown)


def test_inconsistent_id_order(file_to_combine_setup):
    with Dataset(_ids_not_in_order_nc) as nc:
        expected = 1
        assert expected == len(nc.dimensions['feature_id'])
        expected = [2]
        assert expected == list(nc.variables['feature_id'])
        expected = pytest.approx([3.1, 6.2, 9.3])
        assert expected == list(nc.variables['streamflow'])


def test_combined_dims(file_to_combine_setup):
    with Dataset(_ids_in_order_nc) as nc:
        dims = nc.dimensions
        assert 'time' in dims
        assert 3 == len(dims['time'])
        assert 'feature_id' in dims
        assert 4 == len(dims['feature_id'])


def test_combined_time(file_to_combine_setup):
    date_template = '2017-04-29 0{0}:00:00'
    expected = [parser.parse(date_template.format(i)) for i in range(3)]
    with Dataset(_ids_in_order_nc) as nc:
        var = nc.variables['time']
        returned = list(num2date(var[:], var.units))
        assert expected == returned


def test_combined_ids(file_to_combine_setup):
    expected = [2, 4, 6, 8]
    with Dataset(_ids_in_order_nc) as nc:
        returned = list(nc.variables['feature_id'])
        assert expected == returned


def test_combined_streamflow(file_to_combine_setup):
    expected = pytest.approx([5, 10, 15])
    with Dataset(_ids_in_order_nc) as nc:
        returned = list(nc.variables['streamflow'][:,2])
        assert expected == returned
