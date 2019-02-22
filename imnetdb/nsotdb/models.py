nodes_types = [
    'Cable',
    'Device', 'DeviceGroup',
    'Interface',
    'IPAddress', 'IPNetwork', 'IPInterface',
    'LAG',
    'VLAN', 'VLANGroup'
]

rel_types = [
    ('Device',      'device_member',        'DeviceGroup'),
    ('Device',      'equip_interface',      'Interface'),
    ('Interface',   'lag_member',           'LAG'),
    ('Interface',   'cabled',               'Cable'),
    ('VLAN',        "vlan_member",          'VLANGroup')
]

