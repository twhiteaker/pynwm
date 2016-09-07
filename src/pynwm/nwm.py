#!/usr/bin/python2
"""Downloads data from the National Water Model via HydroShare.

The National Water Model is a series of model products from the National
Weather Service which compute streamflow for roughly 2.7 million river reaches
in the contiguous United States, where each river reach is a feature from the
National Hydrography Dataset and is identified by its unique COMID value.

The National Water Model includes an analysis and assimilation product that
represents the best estimate of current or historical streamflow conditions,
and three forecast products that cover short, medium, and long range forecasts.
Model results are available as a set of netCDF files, with a single file per
time step. For more on the model, see http://water.noaa.gov/about/nwm.

HydroShare is a National Science Foundation funded project which provides a
number of service to the hydrologic sciences community, including archiving
and providing access to National Water Model results. They include API for
accessing data and a couple of demonstration apps. The API is described at
https://apps.hydroshare.org/apps/nwm-data-explorer/api/.  HydroShare attempts
to add value to the model product by adding latitude and longitude coordinates
as variables within each model file. The doubles the file size, but enables the
file to be displayed in common netCDF viewing software. During this process,
the file is also converted from netCDF 3 format to netCDF 4 format.

In addition to documented API methods, the HydroShare API includes a couple of
hidden methods used by the demonstration apps. The apps include a time series
viewer and a file explorer, available at (respectively):
https://apps.hydroshare.org/apps/nwm-forecasts/
https://apps.hydroshare.org/apps/nwm-data-explorer/

This Python module includes functions for accessing data from the HydroShare
API into the National Water Model archive.
"""

from datetime import datetime, timedelta
import json
import os
import re
import urllib
from urllib2 import HTTPError

from dateutil import parser as date_parser
import pytz
from netCDF4 import Dataset
import numpy as np


def get_latest_analysis_filename():
    uri = ('https://apps.hydroshare.org/apps/nwm-data-explorer/api/'
           'GetFileList/?config=analysis_assim&geom=channel')
    response = urllib.urlopen(uri).read()
    files = json.loads(response)
    return files[-1]


def get_latest_analysis_file(output_folder):
    """Downloads latest analysis and assimilation file.

    Downloads latest analysis and assimilation file to the output folder and
    unzips it.

    Args:
        output_folder: Path to the folder where the file will be saved.

    Returns:
        Filename, including directory, of the downloaded file.
    """

    filename = get_latest_analysis_filename()
    uri = ('https://apps.hydroshare.org/apps/nwm-data-explorer/api/'
           'GetFile?file={0}').format(filename)
    output_filename = os.path.join(output_folder, filename)
    urllib.urlretrieve(uri, output_filename)
    return output_filename


def _get_date_from_analysis_filename(filename):
    start_index = filename.find('.') + 1
    return date_parser.parse(filename[start_index:start_index + 12])


def get_analysis_bounding_dates():
    """Returns dates of earliest and latest available analysis files."""

    uri = ('https://apps.hydroshare.org/apps/nwm-data-explorer/api/'
           'GetFileList/?config=analysis_assim&geom=channel')
    response = urllib.urlopen(uri).read()
    files = json.loads(response)
    start_date = _get_date_from_analysis_filename(files[0])
    end_date = _get_date_from_analysis_filename(files[-1])
    return start_date, end_date


def get_latest_forecast_date(product):
    """Returns latest forecast date for the given forecast product.

    HydroShare stores a rolling archive of forecasts due to size limitations,
    so the start date of available forecasts changes over time.  As forecasts
    arrive at HydroShare from NOAA, a folder for the forecast date is created
    although the forecast results may not have all arrived from NOAA.
    HydroShare cannot handle some queries when the forecast has not completely
    arrived yet. Therefore, we require that the last expected time step for the
    product is available in the folder before considering that forecast
    complete.

    Args:
        product: String indicating model product. Valid values are:
            short_range, medium_range, long_range

    Returns:
        Datetime object of latest forecast date, or None if no complete
        forecast is found.
    """

    valid_products = {'short_range': {'suffix_pattern': '',
                                      'max_time_step': '015'},
                      'medium_range': {'suffix_pattern': '',
                                       'max_time_step': '240'},
                      'long_range': {'suffix_pattern': '_[1-4]',
                                     'max_time_step': '720'}}
    if product not in valid_products:
        m = ('Product for getting latest forecast date must be one of the '
             'following: {0}'.format(', '.join(valid_products)))
        raise ValueError(m)
    suffix_pattern = valid_products[product]['suffix_pattern']
    max_time_step = valid_products[product]['max_time_step']

    # Get possible dates for which forecasts are available
    uri_template = ('https://apps.hydroshare.org/apps/nwm-data-explorer/'
                    'files_explorer/get-folder-contents/?selection_path=%2F'
                    'projects%2Fwater%2Fnwm%2Fdata%2F{0}%3Ffolder&query_type='
                    'filesystem')
    uri = uri_template.format(product)
    response = urllib.urlopen(uri).read()
    possible_dates = re.findall(r'\>([0-9]+)\<', response)

    # If last time step is available, consider the forecast complete
    pattern_template = (r'\>(nwm.t[0-9]+z.{product}.channel_rt{suffix}.'
                        'f{max_time_step}.conus.nc_georeferenced.nc)\<')
    pattern = pattern_template.format(
        product=product, suffix=suffix_pattern, max_time_step=max_time_step)

    for folder_date in reversed(possible_dates):
        uri = uri_template.format(product + '%2F' + folder_date)
        response = urllib.urlopen(uri).read()
        matches = re.findall(pattern, response)
        if product == 'long_range' and len(matches) == 16:
            return date_parser.parse(folder_date)
        elif product != 'long_range' and len(matches):
            return date_parser.parse(folder_date + 't' + matches[-1][5:7])


