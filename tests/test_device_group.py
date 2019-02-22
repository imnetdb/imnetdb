def test_device_group(imnetdb):

    group_dataset = {
        'leafgroup-01': dict(role='leaf'),
        'leafgroup-02': dict(role='leaf'),
        'leafgroup-03': dict(role='leaf'),
        'spinegroup-01': dict(role='spine'),
        'spinegroup-02': dict(role='spine'),
    }

    for group_name, fields in group_dataset.items():
        group_dataset[group_name]['node'] = imnetdb.device_groups.ensure(group_name, **fields)

    devices = {
        'leaf01-1': dict(role='leaf', group='leafgroup-01'),
        'leaf01-2': dict(role='leaf', group='leafgroup-01'),

        'leaf02-1': dict(role='leaf', group='leafgroup-02'),
        'leaf02-2': dict(role='leaf', group='leafgroup-02'),

        'leaf03-1': dict(role='leaf', group='leafgroup-03'),
        'leaf03-2': dict(role='leaf', group='leafgroup-03'),

        'spine01-1': dict(role='spine', group='spinegroup-01'),
        'spine01-2': dict(role='spine', group='spinegroup-01'),

        'spine02-1': dict(role='spine', group='spinegroup-02'),
        'spine02-2': dict(role='spine', group='spinegroup-02')
    }

    for device_name, device_info in devices.items():
        group_name = device_info.pop('group')
        group_node = group_dataset[group_name]['node']
        device_node = imnetdb.devices.ensure(device_name, **device_info)
        devices[device_name]['node'] = device_node
        imnetdb.device_groups.add_device(group_node, device_node)
