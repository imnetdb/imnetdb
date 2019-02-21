def test_device_group(gdb_client):

    gdb_client.device_groups.ensure('leafgroup-01', role='leaf')
    gdb_client.device_groups.ensure('leafgroup-02', role='leaf')
    gdb_client.device_groups.ensure('leafgroup-03', role='leaf')
    gdb_client.device_groups.ensure('spinegroup-01', role='spine')
    gdb_client.device_groups.ensure('spinegroup-02', role='spine')

