import pytest
from imnetdb.db import IMNetDB


@pytest.fixture(scope='module')
def imnetdb():
    client = IMNetDB('admin123')
    client.reset_database()
    return client

