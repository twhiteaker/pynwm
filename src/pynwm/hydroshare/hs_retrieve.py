#!/usr/bin/python2
"""Retrieves National Water Model data from HydroShare."""

from datetime import datetime, timedelta
import json
import os
import re
from urllib import urlopen, urlretrieve
from urllib2 import HTTPError

from dateutil import parser as date_parser
import pytz

from hs_constants import HS_DATA_EXPLORER_URI, HS_API_URI
from hs_latest import find_latest_simulation
from pynwm.constants import PRODUCTSv1_1


def get_file(filename, output_folder):
    uri = HS_DATA_EXPLORER_URI + 'api/GetFile?file={0}'.format(filename)
    output_filename = os.path.join(output_folder, filename)
    urlretrieve(uri, output_filename)


def _get_netcdf_data_response_to_json(uri, response):
    """Loads JSON from response to get-netcdf-data request."""

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
    """Returns a list of time series from get-netcdf-data JSON."""

    key = 'long_range_mem1' if product == 'long_range' else product
    time_step_hrs = PRODUCTSv1_1[key]['step_hrs']
    offset_hrs = PRODUCTSv1_1[key]['offset_hrs']

    data_list = json_data.itervalues().next()
    series_list = []
    if product != 'long_range':
        data_list = [data_list]  # Match long range structure for simplicity
    for sim_result in data_list:
        if not len(sim_result[1]):
            m = 'Empty result set. Try adjusting input parameters'
            raise ValueError(m)
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


def _hours_to_lags(hour_list):
    hours = [h + 'z' for h in hour_list]
    return '%2C'.join(hours)


def _get_streamflow(product, feature_id, s_date, s_time, e_date, lag):
    """Downloads streamflow time series for a given river.

    Downloads streamflow time series for a given river feature using
    the HydroShare archive and Web service. Units are in cubic feet per
    second as returned by HydroShare. For the API description, see
    https://apps.hydroshare.org/apps/nwm-data-explorer/api/

    Args:
        product: String indicating model product. Valid values are:
            analysis_assim, short_range, medium_range, long_range
        feature_id: String identifier of the river feature.
        s_date: (String or Date) Valid date for the model simulation.
        s_time: (String) Two digit simulation hour, e.g., '06'.
        e_date: (String or Date) End date of data to retrieve. Valid
            for analysis_assim only.
        lag: (String) Lag argument for URI. This is an escaped comma
            delimited list of long_range forecast simulation hours,
            e.g., 00z%2C06z%2C12z%2C18z.

    Returns:
        A list of dicts representing time series. Each series includes
        name, datetimes, and values. For example:

        {'name': 'Member 1 t00z',
         'dates': ['2016-06-02 01:00:00+00:00', '2016-06-02 02:...']
         'values': [257.2516, 1295.7293]}

    Raises:
        HTTPError: An error occurred accessing data from HydroShare.
        ValueError: Service request returned no data, likely due to
            invalid input arguments.
    """

    if 'long_range' in product:
        product = 'long_range'
    s_date = date_parser.parse(str(s_date)).strftime('%Y-%m-%d')
    if e_date:
        e_date = date_parser.parse(str(e_date)).strftime('%Y-%m-%d')

    uri_template = (
        HS_API_URI + 'get-netcdf-data?config={0}&geom=channel_rt&'
        'variable=streamflow&COMID={1}&'
        'startDate={2}&time={3}&endDate={4}&lag={5}')
    uri = uri_template.format(product, feature_id, s_date, s_time, e_date, lag)
    response = urlopen(uri)
    json_data = _get_netcdf_data_response_to_json(uri, response)
    series_list = _unpack_series(json_data, product)
    return series_list


def _assert_forecast_product(product):
    valid_products = ['short_range', 'medium_range', 'long_range']
    if product not in valid_products:
        m = 'Invalid product: {0}. Valid products include {1}.'
        m = m.format(str(product), ', '.join(valid_products))
        raise ValueError(m)


def get_forecasted_streamflow(product, feature_id, sim_yyyymmdd, sim_hh):
    """Downloads forecasted streamflow time series for a given river.

    Args:
        product: String indicating model product. Valid values are:
            short_range, medium_range, long_range
        feature_id: String or Integer identifier of the river feature.
        sim_yyyymmdd: Model simulation date in yyyymmdd string format.
        sim_hh: (String) Two digit simulation hour, e.g., '06'.

    Returns:
        A list of dicts representing time series. Each series includes
        name, datetimes, and values. For example:

        {'name': 'Member 1 t00z',
         'dates': ['2016-06-02 01:00:00+00:00', '2016-06-02 02:...']
         'values': [257.2516, 1295.7293]}

    Example:
        >>> series = hs_retrieve.get_forecasted_streamflow(
                'short_range', 5671187, '20170420', '06')
        >>> for s in series:
                dates = s['dates']
                for i, v in enumerate(s['values']):
                    print dates[i].strftime('%y-%m-%d %H'), '\t', v
    """

    _assert_forecast_product(product)
    lag = _hours_to_lags([sim_hh])
    return _get_streamflow(product, feature_id, sim_yyyymmdd, sim_hh, '', lag)


def get_analysis_streamflow(feature_id, start_date, end_date):
    """Downloads analysis_assim streamflow time series for a river.

    Args:
        feature_id: String identifier of the river feature.
        start_date: (String or Date) Start date for time series data.
        end_date: (String or Date) End date for time series data.

    Returns:
        A list of dicts representing time series. Each series includes
        name, dates, and values.
    """

    return _get_streamflow('analysis_assim', feature_id, start_date, '',
                           end_date, '')


def get_latest_forecasted_streamflow(product, feature_id):
    """Gets the latest forecasted streamflow time series for a river.

    Args:
        product: String indicating model product. Valid values are:
            short_range, medium_range, long_range
        feature_id: String identifier of the river feature.

    Returns:
        A list of dicts representing time series. Each series includes
        name, dates, and values.
    """

    _assert_forecast_product(product)
    lag = _hours_to_lags(['00', '06', '12', '18'])
    sims = find_latest_simulation(product)
    key = sims.itervalues().next()
    sim_date = re.findall('\d{8}', key)[0]
    sim_hh = re.findall('t\d\d-', key)[0][1:3]
    return _get_streamflow(product, feature_id, sim_date, sim_hh, '', lag)
