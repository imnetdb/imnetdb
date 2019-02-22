from collections import defaultdict


def test_cabling(imnetdb):
    nodes = defaultdict(dict)

    imnetdb.wipe_database()
    imnetdb.ensure_database()

    nodes['device']['spine1'] = imnetdb.devices.ensure('spine1', role='spine')
    nodes['device']['leaf1'] = imnetdb.devices.ensure('leaf1', role='leaf')

    if_0 = imnetdb.interfaces.ensure(dict(device='spine1', name='eth0'))
    imnetdb.interfaces.ensure(dict(device='spine1', name='eth1'))
    imnetdb.interfaces.ensure(dict(device='spine1', name='eth2'))

    imnetdb.interfaces.ensure(dict(device='leaf1', name='eth0'))
    if_1 = imnetdb.interfaces.ensure(dict(device='leaf1', name='eth1'))
    imnetdb.interfaces.ensure(dict(device='leaf1', name='eth2'))

    cable_node1 = imnetdb.cabling.ensure(interface_nodes=[if_0, if_1],
                                         role='leaf-spine', mode='fiber')

    cable_node2 = imnetdb.cabling.ensure(interface_nodes=[if_0, if_1])

    assert cable_node1 == cable_node2


def test_cabling_one_side(imnetdb):
    if_0 = imnetdb.interfaces[dict(device='spine1', name='eth0')]
    if_1 = imnetdb.interfaces[dict(device='leaf1', name='eth1')]

    found_0 = imnetdb.cabling.find(interface_nodes=[if_0])
    found_1 = imnetdb.cabling.find(interface_nodes=[if_1])

    assert found_0 == found_1


def test_cabling_remove(imnetdb):
    if_0 = imnetdb.interfaces[dict(device='spine1', name='eth0')]

    found_0 = imnetdb.cabling.find(interface_nodes=[if_0])
    cable_node = found_0['cable_node']
    imnetdb.cabling.remove(cable_node)

    found_1 = imnetdb.cabling.find(interface_nodes=[if_0])
    assert found_1 is None
