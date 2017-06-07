from pynwm import filenames


def test_hour_from_filename():
    '''Should find 't##z' where ## is two-digit model simulation hour.'''

    files = ['nwm.t00z.short_range.channel_rt.f008.conus.nc',
             'nwm.t00z.analysis_assim.channel_rt.tm01.conus.nc',
             'nwm.t00z.long_range.channel_rt_1.f006.conus.nc']
    expected = 't00z'
    for filename in files:
        hour = filenames.hour_from_filename(filename)
        assert expected == hour
