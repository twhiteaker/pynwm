from dateutil import parser

from pynwm import nwm_subset


def test_dates_to_naive_utc():
    '''Should return dates in UTC time zone with tzinfo removed.'''

    in_dates = [parser.parse('2017-04-29 04:00:00-00'),
                parser.parse('2017-05-29 00:00:00-04'),
                parser.parse('2017-06-29 04:00:00')]
    expected = [parser.parse('2017-04-29 04:00:00'),
                parser.parse('2017-05-29 04:00:00'),
                parser.parse('2017-06-29 04:00:00')]
    returned = nwm_subset._dates_to_naive_utc(in_dates)
    assert expected == returned
