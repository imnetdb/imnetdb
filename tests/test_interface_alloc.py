import pytest
from bracket_expansion import bracket_expansion


@pytest.fixture(scope='function')
def _setup_test(imnetdb):
    imnetdb.reset_database()

    device_name = 'spine1'
    device_node = imnetdb.devices.ensure(device_name)

    for if_name in bracket_expansion("Ethernet[1-48]"):
        imnetdb.interfaces.ensure(dict(device_node=device_node, name=if_name),
                                  speed=10, role='server')

    for if_name in bracket_expansion("Ethernet[49-56]"):
        imnetdb.interfaces.ensure(dict(device_node=device_node, name=if_name),
                                  speed=100, role='fabric')

    return device_name, imnetdb


def test_interface_alloc_pass(_setup_test):
    device_name, imnetdb = _setup_test

    if_node_list = imnetdb.interfaces.allocate(device_name, count=10, speed=10)
    assert len(if_node_list) == 10

    if_node_list = imnetdb.interfaces.allocate(device_name, count=8, speed=100)
    assert len(if_node_list) == 8


def test_interface_alloc_fail(_setup_test):
    device_name, imnetdb = _setup_test

    if_node_list = imnetdb.interfaces.allocate(device_name, count=49, speed=10)
    assert if_node_list is None

    if_node_list = imnetdb.interfaces.allocate(device_name, count=9, speed=100)
    assert if_node_list is None


def test_interface_alloc_pass_by_role(_setup_test):
    device_name, imnetdb = _setup_test

    if_node_list = imnetdb.interfaces.allocate(
        device_name, count=5, filters='interface.role == "server"')

    assert len(if_node_list) == 5

    if_node_list = imnetdb.interfaces.allocate(
        device_name, count=5, filters='interface.role == "shamu"'
    )

    assert if_node_list is None
