"""Recipes classes.
"""
import os.path

from dataclasses import dataclass
from datetime import datetime

from aracnid_logger import Logger
from dateutil.parser import parse
from pymongo.collection import ReturnDocument

from beersmith_direct.connector import Connector

# initialize logging
logger = Logger(__name__).get_logger()


class Recipes(Connector):
    """Contains the code to connect and process recipes from Beersmith.
    """
    def __init__(self) -> None:
        """Initializes the Recipes Connector.

        Establishes connections to Beersmith and MongoDB.
        Sets up access to configuration properties.

        """
        self.collection_name = os.environ.get('BEERSMITH_COLLECTION')
        self.collection_name_raw = f'raw_{self.collection_name}'
        logger.debug(f'collection_name: {self.collection_name}')
        super().__init__(config_name=self.collection_name)

        # initialize MongoDB collection
        self.collection = self.read_collection(self.collection_name)
        self.collection_raw = self.read_collection(self.collection_name_raw)

    def pull(self, filename=None, path=None, save_last=True, **kwargs):
        """Pull updated recipes in MongoDB.

        Args:
            filename: Name of the recipe file.
            path: Location of the recipe file.
            save_last (bool): if set to True (default), details of the last
                object retrieved is saved in the configuration properties
            **kwargs: keyword arguments that specify the timespan to retrieve.
        """
        start, end = self.timespan(collection='beersmith', **kwargs)
        logger.debug(f'timespan: {start}, {end}')

        archive_list = self.update_recipes_from_archive(
            filename=filename, basepath=path, start=start, end=end
        )

        # clear rebuild flag, if set
        self.props.rebuild = False
        self.props.update()

        # logger.debug(f'recipes processed: {updated_count}')

    def rebuild(self, filename=None, path=None, save_last=True):
        """Rebuild recipes in MongoDB.

        Args:
            filename: Name of the recipe file.
            path: Location of the recipe file.
            save_last (bool): if set to True (default), details of the last
                object retrieved is saved in the configuration properties
        """
        # reset the database
        self.reset()

        updated_count = self.update_recipes(filename, path, save_last)

        # clear rebuild flag, if set
        self.props.rebuild = False
        self.props.update()

        # verify count
        recipe_count = self.collection.count_documents({})
        if recipe_count == updated_count:
            logger.debug(f'Recipe collection rebuilt, count: {recipe_count}')
        else:
            logger.warning('Recipe collection rebuilt, discrepancies found')

    def reset(self):
        logger.debug('resetting recipe collection...')
        self.collection.drop()

        # reset props
        self.props.delete()

    def read_recipes(self, filename=None, path=None, **kwargs):
        """Returns a set of recipes.

        Args:
            filename: Name of the recipe file.
            path: Location of the recipe file.
            **kwargs: keyword arguments that specify the timespan to retrieve.
        """
        start, end = self.timespan(collection='beersmith', **kwargs)
        logger.debug(f'timespan: {start}, {end}')

        recipe_list = self.bsm.read_bsmx(filename=filename, path=path)

        return recipe_list

    def read_archive(self, filename=None, path=None):
        """Returns a set of recipes from the recipe archive.

        Args:
            filename: Name of the recipe file.
            path: Location of the recipe file.
            start: Beginning date to process archive records.
            end: End date to process archive records.
        """
        archive_list = self.bsm.read_bsmx(filename=filename, path=path)

        return archive_list

    def save_raw_recipe(self, recipe):
        pass

    def update_recipes(self, filename=None, path=None, save_last=True):
        """Update recipes in MongoDB.

        Args:
            filename: Name of the recipe file.
            path: Location of the recipe file.
            save_last (bool): if set to True (default), details of the last
                object retrieved is saved in the configuration properties
        """
        # TODO: log recipe name, use progress bar

        # read the recipes from BeerSmith
        logger.info('reading Beersmith recipes...')
        recipe_list = self.read_recipes(filename, path)

        # update each recipe
        update_count = 0
        for update_count, recipe in enumerate(recipe_list):
            self.update_recipe(recipe)

            logger.info(f'updated recipe: {recipe.get("name")}')

            # update config properties
            if save_last:
                self.props.last_updated = datetime.now().astimezone()
                self.props.last_id = recipe['name']
                self.props.update()

        return update_count + 1

    def update_recipe(self, recipe):
        """Save the provided BeerSmith Recipe into MongoDB.

        Args:
            recipe: Beersmith Recipe.

        Returns:
            The MongoDB representation of the BeerSmith Recipe object.
        """
        recipe_id = recipe['name']
        updated_recipe = self.collection.find_one_and_replace(
            filter={'_id': recipe_id},
            replacement=recipe,
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        return updated_recipe

    def delete_recipe(self, recipe_id=None):
        """Delete the recipe specified by the recipe identifier.

        Args:
            recipe: Beersmith Recipe identifier.

        Returns:
            The MongoDB representation of the BeerSmith Recipe object.
        """
        self.collection.delete_one(
            filter={'_id': recipe_id}
        )

    def update_recipes_from_archive(self, 
        filename='Archive.bsmx', basepath=None, start=None, end=None):
        """Updates a set of recipes from the recipe archive.

        Args:
            filename: Name of the archive file.
            basepath: Location of the archive file.
            start: Beginning date to process archive records.
            end: End date to process archive records.
        """
        rebuild_recipes = False

        # set default filename
        if not filename:
            filename = 'Archive.bsmx'
        if not basepath:
            basepath = self.bsm.default_path

        # read the archive
        archive_list = self.read_archive(filename, basepath)

        for archive in archive_list:
            action_date = parse(archive['date']).astimezone()

            if start and action_date < start:
                continue

            if end and action_date > end:
                continue
            
            action = archive['action']
            filename = archive['file']
            directory = archive['directory']
            archive_date = parse(archive['date']).astimezone()
            logger.debug(f'[{archive_date}] {archive["name"]}: {action}')

            # # set recipe file path
            # if directory.startswith('/'):
            #     directory = directory[1:]
            # path = os.path.join(basepath, directory)

            if action in ('Add Recipe', 'Insert/Paste'):
                recipe_list = self.read_recipes(filename, basepath)
                recipe = recipe_list[0]
                self.update_recipe(recipe)

                logger.debug(f'\tprocessed: {action}')

            elif action in ('Edit', 'Move'):
                recipe_list = self.read_recipes(filename, basepath)
                recipe = recipe_list[0]

                # confirm the recipe already exists
                recipe_id = recipe['name']
                recipe_check = self.collection.find_one({'_id': recipe_id})
                if recipe_check:
                    self.update_recipe(recipe)
                    logger.debug(f'\tprocessed: {action}')

                # if recipe was renamed, there is no way to find which was the source recipe
                # need to reload the entire database
                else:
                    logger.debug('\tEditing recipe names cause database inconsistencies. The database will be rebuilt.')
                    # config.rebuild = True
                    rebuild_recipes = True  # should be able to rebuild automatically, unless renamed recipe is not unique
                    break

            elif action == 'Delete/Cut':
                recipe_id = archive['name']
                self.delete_recipe(recipe_id)

            elif action == 'Paste':
                # this will create a twin record and there's no way of differentiating it with the original
                # need to reload the entire database
                logger.warning('\tCannot process "Paste" actions. Confirm that no duplicate recipes exist and rebuild the database.')
                rebuild_recipes = True  # need to let user fix the condition first and manually rebuild
                break

            # update props
            self.props.last_updated = archive_date
            self.props.last_id = recipe_id
            self.props.update()

        # reload the entire database if necessary
        if rebuild_recipes:
            self.props.rebuild = True
            self.props.update()


@dataclass
class Recipe:
    name: str = 'default'

    def __init__(self) -> None:
        pass
