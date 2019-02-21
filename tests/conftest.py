import pytest
from imnetdb.gdb import GDBClient


@pytest.fixture(scope='session')
def gdb_client():
    return GDBClient('admin123')
