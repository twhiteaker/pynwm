import collections

from pynwm import filenames


_assim_files = ['nwm.t00z.analysis_assim.channel_rt.tm0{0}.conus.nc'.format(i)
                for i in range(3)]


def test_multiple_groups():
    '''Files should be grouped by simulation.'''

    assim_complete = ['nwm.t00z.analysis_assim.channel_rt.tm00.conus.nc',
                      'nwm.t00z.analysis_assim.channel_rt.tm01.conus.nc',
                      'nwm.t00z.analysis_assim.channel_rt.tm02.conus.nc']
    assim_incomplete = ['nwm.t01z.analysis_assim.channel_rt.tm00.conus.nc',
                        'nwm.t01z.analysis_assim.channel_rt.tm01.conus.nc']
    files =  assim_complete + assim_incomplete
    sims = filenames.group_simulations(files, '20170601')

    expected = 2
    assert expected == len(sims)

    complete_sim = sims['analysis_assim_20170601t00-00']
    expected = len(assim_complete)
    assert expected == len(complete_sim['files'])
    expected = True
    assert expected == complete_sim['is_complete']
    expected = '20170601t00-00'
    assert expected == complete_sim['date']
    for filename in complete_sim['files']:
        assert filename in assim_complete

    incomplete_sim = sims['analysis_assim_20170601t01-00']
    expected = len(assim_incomplete)
    assert expected == len(incomplete_sim['files'])
    expected = False
    assert expected == incomplete_sim['is_complete']
    expected = '20170601t01-00'
    assert expected == incomplete_sim['date']
    for filename in incomplete_sim['files']:
        assert filename in assim_incomplete


def test_group_return_types():
    '''Type should be OrderedDict of dictionaries like:
    {'product': 'long_range_mem1',
     'date': '20170401t06-00',
     'is_complete': True,
     'files': ['nwm...f006.conus.nc', 'nwm...f012.conus.nc', ...]
     'links': ['http...', ...]}
    '''

    files = ['nwm.t00z.short_range.channel_rt.f001.conus.nc',
             'nwm.t00z.short_range.channel_rt.f003.conus.nc',
             'nwm.t00z.short_range.channel_rt.f002.conus.nc']
    sims = filenames.group_simulations(files, '20170601')

    assert collections.OrderedDict == type(sims)
    key, sim = sims.items()[0]
    assert str == type(key)
    assert dict == type(sim)
    expected = ['date', 'files', 'is_complete', 'links', 'product']
    assert expected == sorted(list(sim.keys()))
    assert str == type(sim['product'])
    assert str == type(sim['date'])
    assert bool == type(sim['is_complete'])
    assert list == type(sim['files'])
    assert list == type(sim['links'])


def test_links_included():
    '''If provided, links should be kept in same order as files.'''

    files = ['nwm.t00z.short_range.channel_rt.f001.conus.nc',
             'nwm.t00z.short_range.channel_rt.f003.conus.nc',
             'nwm.t00z.short_range.channel_rt.f002.conus.nc']
    links = ['1', '3', '2']
    file_link_lookup = {}
    for i, filename in enumerate(files):
        file_link_lookup[filename] = links[i]

    sims = filenames.group_simulations(files, '20170601', links)
    key, sim = sims.items()[0]
    returned_links = sim['links']
    assert len(sim['files']) == len(returned_links)
    for i, filename in enumerate(sim['files']):
        expected = file_link_lookup[filename]
        assert expected == returned_links[i]
