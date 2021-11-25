"""Class module that connects to both Beersmith and MongoDB.
"""
from datetime import datetime
import os

from aracnid_config import Config
from aracnid_logger import Logger
from aracnid_utils import timespan as ts
from i_mongodb import MongoDBInterface

from beersmith_direct.i_beersmith import BeersmithInterface

# initialize logging
logger = Logger(__name__).get_logger()

logger.debug('module installed')


class Connector(MongoDBInterface):
    """Provides interfaces to Beersmith and MongoDB to enable data exchange.

    This class can be used on its own or inherited, but it is more useful to
    create subclasses that inherit from the Connector class for specific data
    type. The attributes and instance methods help with this.

    Environment Variables:
        TBD

    Attributes:
        config_name: Name of the configuration object in MongoDB.
        props: Configuration Properties object.
    """

    def __init__(self, config_name=None):
        """Initializes the interfaces and instance attributes.
        """
        self.bsm = BeersmithInterface()
        self.mdbi = MongoDBInterface.__init__(self)

        self.config_name = config_name
        if config_name:
            logger.debug(f'config_name: {self.config_name}')
            self.props = Config(self.config_name, mdb=self.mdbi)

        self.set_start_min()

    def set_start_min(self):
        """Sets an attribute for the minimum start time.

        The minimum start time is determined by the environment.

        Args:
            None
        """
        start_str = os.environ.get('BEERSMITH_START_STR')
        self.start_min = datetime.fromisoformat(start_str).astimezone()

    def timespan(self, **kwargs):
        """Calculates the endpoints of a timespan.

        This instance method supplies the generic timespan function with more
        specific start times based on the last updated order or a preset
        minimum start time.

        Args:
            kwargs: Keyword arguments that specify the timespan.

        Returns:
            The start and end datetime objects that define the timespan.
        """
        begin = kwargs.get('begin')
        begin_str = kwargs.get('begin_str')
        week_str = kwargs.get('week_str')
        if not begin and not begin_str and not week_str:
            kwargs['begin'] = self.datetime_begin()

        return ts(**kwargs)

    def datetime_begin(self):
        """Provides the start time based on the last updated order.

        If no orders have been saved, this instance method defaults to the
        minimum start time preset from the environment.

        Returns:
            Datetime object that represents the start time of the timespan.
        """
        last_updated = self.props.last_updated

        if last_updated:
            return last_updated

        return self.start_min
