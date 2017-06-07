from dateutil import parser

from pynwm.hydroshare import hs_list


def test_without_member():
    '''Should return date string in yyyymmdd format.'''

    files = ['analysis_assim-nwm.20170603.t21z.analysis_assim.channel_rt.tm00.conus.nc',
             u'analysis_assim-nwm.20170603.t21z.analysis_assim.channel_rt.tm00.conus.nc',
             'short_range-20170603-nwm.t01z.short_range.channel_rt.f007.conus.nc',
             'medium_range-20170603-nwm.t06z.medium_range.channel_rt.f207.conus.nc',
             'long_range-20170603-nwm.t18z.long_range.channel_rt_1.f294.conus.nc']
    expected = '20170603'
    for filename in files:
        returned = hs_list._date_from_filename(filename)
        assert expected == returned
