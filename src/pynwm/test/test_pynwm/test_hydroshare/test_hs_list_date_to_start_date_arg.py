from dateutil import parser

from pynwm.hydroshare import hs_list


def test_no_date():
    '''Should return empty string.'''

    no_dates = [None, '']
    expected = ''
    for date in no_dates:
        returned = hs_list._date_to_start_date_arg(date)
        assert expected == returned


def test_date_obj():
    '''Should return startDate string URL argument.'''

    date = parser.parse('2017-06-01')
    returned = hs_list._date_to_start_date_arg(date)
    expected = '&startDate=2017-06-01'
    assert expected == returned


def test_date_str():
    '''Should return startDate string URL argument.'''

    dates = ['2017-06-01', '6/1/2017', '6-1-2017', '2017-6-1']
    expected = '&startDate=2017-06-01'
    for date in dates:
        returned = hs_list._date_to_start_date_arg(date)
        assert expected == returned

