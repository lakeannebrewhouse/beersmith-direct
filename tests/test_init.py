"""Test functions for Squaredown import.
"""
import beersmith_direct

def test_version():
    """Tests that Squaredown was imported successfully.
    """
    assert beersmith_direct.__version__
