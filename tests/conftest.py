import pytest
from imnetdb.gdb import IMNetDB


@pytest.fixture(scope='session')
def imnetdb():
    return IMNetDB('admin123')
