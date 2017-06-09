#!/usr/bin/python2
"""Extracts data from National Water Model files into new files."""

import os

from netCDF4 import Dataset, date2num
import numpy as np
import pytz

import constants 
import nwm_data


def subset_channel_file(in_nc_filename, out_nc_filename, river_ids,
                        just_streamflow=False):
    """Extracts data from an input channel file to a new file.

    A National Water Model channel file contains data related to river
    channels such as streamflow. This function makes a copy of that file
    but only includes data for the provided river identifiers.

    The input and output files are netCDF files.

    Args:
        in_nc_filename: Filename of input netCDF file of model results.
        out_nc_filename: Filename for the resulting subsetted file.
        river_ids: List or numpy array of integer identifiers for the
            rivers to be included in the subsetted file.
        just_streamflow: (Optional) True if other hydrologic variables
            such as velocity and channel inflow should be excluded.
            False if all variables should be included.
    """

    with Dataset(in_nc_filename, 'r') as in_nc:
        schema = nwm_data.get_schema(in_nc)
        if just_streamflow:
            vars_to_include = ['streamflow', schema['id_var'],
                               'time', 'reference_time']
        else:
            vars_to_include = in_nc.variables.keys()
        nc_ids = in_nc.variables[schema['id_var']][:]
        if river_ids is None:
            river_ids = nc_ids[:]
        index = nwm_data.get_id_indices(river_ids, nc_ids)
        with Dataset(out_nc_filename, 'w', format=in_nc.data_model) as out_nc:
            out_nc.setncatts({k: in_nc.getncattr(k) for k in in_nc.ncattrs()})

            for name, dim in in_nc.dimensions.iteritems():
                length = len(dim) if not dim.isunlimited() else None
                if name == schema['id_var']:
                    out_nc.createDimension(name, len(river_ids))
                else:
                    out_nc.createDimension(name, length)

            for name, var in in_nc.variables.iteritems():
                if name in vars_to_include:
                    out_var = out_nc.createVariable(
                        name, var.datatype, var.dimensions)
                    attributes = {k: var.getncattr(k) for k in var.ncattrs()}
                    out_var.setncatts(attributes)
                    dims = var.dimensions
                    if len(dims) == 1 and dims[0] == schema['id_dim']:
                        out_var[:] = var[index]
                    else:
                        out_var[:] = var[:]


def get_files_exist(nc_files):
    files = [f for f in nc_files if os.path.isfile(f)]
    not_files = [f for f in nc_files if not os.path.isfile(f)]
    if not_files:
        file_list = '\n'.join(not_files)
        m = 'Warning: These input files do not exist.\n{0}'.format(file_list)
        print(m)
    return files


def _dates_to_naive_utc(date_objects):
    """Converts dates to UTC time zone and strips time zone info.

    Date objects can be time zone aware. If the input date objects are time
    zone aware, they are converted to UTC time and then the time zone info is
    removed from the resulting object.

    If inputs dates are not time zone aware, no conversion occurs. Therefore,
    care should be taken NOT to provide time zone naive dates that are not
    already in UTC time.

    Args:
        date_objects: List of date objects.

    Returns:
        List of time zone naive date objects converted to UTC time.
    """

    if len(date_objects) == 0:
        return
    naive_dates = []
    for date in date_objects:
        if date.tzinfo is not None and date.tzinfo.utcoffset(date) is not None:
            date = date.astimezone(pytz.utc)
        naive_dates.append(date.replace(tzinfo=None))
    return naive_dates


def combine_files(nc_files, output_file, river_ids=None,
                  consistent_id_order=True):
    """Combines streamflow from several files into a single netCDF file.

    Each file from the National Water Model represents a single time
    step. This function combines the streamflow from multiple files into
    a single netCDF file. Provide an array of river identifiers to
    subset the data. Note that if you want to combine files in their
    entirety, you may want to try the external utilities NCO and ncrcat
    instead.

    Args:
        nc_files: List of netCDF filenames.
        output_file: The output netCDF file.
        river_ids: (Optional) List or numpy array of integer river
            identifiers to include in the output. If None, all rivers
            are used.
        consistent_id_order: (Optional) True if the order of Ids in all
            files can be safely assumed to be the same; False otherwise.
            If True, this speeds up processing a bit.

    Example:
        >>> file_pattern = 'nwm.t00z.short_range.channel_rt.f00{0}.conus.nc'
        >>> files = [file_pattern.format(i + 1) for i in range(18)]
        >>> comids = [5671187, 5670795]
        >>> nwm_subset.combine_files(files, 'combined.nc', comids)
    """

    nc_files = get_files_exist(nc_files)
    if not nc_files:
        raise Exception('No files to combine')
    if river_ids is None:
        with Dataset(nc_files[0], 'r') as nc:
            schema = nwm_data.get_schema(nc)
            river_ids = nc.variables[schema['id_var']][:]
    elif len(river_ids) and type(river_ids[0]) is str:
        river_ids = [int(x) for x in river_ids]

    q, t = nwm_data.build_streamflow_cube(
        nc_files, river_ids, consistent_id_order)
    t = _dates_to_naive_utc(t)
    num_rivers = len(q[0])

    out_schema = constants.SCHEMAv1_1
    id_dim = out_schema['id_dim']
    id_var = out_schema['id_var']
    q_type = out_schema['flow_dtype']
    time_units = 'minutes since {0}'.format(constants.SINCE_DATE)
    fill_value = out_schema['fill_val_int']
    with Dataset(output_file, 'w') as nc:
        nc.createDimension('time', len(nc_files))
        nc.createDimension(id_dim, num_rivers)

        time_var = nc.createVariable('time', 'i', ('time',))
        for name_value in out_schema['time_attrs']:
            time_var.setncattr(name_value[0], name_value[1])
        time_var.units = time_units
        time_var[:] = [round(d) for d in date2num(t, time_units)]

        id_var = nc.createVariable(id_var, 'i', (id_dim,))
        for name_value in out_schema['id_attrs']:
            id_var.setncattr(name_value[0], name_value[1])
        id_var[:] = river_ids

        q_var = nc.createVariable('streamflow', q_type, ('time', id_dim),
                                  fill_value=fill_value)
        for name_value in out_schema['flow_attrs']:
            q_var.setncattr(name_value[0], name_value[1])
        q_var[:] = q
