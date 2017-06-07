import os
import tempfile

from netCDF4 import Dataset

from pynwm import nwm_data, constants


def test_get_schema():
    '''Should identify schema from id dimension in netCDF file.'''

    tempdir = tempfile.gettempdir()
    v1_0_dim = 'station'
    v1_1_dim = 'feature_id'

    v1_0_file = os.path.join(tempdir, 'v1_0.nc')
    with Dataset(v1_0_file, 'w') as nc:
        dim = nc.createDimension(v1_0_dim, None)
    expected = constants.SCHEMAv1_0
    returned = nwm_data.get_schema(nc)
    assert expected == returned
    os.remove(v1_0_file)
    
    v1_1_file = os.path.join(tempdir, 'v1_1.nc')
    with Dataset(v1_1_file, 'w') as nc:
        dim = nc.createDimension(v1_1_dim, None)
    expected = constants.SCHEMAv1_1
    returned = nwm_data.get_schema(nc)
    assert expected == returned
    os.remove(v1_1_file)
