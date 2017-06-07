import os
import tempfile

from netCDF4 import Dataset
from dateutil import parser
import numpy as np
import numpy.ma as ma
import pytest

from pynwm import nwm_data

_tempdir = tempfile.gettempdir()
_files_to_cube = [os.path.join(_tempdir, 'files_to_cube{0}.nc'.format(i))
                  for i in range(3)]
_ids = [2, 4, 6]
_flows_template = [3.0, 4.5, 5.0]


@pytest.fixture(scope='module')
def files_to_cube_setup(request):
    date_template = '2017-04-29_0{0}:00:00'
    for i, nc_file in enumerate(_files_to_cube):
        date = date_template.format(i)
        flows = [flow * (i + 1) for flow in _flows_template]
        if i == 1:
            flows[1] = -9999.0  # one way of masking data
        elif i == 2:
            flows = ma.masked_array(flows, mask=[0, 1, 0])  # explicit mask
        with Dataset(nc_file, 'w') as nc:
            nc.model_output_valid_time = date
            dim = nc.createDimension('feature_id', 3)
            id_var = nc.createVariable('feature_id', 'i', ('feature_id',))
            id_var[:] = _ids
            flow_var = nc.createVariable('streamflow', 'f', ('feature_id',),
                                         fill_value=-9999.0)
            flow_var[:] = flows
    def files_to_cube_teardown():
        for nc_file in _files_to_cube:
            os.remove(nc_file)
    request.addfinalizer(files_to_cube_teardown)


def test_no_files_to_cube():
    '''Should return None if no files to combine.'''

    expected = None
    returned = nwm_data.build_streamflow_cube([])
    assert expected == returned


def test_cube_has_input_ids(files_to_cube_setup):
    '''Output cube should only include flow for input ids.'''

    ids = [2, 6]
    q, t = nwm_data.build_streamflow_cube(_files_to_cube, ids)
    returned = list(q[:,0])
    expected = pytest.approx([3, 6, 9])
    assert expected == returned
    returned = list(q[:,1])
    expected = pytest.approx([5, 10.0, 15])
    assert expected == returned


def test_cube_has_mask(files_to_cube_setup):
    '''Output cube should return -9999.0 for masked values.'''

    ids = [4]
    q, t = nwm_data.build_streamflow_cube(_files_to_cube, ids)
    returned = list(q[:,0])
    expected = pytest.approx([4.5, -9999.0, -9999.0])
    assert expected == returned


def test_cube_dates(files_to_cube_setup):
    '''Output cube should concatenate dates in input.'''

    ids = [2]
    q, t = nwm_data.build_streamflow_cube(_files_to_cube, ids)
    returned = list(t)
    expected = [parser.parse('2017-04-29 0{0}:00:00-00'.format(i))
                for i in range(3)]
    assert expected == returned
