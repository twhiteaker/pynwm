#!/usr/bin/python2
"""Reads data from a National Water Model file."""

import numpy as np
from dateutil import parser as date_parser
import pytz
from netCDF4 import Dataset, num2date

import constants 


def get_schema(nc_dataset):
    v1_0_dim = constants.SCHEMAv1_0['id_dim']
    if v1_0_dim in nc_dataset.dimensions:
        schema = constants.SCHEMAv1_0
    else:
        schema = constants.SCHEMAv1_1
    return schema


def get_id_indices(find_ids, all_ids):
    if len(find_ids) and type(find_ids[0]) is str:
        find_ids = [int(x) for x in find_ids]
    if type(find_ids) != 'numpy.ndarray':
        find_ids = np.array(find_ids)
    if type(all_ids) != 'numpy.ndarray':
        all_ids = np.array(all_ids)
    sorted_index = all_ids.argsort()
    sorted_nc_comids = all_ids[sorted_index]
    found_index_sorted = np.searchsorted(sorted_nc_comids, find_ids)
    index = sorted_index[found_index_sorted]
    return index


def read_streamflow(nc_filename, river_ids):
    """Reads streamflow for a set of river identifiers in a given file.

    Reads streamflow in cubic meters per second for a set of rivers
    from a National Water Model simulation result file.

    Args:
        nc_filename: Filename of input netCDF file of model results.
        river_ids: List or numpy array of integers representing feature
            identifiers for the rivers whose streamflow value is to be
            returned. These are NHD COMIDs for U.S. rivers, and
            arbitrary identifiers for other rivers.

    Returns:
        A dictionary with a 'flows' array of streamflow values in
        cubic meters per second in the same order as the input river
        identifiers along with 'datetime' providing the date associated
        with the streamflow values. For example:

        {'flows': [10.3, 283.2, 3.6],
         'datetime': datetime.datetime(2016, 6, 21, 15, 0, tzinfo=<UTC>)}

    Example:
        >>> filename = 'example_file.nc'
        >>> comids = [5671187, 5670795]
        >>> result = nwm.read_streamflow(filename, comids)
        >>> print('ID {0}: {1} cms'.format(comids[0], result['flows'][0]))
        ID 5671187: 3.16675 cms
    """

    result = {}
    qs = {}

    with Dataset(nc_filename, 'r') as nc:
        schema = get_schema(nc)
        date = time_from_dataset(nc)
        result['datetime'] = date
        nc_ids = nc.variables[schema['id_var']][:]
        nc_q = nc.variables['streamflow']
        indices = get_id_indices(river_ids, nc_ids)
        result['flows'] = nc_q[indices]
    return result


def time_from_dataset(nc_dataset):
    if 'time' in nc_dataset.variables:
        var = nc_dataset.variables['time']
        units = var.units
        val = var[0]
        date = num2date(val, units)       
    elif 'model_output_valid_time' in nc_dataset.ncattrs():
        date = date_parser.parse(
            nc_dataset.model_output_valid_time.replace('_', ' '))
    else:
        raise ValueError('Could not find model output time in netCDF dataset.')
    if date.tzinfo is None:
        date = date.replace(tzinfo=pytz.utc)
    return date


def build_streamflow_cube(nc_files, river_ids=None, consistent_id_order=True):
    """Reads streamflow from several NWM files into a single array.

    Reads streamflow from several files into a single array. Each file
    from the National Water Model represents a single time step. This
    function can be used to read the streamflow values for all time
    steps in a given simulation into a single multidimensional numpy
    array. Only streamflow for the input rivers are included in the
    result.

    Args:
        nc_files: List of netCDF filenames.
        river_ids: (Optional) List or numpy array of integer identifiers
            for the rivers whose streamflow value is to be returned. If
            None, all rivers are used in the same order as the first file
            provided.
        consistent_id_order: (Optional) True if the order of Ids in all
            files is the same; False otherwise. If True, this speeds up
            processing a bit.

    Returns:
        Tuple consisting of:
            streamflow array (float)
            time array (date)
        The streamflow array is sized by (number of time steps, number
        of rivers) and the time array is sized by (number of files). 

    Example:
        >>> file_pattern = 'nwm.t00z.short_range.channel_rt.f00{0}.conus.nc.gz'
        >>> files = [file_pattern.format(i + 1) for i in range(15)]
        >>> comids = [5671187, 5670795]
        >>> q, t = nwm_data.build_streamflow_cube(files, comids)
    """

    if not len(nc_files):
        return
    if river_ids is not None and len(river_ids) > 0:
        num_rivers = len(river_ids)
    else:
        nc_file = nc_files[0]
        with Dataset(nc_files[0], 'r') as nc:
            num_rivers = len(nc.variables['streamflow'])
            schema = get_schema(nc)
            river_ids = nc.variables[schema['id_var']][:]

    indices = None
    #out_q = np.zeros((len(nc_files), num_rivers))
    out_q = np.empty((len(nc_files), num_rivers))
    out_t = []

    fill_value = constants.SCHEMAv1_1['fill_val_float']
    for i, nc_file in enumerate(nc_files):
        with Dataset(nc_file, 'r') as nc:
            schema = get_schema(nc)
            out_t.append(time_from_dataset(nc))
            if indices is None or not consistent_id_order:
                nc_ids = nc.variables[schema['id_var']][:]
                indices = get_id_indices(river_ids, nc_ids)
            q = nc.variables['streamflow'][indices]
            if isinstance(q, np.ma.MaskedArray):
                q = q.filled()  # Turns masked values into fill values
            # Assume values <= fill_value are fills
            q[q <= fill_value] = fill_value
            out_q[i] = q
    return out_q, out_t
