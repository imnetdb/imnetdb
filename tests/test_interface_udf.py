import pytest
from bracket_expansion import bracket_expansion


@pytest.fixture(scope='function')
def _setup_test(imnetdb):
    imnetdb.reset_database()

    device_name = 'spine1'
    device_node = imnetdb.devices.ensure(device_name)

    for if_name in bracket_expansion("Ethernet[1-12]"):
        imnetdb.interfaces.ensure((device_node, if_name),
                                  speed=10, role='server', slot=1)

    for if_name in bracket_expansion("Ethernet[13-24]"):
        imnetdb.interfaces.ensure((device_node, if_name),
                                  speed=10, role='server', slot=2)

    for if_name in bracket_expansion("Ethernet[25-48]"):
        imnetdb.interfaces.ensure((device_node, if_name),
                                  speed=25, role='server', slot=3)

    for if_name in bracket_expansion("Ethernet[49-56]"):
        imnetdb.interfaces.ensure((device_node, if_name), speed=100, role='fabric')

    return device_name, imnetdb


def test_interface_alloc_pass_by_slot(_setup_test):
    device_name, imnetdb = _setup_test

    # allocate 12 ports from slot 2, we should get 12 back.

    if_node_list = imnetdb.interfaces.allocate(
        device_name, count=12, filters='interface.role == "server" and interface.slot == 2')

    assert len(if_node_list) == 12

    # allocate 12 ports from slot 2, there should be none left.

    if_node_list = imnetdb.interfaces.allocate(
        device_name, count=12, filters='interface.role == "server" and interface.slot == 2')

    assert if_node_list is None

    # allocate 12 ports from slot 3, we should get 12 back.

    if_node_list = imnetdb.interfaces.allocate(
        device_name, count=12, filters='interface.role == "server" and interface.slot == 3')

    assert len(if_node_list) == 12
