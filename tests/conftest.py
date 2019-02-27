import pytest

from imnetdb.db import IMNetDB
from imnetdb.rpools import RPoolsDB


@pytest.fixture(scope='module')
def imnetdb():
    client = IMNetDB('admin123')
    client.reset_database()
    return client


@pytest.fixture(scope='module')
def rpoolsdb():
    client = RPoolsDB('admin123')
    client.reset_database()
    return client
