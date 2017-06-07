from datetime import timedelta
import json

from dateutil import parser

from pynwm.hydroshare import hs_retrieve


_seed_date = parser.parse('2016-06-21 17:00-00')
_long_rng_seed_dates = [parser.parse('2016-06-21 17:00-00'),
                        parser.parse('2017-06-07 06:00-00')]
_json_str = '{"5671187": [[1466528400], [7.1, 6.9], "notLong"]}'
_long_rng_json_str = ('{"5671187": [[[1466528400], [7.1, 6.9], "t06z"],'
                      '[[1496815200], [1.1, 2.9], "t12z"]]}')


def call_unpack(json_str, product):
    json_data = json.loads(json_str)
    return hs_retrieve._unpack_series(json_data, product)


def test_dates_analysis_assim():
    '''Should convert integer time stamp into time zone aware date object.'''

    returned = call_unpack(_json_str, 'analysis_assim')
    expected = [_seed_date + timedelta(hours=(3 + i)) for i in range(2)]
    for series in returned:
        assert expected == series['dates']


def test_dates_short_range():
    '''Should convert integer time stamp into time zone aware date object.'''

    returned = call_unpack(_json_str, 'short_range')
    expected = [_seed_date + timedelta(hours=(1 + i)) for i in range(2)]
    for series in returned:
        assert expected == series['dates']


def test_dates_medium_range():
    '''Should convert integer time stamp into time zone aware date object.'''

    returned = call_unpack(_json_str, 'medium_range')
    expected = [_seed_date + timedelta(hours=(3 + i * 3)) for i in range(2)]
    for series in returned:
        assert expected == series['dates']


def test_dates_long_range():
    '''Should convert integer time stamp into time zone aware date object.'''

    returned = call_unpack(_long_rng_json_str, 'long_range')
    for i, series in enumerate(returned):
        seed_date = _long_rng_seed_dates[i]
        expected = [seed_date + timedelta(hours=(6 + i * 6)) for i in range(2)]
        assert expected == series['dates']


def test_vals_long_range():
    returned = call_unpack(_long_rng_json_str, 'long_range')
    vals = [[7.1, 6.9], [1.1, 2.9]]
    for i, series in enumerate(returned):        
        expected = vals[i]
        assert expected == series['values']


def test_vals_not_long_range():
    returned = call_unpack(_json_str, 'short_range')
    expected = 1
    assert expected == len(returned)
    expected = [7.1, 6.9]
    assert expected == returned[0]['values']
