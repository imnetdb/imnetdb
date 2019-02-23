from bracket_expansion import bracket_expansion


def create_device(imnetdb, device_name, if_name_expr):
    dev_node = imnetdb.devices.ensure(device_name)

    if_nodes = [
        imnetdb.interfaces.ensure(dict(device_node=dev_node, name=if_name), speed=10)
        for if_name in bracket_expansion(if_name_expr)
    ]

    lag_node = imnetdb.lags.ensure(dict(device=dev_node['name'], name='ae0'))

    for if_node in if_nodes[0:2]:
        imnetdb.lags.add_interface(lag_node, if_node)

    lag_node = imnetdb.lags.ensure(dict(device=dev_node['name'], name='ae1'))

    for if_node in if_nodes[2:4]:
        imnetdb.lags.add_interface(lag_node, if_node)

    return dev_node, lag_node, if_nodes


def test_lag_basic(imnetdb):
    imnetdb.reset_database()

    dev_node, lag_node, if_nodes = create_device(imnetdb, 'spine1', "Ethernet[1-10]")

    # read back the LAGS for this device.

    lag_dataset = imnetdb.lags.device_catalog(dev_node['name'])
    assert list(lag_dataset) == ['ae0', 'ae1']


def test_lag_more_device(imnetdb):
    create_device(imnetdb, 'leaf1', 'Ethernet[20-30]')
    create_device(imnetdb, 'leaf2', 'Ethernet[30-40]')
    create_device(imnetdb, 'leaf3', 'Ethernet[40-50]')
