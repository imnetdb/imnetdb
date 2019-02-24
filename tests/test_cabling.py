

def test_cabling_pass(imnetdb):

    imnetdb.reset_database()

    spine1 = imnetdb.devices.ensure('spine1', role='spine')
    if_0 = imnetdb.interfaces.ensure((spine1, 'eth0'))
    imnetdb.interfaces.ensure((spine1, 'eth1'))
    imnetdb.interfaces.ensure((spine1, 'eth2'))

    leaf1 = imnetdb.devices.ensure('leaf1', role='leaf')

    imnetdb.interfaces.ensure((leaf1, 'eth0'))
    if_1 = imnetdb.interfaces.ensure((leaf1, 'eth1'))
    imnetdb.interfaces.ensure((leaf1, 'eth2'))

    cable_node1 = imnetdb.cabling.ensure(interface_nodes=[if_0, if_1],
                                         role='leaf-spine', mode='fiber')

    cable_node2 = imnetdb.cabling.ensure(interface_nodes=[if_0, if_1])

    assert cable_node1 == cable_node2


def test_cabling_one_side(imnetdb):
    spine1 = imnetdb.devices['spine1']
    leaf1 = imnetdb.devices['leaf1']

    if_0 = imnetdb.interfaces[(spine1, 'eth0')]
    if_1 = imnetdb.interfaces[(leaf1, 'eth1')]

    found_0 = imnetdb.cabling.find(interface_nodes=[if_0])
    found_1 = imnetdb.cabling.find(interface_nodes=[if_1])

    assert found_0 == found_1


def test_cabling_remove(imnetdb):
    spine1 = imnetdb.devices['spine1']
    if_0 = imnetdb.interfaces[(spine1, 'eth0')]

    found_0 = imnetdb.cabling.find(interface_nodes=[if_0])
    cable_node = found_0['cable_node']
    imnetdb.cabling.remove(cable_node)

    found_1 = imnetdb.cabling.find(interface_nodes=[if_0])
    assert found_1 is None
