import pytest
from imnetdb.nsotdb import IMNetDB


@pytest.fixture(scope='session')
def imnetdb():
    return IMNetDB('admin123')
