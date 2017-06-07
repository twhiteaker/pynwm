import pytest

from pynwm import nwm_data

_all_ids = [10, 20, 30, 40, 50]


def test_one_id():
    one_id = [20]
    expected = [1]
    returned = list(nwm_data.get_id_indices(one_id, _all_ids))
    assert expected == returned


def test_string_id():
    string_id = ['20']
    expected = [1]
    returned = list(nwm_data.get_id_indices(string_id, _all_ids))
    assert expected == returned


def test_multiple_ids():
    two_ids = [40, 30]
    expected = [3, 2]
    returned = list(nwm_data.get_id_indices(two_ids, _all_ids))
    assert expected == returned


def test_invalid_ids():
    no_id = [100]
    with pytest.raises(IndexError):
        returned = list(nwm_data.get_id_indices(no_id, _all_ids))