def _get_netcdf_data_response_to_json(uri, response):
    """Loads JSON from response to HydroShare get-netcdf-data request."""

    text = response.read()
    if 'Internal Server Error' in text:
        raise HTTPError(uri, 500, 'Internal Server Error', None, None)
    response_obj = json.loads(text)
    if 'error' in response_obj:
        parameter_error_message = '{0} -- Try adjusting input parameters'
        raise ValueError(parameter_error_message.format(response_obj['error']))

    data_text = response_obj['ts_pairs_data']
    data = json.loads(data_text)

    return data


def _unpack_series(json_data, product):
    """Returns a list of time series from HydroShare get-netcdf-data JSON."""

    if product == 'analysis_assim':
        time_step_hrs = 1
        offset_hrs = 3
    elif product == 'short_range':
        time_step_hrs = 1
        offset_hrs = 1
    elif product == 'medium_range':
        time_step_hrs = 3
        offset_hrs = 3
    elif product == 'long_range':
        time_step_hrs = 6
        offset_hrs = 6

    data_list = json_data.itervalues().next()
    series_list = []
    if product != 'long_range':
        data_list = [data_list]  # Match long range structure for simplicity
    for sim_result in data_list:
        if not len(sim_result[1]):
            raise ValueError('Empty result set. Try adjusting input '
                             'parameters')
        model_init_time = datetime.utcfromtimestamp(sim_result[0][0]).replace(
            tzinfo=pytz.utc)
        start_date = model_init_time + timedelta(hours=offset_hrs)
        value_count = len(sim_result[1])
        series_count = len(sim_result) - 2
        dates = [start_date + timedelta(hours=i*time_step_hrs)
                 for i in range(value_count)]

        label = sim_result[-1]

        for i, value_list in enumerate(sim_result[1:-1]):
            if series_count > 1:
                name = 'Member {0} {1}'.format(i + 1, label)
            else:
                name = product

            series_list.append({'name': name,
                                'dates': dates,
                                'values': value_list})
    return series_list


def get_streamflow(product, comid, sim_datetime_utc=None, timezone=None):
    """Downloads time seies from National Water Model for a given river.

    Downloads streamflow time series for a given river feature using the
    HydroShare archive and Web service. Units are in cubic feet per second as
    returned by HydroShare. For the API description, see
    https://apps.hydroshare.org/apps/nwm-data-explorer/api/

    Args:
        product: String indicating model product. Valid values are:
            analysis_assim, short_range, medium_range, long_range
        comid: National Hydrography Dataset identifier of the river feature.
        sim_datetime_utc: (Optional) Date and time when the model simulation
            was run. If None, then earliest available result datetime is used
            if product is analysis_assim, and most current complete forecast is
            used for all other products.
        timezone: (Optional) Text or timezone instance describing time zone if
            time series should be temporally shifted, e.g., 'America/Chicago'.
            Otherwise, UTC time as returned from HydroShare is used.

    Returns:
        A list of dicts representing time series. Each series includes name,
        datetimes, and values. For example:

        {'name': 'Member 1 t00z',
         'dates': ['2016-06-02 01:00:00+00:00', '2016-06-02 02:00:00+00:00']
         'values': [257.2516, 1295.7293]}

    Raises:
        HTTPError: An error occurred accessing data from the Web service.
        ValueError: Service request returned no data, likely due to invalid
            input arguments.

    Example:
        >>> series = nwm.get_streamflow(
                'short_range', 5671187, None, 'US/Central')
        >>> for s in series:
                dates = s['dates']
                for i, v in enumerate(s['values']):
                    print dates[i].strftime('%y-%m-%d %H'), '\t', v
        16-06-21 07     108.3435
        16-06-21 08 	108.1367
        16-06-21 09 	107.931
        16-06-21 10 	107.7264
        16-06-21 11 	107.5228
        16-06-21 12 	107.32
        16-06-21 13 	107.1176
        16-06-21 14 	106.9152
        16-06-21 15 	106.7157
        16-06-21 16 	106.6292
        16-06-21 17 	106.6784
        16-06-21 18 	106.5329
        16-06-21 19 	106.3177
        16-06-21 20 	106.0577
        16-06-21 21 	105.781
    """

    if sim_datetime_utc is None and product == 'analysis_assim':
        sim_datetime_utc = get_analysis_bounding_dates()[0]
    elif sim_datetime_utc is None:
        sim_datetime_utc = get_latest_forecast_date(product)
    elif isinstance(sim_datetime_utc, basestring):
        sim_datetime_utc = date_parser.parse(sim_datetime_utc)
    start_date = sim_datetime_utc.strftime('%Y-%m-%d')
    start_time = sim_datetime_utc.strftime('%H')
    end_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

    uri_template = (
        'https://apps.hydroshare.org/apps/nwm-forecasts/get-netcdf-data?'
        'config={0}&geom=channel_rt&variable=streamflow&comid={1}&'
        'startDate={2}&time={3}&lag=00z%2C06z%2C12z%2C18z&endDate={4}')
    uri = uri_template.format(product, comid, start_date, start_time, end_date)
    response = urllib.urlopen(uri)
    json_data = _get_netcdf_data_response_to_json(uri, response)
    series_list = _unpack_series(json_data, product)

    if timezone is not None:
        if isinstance(timezone, basestring):
            tz = pytz.timezone(timezone)
        else:
            tz = timezone
        for series in series_list:
            series['dates'] = [d.astimezone(tz) for d in series['dates']]

    return series_list


