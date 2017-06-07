import os
import tempfile

from pynwm import nwm_subset


def test_get_files_exist():
    template = os.path.join(tempfile.gettempdir(), 'test_get_files_exist{0}')
    filenames = [template.format(i) for i in range(5)]
    files_to_create = filenames[::2]
    for filename in files_to_create:
        with open(filename, 'wb') as f:
            f.close()
    returned = nwm_subset.get_files_exist(filenames)
    expected = files_to_create
    assert expected == returned
