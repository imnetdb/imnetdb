
def test_clean(gdb_client):
    gdb_client.wipe_database()
    gdb_client.ensure_database()
