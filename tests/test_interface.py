import pytest
from bracket_expansion import bracket_expansion


@pytest.fixture(scope='function')
def _setup_test(imnetdb):
    imnetdb.reset_database()

    device_name = 'spine1'
    device_node = imnetdb.devices.ensure(device_name)

    for if_name in bracket_expansion("Ethernet[1-48]"):
        imnetdb.interfaces.ensure((device_node, if_name), speed=10, role='server')

    for if_name in bracket_expansion("Ethernet[49-56]"):
        imnetdb.interfaces.ensure((device_node, if_name), speed=100, role='fabric')

    return device_name, imnetdb


def test_interface_alloc_pass(_setup_test):
    device_name, imnetdb = _setup_test

    if_node_list = imnetdb.interfaces.pool.take_batch(
        match={'device': device_name, 'speed': 10},
        count=10)

    assert len(if_node_list) == 10

    if_node_list = imnetdb.interfaces.pool.take_batch(
        match={'device': device_name, 'speed': 100},
        count=8)

    assert len(if_node_list) == 8


def test_interface_alloc_fail(_setup_test):
    device_name, imnetdb = _setup_test

    # take batch will take only as many as it can, returning the
    # items taken.  we know there are 48x10g ports.  try to take 49.

    if_node_list = imnetdb.interfaces.pool.take_batch(
        match=dict(device=device_name, speed=10),
        count=49)

    assert len(if_node_list) == 48

    # we know there are only 8x100g ports.  try to take 9

    if_node_list = imnetdb.interfaces.pool.take_batch(
        match=dict(device=device_name, speed=100),
        count=9)

    assert len(if_node_list) == 8


def test_interface_alloc_pass_by_role(_setup_test):
    device_name, imnetdb = _setup_test

    if_node_list = imnetdb.interfaces.pool.take_batch(
        match=dict(device=device_name, role='server'),
        count=5)

    assert len(if_node_list) == 5

    # there are no "shamu" ports, so we should get back and empty list

    if_node_list = imnetdb.interfaces.pool.take_batch(
        match=dict(device=device_name, role='shamu'),
        count=5)

    assert len(if_node_list) == 0

