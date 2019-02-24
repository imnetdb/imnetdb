import pytest
from imnetdb.db import IMNetDB


@pytest.fixture(scope='session')
def imnetdb():
    return IMNetDB('admin123')
