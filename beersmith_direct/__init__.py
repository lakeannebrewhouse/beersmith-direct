"""A set of functions to retrieve and save Beersmith data into MongoDB.
"""
from importlib.metadata import version

from beersmith_direct.i_beersmith import BeersmithInterface
from beersmith_direct.recipes import Recipes


__version__ = version(__package__)
