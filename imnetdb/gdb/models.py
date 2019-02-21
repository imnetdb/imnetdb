nodes_types = [
    'Device',
    'DeviceGroup',
    'Interface',
    'LAG'
]

rel_types = [
    ('Device', 'group_member', 'DeviceGroup'),
    ('Device', 'equip_iface', 'Interface'),
    ('Interface', 'lag_member', "LAG"),
    ('Interface', 'connected', 'Cable')
]