def read_q_for_comids(nc_filename, comids):
    """Reads streamflow for a set of COMID identifiers in a given file.

    Reads streamflow in cubic meters per second for each river represented by
    a set of National Hydrography Dataset COMID identifiers from a National
    Water Model simulation result file.

    Args:
        nc_filename: Filename of input netCDF file of model results.
        comids: List or numpy array of integers representing COMIDs for the
            rivers whose streamflow value is to be returned.

    Returns:
        A dictionary with a 'flows' array of streamflow values in cubic meters
        per second in the same order as the input COMIDs, along with 'datetime'
        providing the date associated with the streamflow values. For example:

        {'flows': [10.3, 283.2, 3.6],
         'datetime': datetime.datetime(2016, 6, 21, 15, 0, tzinfo=<UTC>)}

    Example:
        >>> filename = 'example_file.nc'
        >>> comids = [5671187, 5670795]
        >>> result = nwm.read_q_for_comids(filename, comids)
        >>> print('COMID {0}: {1} cms'.format(comids[0], result['flows'][0]))
        COMID 5671187: 3.16675 cms
    """

    result = {}
    qs = {}
    if type(comids) != 'numpy.ndarray':
        comids = np.array(comids)

    with Dataset(nc_filename, 'r') as nc:
        date = date_parser.parse(nc.model_output_valid_time.replace('_', ' '))
        date = date.replace(tzinfo=pytz.utc)
        result['datetime'] = date
        nc_comids = nc.variables['station_id'][:]
        nc_q = nc.variables['streamflow']
        sort_idx = nc_comids.argsort()
        indices = sort_idx[np.searchsorted(nc_comids[sort_idx], comids)]
        result['flows'] = nc_q[indices]
    return result


def subset_channel_file(in_nc_filename, out_nc_filename, comids,
                        just_flow_and_time=False):
    """Extracts a subset of data from an input channel file to a new file.

    A National Water Model channel file contains data related to river
    channels such as streamflow. This function makes a copy of that file but
    only includes data for river features included within a list of National
    Hydrography Dataset COMID identifiers.

    The input and output files are netCDF files.

    Args:
        in_nc_filename: Filename of input netCDF file of model results.
        out_nc_filename: Filename for the resulting subsetted file.
        comids: List or numpy array of integers representing COMIDs for the
            rivers to be included in the subsetted file.
        just_flow_and_time: (Optional) True if only streamflow and time
            variables should be included in the output. False if all variables
            should be included.
    """

    if type(comids) != 'numpy.ndarray':
        comids = np.array(comids)

    with Dataset(in_nc_filename, 'r') as in_nc:
        if just_flow_and_time:
            vars_to_include = ['streamflow', 'time']
        else:
            vars_to_include = in_nc.variables.keys()
        nc_comids = in_nc.variables['station_id'][:]
        orig_indices = nc_comids.argsort()
        index = orig_indices[np.searchsorted(nc_comids[orig_indices], comids)]
        with Dataset(out_nc_filename, 'w', format=in_nc.data_model) as out_nc:
            out_nc.setncatts({k: in_nc.getncattr(k) for k in in_nc.ncattrs()})

            for name, dim in in_nc.dimensions.iteritems():
                length = len(dim) if not dim.isunlimited() else None
                if name == 'station':
                    out_nc.createDimension(name, len(comids))
                else:
                    out_nc.createDimension(name, length)

            for name, var in in_nc.variables.iteritems():
                if name in vars_to_include:
                    out_var = out_nc.createVariable(
                        name, var.datatype, var.dimensions)
                    attributes = {k: var.getncattr(k) for k in var.ncattrs()}
                    out_var.setncatts(attributes)
                    if name == 'time':
                        out_var[:] = var[:]
                    else:
                        out_var[:] = var[index]
