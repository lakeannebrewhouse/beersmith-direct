"""Tests connector functionality.
"""
import os

import pytest
from i_mongodb import MongoDBDatabase

from beersmith_direct.connector import Connector


def test_init_connector():
    """Tests initializing connector.
    """
    connector = Connector(config_name='beersmith')

    assert connector
    assert isinstance(connector, Connector)

@pytest.fixture(name='conn')
def fixture_connector():
    """Pytest fixture to initialize and return a Connector.
    """
    connector = Connector(config_name='beersmith')

    return connector

def test_init_connector_beersmith(conn):
    """Tests the Connector's BeerSmith initialization.
    """
    # test initialization
    beersmith_path = os.environ.get('BEERSMITH_DEFAULT_PATH')
    assert conn.bsm.default_path == beersmith_path

def test_init_connector_mongodb(conn):
    """Tests the Connector's MongoDB initialization.
    """
    # test authentication
    mdb = conn.mdb
    assert mdb
    assert isinstance(mdb, MongoDBDatabase)

    # verify database name
    db_name = os.environ.get('MONGODB_DBNAME')
    assert mdb.name == db_name
