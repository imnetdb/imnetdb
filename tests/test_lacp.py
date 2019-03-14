from collections import namedtuple, defaultdict
from bracket_expansion import bracket_expansion


DeviceData = namedtuple("DeviceData", ["device", "lags", "interfaces"])


def create_device(imnetdb, device_name, if_name_expr):
    dev_node = imnetdb.devices.ensure(device_name)

    if_nodes = [
        imnetdb.interfaces.ensure((dev_node, if_name), speed=10)
        for if_name in bracket_expansion(if_name_expr)
    ]

    lags = dict()

    # lag0 will be the first two ports

    lag_node = imnetdb.lags.ensure((dev_node, 'lag0'))
    lags['lag0'] = lag_node

    for if_node in if_nodes[0:2]:
        imnetdb.lags.add_member(lag_node, if_node)

    # lag1 will be the 2nd two ports

    lag_node = imnetdb.lags.ensure((dev_node, 'lag1'))
    lags['lag1'] = lag_node

    for if_node in if_nodes[2:4]:
        imnetdb.lags.add_member(lag_node, if_node)

    return DeviceData(dev_node, lags, if_nodes)


def test_lacp_basic(imnetdb):
    spine1 = create_device(imnetdb, 'spine1', 'Ethernet[40-50]')
    leaf1 = create_device(imnetdb, 'leaf1', 'Ethernet[20-30]')
    leaf2 = create_device(imnetdb, 'leaf2', 'Ethernet[30-40]')

    lacp0 = imnetdb.lacp.ensure(peer_nodes=[spine1.lags['lag0'], leaf1.lags['lag0']], role='foo')
    lacp1 = imnetdb.lacp.ensure(peer_nodes=[spine1.lags['lag1'], leaf2.lags['lag0']], role='baz')

    # ensure there are two LACP nodes

    assert imnetdb.lacp.col.count() == 2

    # ensure that the LACP nodes are properly formed

    peering_info = imnetdb.lacp.get_peering()
    assert len(peering_info) == 2

    # now check that each LACP connects to LAGs are correctly retrieved from the database

    lacp_by_id = {lacp['peering_node']['_id']: lacp for lacp in peering_info}

    found_lacp0 = lacp_by_id[lacp0['_id']]
    found_lacp1 = lacp_by_id[lacp1['_id']]

    found_lacp0_peers = {(peer['device'], peer['name']) for peer in found_lacp0['peer_nodes']}
    found_lacp1_peers = {(peer['device'], peer['name']) for peer in found_lacp1['peer_nodes']}

    assert found_lacp0_peers == {("spine1", "lag0"), ("leaf1", "lag0")}
    assert found_lacp1_peers == {("spine1", "lag1"), ("leaf2", "lag0")}
