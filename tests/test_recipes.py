"""Tests recipes functionality.
"""
import os

import pytest

from beersmith_direct import Recipes

RECIPE_NAME = '2021-11-16_Reston Red Ale'
RECIPE_NAME_2 = '2021-11-16_Reston Red Ale 2'

@pytest.fixture(name='recipes')
def fixture_recipes():
    """Pytest fixture to initialize and return the BeersmithInterface object.
    """
    return Recipes()

def test_read_bsmx_one_recipe(recipes):
    """Tests reading BSMX file with one recipe.
    """
    filename = 'bsm-one-recipe.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 1
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_read_bsmx_two_recipes(recipes):
    """Tests reading BSMX file with two recipes.
    """
    filename = 'bsm-two-recipes.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 2
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_read_bsmx_one_folder(recipes):
    """Tests reading BSMX file with one folder.
    """
    filename = 'bsm-one-folder-one-recipe.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 1
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_read_bsmx_two_folders(recipes):
    """Tests reading BSMX file with two folders.
    """
    filename = 'bsm-two-folders.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 2
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_read_bsmx_nested_folders(recipes):
    """Tests reading BSMX file with nested folders.

    Not currently working.
    """
    filename = 'bsm-nested-folders.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 2
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_reset_recipes(recipes):
    """Helper function to reset recipes object.
    """
    recipes.reset()

    assert True

def test_rebuild_one_recipe(recipes):
    """Tests rebuilding one recipe.
    """
    filename = 'bsm-one-recipe.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipes.rebuild(filename, path)

    assert recipes.collection.count_documents({}) == 1

def test_rebuild_two_recipes(recipes):
    """Tests rebuilding two recipes.
    """
    filename = 'bsm-two-recipes.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipes.rebuild(filename, path)

    assert recipes.collection.count_documents({}) == 2

def test_update_recipes(recipes):
    """Tests updating one recipe.
    """
    filename = 'bsm-one-recipe.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipes.reset()
    recipes.update_recipes(filename, path)

    assert recipes.collection.count_documents({}) == 1

@pytest.mark.skip(reason="manual test")
def test_rebuild_complete(recipes):
    """This tests rebuilding the entire database.

    It should not be an automated test.
    """
    recipes.rebuild()

    assert True

def test_verify_config(recipes):
    """Verifies configuration.
    """
    assert recipes.props.last_updated
    assert recipes.props.last_id

def test_read_rebuild_prop(recipes):
    """Verifies 'rebuild' property.
    """
    assert 'rebuild' in recipes.props.props

def test_read_archive_one_action(recipes):
    """Tests reading archive with one action.
    """
    filename = 'bsm-archive-add.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    archive_list = recipes.read_archive(filename=filename, path=path)

    assert len(archive_list) == 1

def test_read_archive_two_actions(recipes):
    """Tests reading archive with two actions.
    """
    filename = 'bsm-archive-two-actions.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    archive_list = recipes.read_archive(filename=filename, path=path)

    assert len(archive_list) == 2

def test_read_archive_add(recipes):
    """Tests reading archive with 'add' action.
    """
    filename = 'bsm-archive-add.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipes.reset()
    recipes.update_recipes_from_archive(filename=filename, basepath=path)

    assert recipes.collection.count_documents({}) == 1

def test_read_archive_edit(recipes):
    """Tests reading archived with 'edit' action.
    """
    filename = 'bsm-archive-edit.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipe_count = recipes.collection.count_documents({})
    recipe = recipes.collection.find_one({'_id': RECIPE_NAME})
    brewer = recipe['brewer']

    recipes.update_recipes_from_archive(filename=filename, basepath=path)

    recipe = recipes.collection.find_one({'_id': RECIPE_NAME})
    assert recipes.collection.count_documents({}) == recipe_count
    assert recipe['brewer'] == 'New Brewer' != brewer

def test_read_archive_delete(recipes):
    """Tests reading archive with 'delete' action.
    """
    filename = 'bsm-archive-delete.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipe_count = recipes.collection.count_documents({})

    recipes.update_recipes_from_archive(filename=filename, basepath=path)

    recipe = recipes.collection.find_one({'_id': RECIPE_NAME})
    assert not recipe
    assert recipes.collection.count_documents({}) == recipe_count - 1

def test_read_archive_paste(recipes):
    """Tests reading archive with 'paste' action.
    """
    filename = 'bsm-archive-paste.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipes.props.rebuild = False
    recipes.props.update()

    recipes.update_recipes_from_archive(filename=filename, basepath=path)

    assert recipes.props.rebuild is True

def test_pull_filter_0(recipes):
    """Tests pull with filter type 0.
    """
    filename = 'bsm-two-recipes.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipes.rebuild(filename, path)
    assert recipes.collection.count_documents({}) == 2

    filename = 'bsm-archive-two-actions.bsmx'
    begin_str = '2021-11-24'
    recipes.pull(filename=filename, path=path, begin_str=begin_str)

    recipe = recipes.collection.find_one({'_id': RECIPE_NAME})
    assert recipe['brewer'] == 'Romano'
    recipe = recipes.collection.find_one({'_id': RECIPE_NAME_2})
    assert recipe['brewer'] == 'Romano'

def test_pull_filter_1(recipes):
    """Tests pull with filter type 1.
    """
    filename = 'bsm-two-recipes.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipes.rebuild(filename, path)
    assert recipes.collection.count_documents({}) == 2

    filename = 'bsm-archive-two-actions.bsmx'
    begin_str = '2021-11-15'
    recipes.pull(filename=filename, path=path, begin_str=begin_str)

    recipe = recipes.collection.find_one({'_id': RECIPE_NAME})
    assert recipe['brewer'] == 'Romano'
    recipe = recipes.collection.find_one({'_id': RECIPE_NAME_2})
    assert recipe['brewer'] == 'New Brewer'

def test_pull_filter_2(recipes):
    """Tests pull with filter type 2
    """
    filename = 'bsm-two-recipes.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipes.rebuild(filename, path)
    assert recipes.collection.count_documents({}) == 2

    filename = 'bsm-archive-two-actions.bsmx'
    begin_str = '2021-10-31'
    recipes.pull(filename=filename, path=path, begin_str=begin_str)

    recipe = recipes.collection.find_one({'_id': RECIPE_NAME})
    assert recipe['brewer'] == 'New Brewer'
    recipe = recipes.collection.find_one({'_id': RECIPE_NAME_2})
    assert recipe['brewer'] == 'New Brewer'

def test_read_archive_official(recipes):
    """Tests reading official archive file.
    """
    filename = 'Archive.bsmx'

    archive_list = recipes.read_archive(filename=filename)

    assert len(archive_list) > 0
