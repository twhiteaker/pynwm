from pynwm import filenames


def test_sim_is_complete():
    '''Should return True if count of files in sim matches expected count by
       version.
    '''

    expected = True
    sim = {'product': 'short_range',
           'date': '20170601t06-00',
           'files': ['filename_placeholder']*18}
    is_complete = filenames.is_sim_complete(sim)
    assert expected == is_complete

    sim['date'] = '20170401t06-00'
    sim['files'] = ['filename_placeholder']*15
    is_complete = filenames.is_sim_complete(sim)
    assert expected == is_complete


def test_sim_is_not_complete():
    '''Should return False if count of files in sim does not match expected
       count by version.
    '''

    expected = False
    sim = {'product': 'short_range',
           'date': '20170601t06-00',
           'files': ['filename_placeholder']*15}
    is_complete = filenames.is_sim_complete(sim)
    assert expected == is_complete

    sim['date'] = '20170401t06-00'
    sim['files'] = ['filename_placeholder']*20
    is_complete = filenames.is_sim_complete(sim)
    assert expected == is_complete
