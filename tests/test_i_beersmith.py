"""Tests initializing Beersmith interface.
"""
from beersmith_direct import BeersmithInterface


def test_init_beersmith():
    """Test initializing Beersmith interface.
    """
    bsm = BeersmithInterface()

    assert bsm
