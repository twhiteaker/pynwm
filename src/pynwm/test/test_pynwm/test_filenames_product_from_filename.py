from pynwm import filenames


def test_short_range_from_filename():
    '''Should find 'short_range' between 'z.' and '.channel'.'''

    filename = 'nwm.t00z.short_range.channel_rt.f008.conus.nc'
    expected = 'short_range'
    product = filenames.product_from_filename(filename)
    assert expected == product


def test_analysis_assim_from_filename():
    '''Should find 'analysis_assim' between 'z.' and '.channel'.'''

    filename = 'nwm.t00z.analysis_assim.channel_rt.tm01.conus.nc'
    expected = 'analysis_assim'
    product = filenames.product_from_filename(filename)
    assert expected == product


def test_long_range_from_filename():
    '''Should find 'long_range' and append '_mem' and the member number.'''

    filename = 'nwm.t00z.long_range.channel_rt_1.f006.conus.nc'
    expected = 'long_range_mem1'
    product = filenames.product_from_filename(filename)
    assert expected == product


def test_medium_range_from_filename():
    '''Should find 'medium_range'.'''

    filename = 'nwm.t00z.medium_range.channel_rt.f021.conus.nc'
    expected = 'medium_range'
    product = filenames.product_from_filename(filename)
    assert expected == product


def test_medium_range_member_from_filename():
    '''Should find 'medium_range' and append '_mem' and the member number.'''

    filename = 'nwm.t00z.medium_range.channel_rt_1.f003.conus.nc'
    expected = 'medium_range_mem1'
    product = filenames.product_from_filename(filename)
    assert expected == product
