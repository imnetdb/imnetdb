
def test_clean(imnetdb):
    imnetdb.wipe_database()
    imnetdb.ensure_database()
