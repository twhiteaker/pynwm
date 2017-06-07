import os
import tempfile

from netCDF4 import Dataset
import numpy.ma as ma
import pytest

from pynwm import nwm_subset


_file_to_subset = os.path.join(tempfile.gettempdir(), 'file_to_subset.nc')


@pytest.fixture(scope='module')
def file_to_subset_setup(request):
    ids = [2, 4, 6]
    flows = [3.1, -9999.0, 5.0]
    date = '2017-04-29_00:00:00'
    flows = ma.masked_array(flows, mask=[0, 1, 0])  # explicit mask
    with Dataset(_file_to_subset, 'w') as nc:
        nc.model_output_valid_time = date
        dim = nc.createDimension('feature_id', 3)
        id_var = nc.createVariable('feature_id', 'i', ('feature_id',))
        id_var[:] = ids
        flow_var = nc.createVariable('streamflow', 'f', ('feature_id',),
                                     fill_value=-9999.0)
        flow_var[:] = flows
        extra_var = nc.createVariable('extra_var', 'i', ('feature_id',))
        extra_var[:] = [1, 2, 3]
    def file_to_subset_teardown():
        os.remove(_file_to_subset)
    request.addfinalizer(file_to_subset_teardown)


def compare_dims(in_nc, out_nc):
    assert in_nc.dimensions.keys() == out_nc.dimensions.keys()
    for dim in in_nc.dimensions:
        if dim != 'feature_id':
            expected = len(in_nc.dimensions[dim])
        else:
            expected = 1
        assert expected == len(out_nc.dimensions[dim])


def compare_vars(in_nc, out_nc):
    for var in out_nc.variables:
        expected = in_nc.variables[var].ncattrs()
        assert expected == out_nc.variables[var].ncattrs()
        if var == 'streamflow':
            expected = pytest.approx([3.1])
        elif var == 'feature_id':
            expected = [2]
        elif var == 'extra_var':
            expected = [1]
        else:
            expected = list(in_nc.variables[var][:])
        assert expected == list(out_nc.variables[var][:])


def test_subset_all_vars(file_to_subset_setup):
    '''Output file should include all variables and attributes from input.'''

    ids = [2]
    out_file = os.path.join(tempfile.gettempdir(), 'subset_all_vars.nc')
    nwm_subset.subset_channel_file(_file_to_subset, out_file, ids)
    with Dataset(_file_to_subset) as in_nc, Dataset(out_file) as out_nc:
        compare_dims(in_nc, out_nc)
        assert in_nc.ncattrs() == out_nc.ncattrs()
        assert in_nc.variables.keys() == out_nc.variables.keys()
        compare_vars(in_nc, out_nc)
    os.remove(out_file)


def test_subset_just_streamflow(file_to_subset_setup):
    '''Output file should include just streamflow variable.'''

    ids = [2]
    out_file = os.path.join(tempfile.gettempdir(), 'subset_just_q.nc')
    nwm_subset.subset_channel_file(_file_to_subset, out_file, ids,
                                   just_streamflow=True)
    with Dataset(_file_to_subset) as in_nc, Dataset(out_file) as out_nc:
        compare_dims(in_nc, out_nc)
        assert in_nc.ncattrs() == out_nc.ncattrs()
        expected = ['feature_id', 'streamflow']
        assert expected == out_nc.variables.keys()
        compare_vars(in_nc, out_nc)
    os.remove(out_file)


def test_subset_with_mask(file_to_subset_setup):
    '''Output file should preserve masked values.'''

    ids = [4]
    out_file = os.path.join(tempfile.gettempdir(), 'subset_with_mask.nc')
    nwm_subset.subset_channel_file(_file_to_subset, out_file, ids,
                                   just_streamflow=True)
    with Dataset(out_file) as nc:
        expected = pytest.approx([-9999.0])
        assert expected == list(nc.variables['streamflow'][:].filled())
    os.remove(out_file)
