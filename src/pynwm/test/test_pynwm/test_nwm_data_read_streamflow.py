import os
import tempfile

from netCDF4 import Dataset
from dateutil import parser
import numpy as np
import numpy.ma as ma
import pytest

from pynwm import nwm_data, constants


_file_to_read_streamflow = os.path.join(tempfile.gettempdir(),
                                        'file_to_read_streamflow.nc')


@pytest.fixture(scope='module')
def file_to_read_streamflow_setup(request):
    ids = [2, 4, 6]
    flows = [1.3, -9999.0, 5.1]
    date = '2017-04-29_04:00:00'
    flows = ma.masked_array(flows, mask=[0, 1, 0])  # explicit mask
    with Dataset(_file_to_read_streamflow, 'w') as nc:
        nc.model_output_valid_time = date
        dim = nc.createDimension('feature_id', 3)
        id_var = nc.createVariable('feature_id', 'i', ('feature_id',))
        id_var[:] = ids
        flow_var = nc.createVariable('streamflow', 'f', ('feature_id',),
                                     fill_value=-9999.0)
        flow_var[:] = flows
    def file_to_read_streamflow_teardown():
        os.remove(_file_to_read_streamflow)
    request.addfinalizer(file_to_read_streamflow_teardown)


def test_read_streamflow_values_and_date(file_to_read_streamflow_setup):
    '''Should return list of streamflow values and applicable datetime.'''

    returned = nwm_data.read_streamflow(_file_to_read_streamflow, [6, 2])

    expected = pytest.approx([5.1, 1.3])
    assert expected == list(returned['flows'])

    expected = parser.parse('2017-04-29 04:00:00-00')
    assert expected == returned['datetime']


def test_read_streamflow_with_mask(file_to_read_streamflow_setup):
    '''Should preserve mask.'''

    returned = nwm_data.read_streamflow(_file_to_read_streamflow, [4])

    expected = pytest.approx([-9999.0])
    assert expected == list(returned['flows'].filled())
