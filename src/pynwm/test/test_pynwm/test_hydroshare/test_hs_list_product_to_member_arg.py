from dateutil import parser

from pynwm.hydroshare import hs_list


def test_without_member():
    '''Should return empty string.'''

    products = ['analysis_assim', 'short_range', 'medium_range', 'long_range']
    expected = ''
    for product in products:
        returned = hs_list._product_to_member_arg(product)
        assert expected == returned


def test_with_member():
    '''Should return member number as URL argument.'''

    product = 'long_range_mem2'
    expected = '&member=2'
    returned = hs_list._product_to_member_arg(product)
    assert expected == returned
