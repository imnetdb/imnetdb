from collections import defaultdict

def test_cabling(gdb_client):
    nodes = defaultdict(dict)

    nodes['device']['spine1'] = gdb_client.devices.ensure('spine1', role='spine')
    nodes['device']['leaf1'] = gdb_client.devices.ensure('leaf1', role='leaf')

    gdb_client.interfaces.ensure(dict(device='spine1', name='eth0'))
    gdb_client.interfaces.ensure(dict(device='spine1', name='eth2'))
    gdb_client.interfaces.ensure(dict(device='spine1', name='eth3'))

    gdb_client.interfaces.ensure(dict(device='leaf1', name='eth0'))
    gdb_client.interfaces.ensure(dict(device='leaf1', name='eth2'))
    gdb_client.interfaces.ensure(dict(device='leaf1', name='eth3'))

