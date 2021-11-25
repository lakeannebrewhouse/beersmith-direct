import pytest
import os

from beersmith_direct import Recipes

RECIPE_NAME = '2021-11-16_Reston Red Ale'
RECIPE_NAME_2 = '2021-11-16_Reston Red Ale 2'

@pytest.fixture(name='recipes')
def fixture_recipes():
    """Pytest fixture to initialize and return the BeersmithInterface object.
    """
    return Recipes()

def test_read_bsmx_one_recipe(recipes):
    filename = 'bsm-one-recipe.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 1
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_read_bsmx_two_recipes(recipes):
    filename = 'bsm-two-recipes.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 2
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_read_bsmx_one_folder(recipes):
    filename = 'bsm-one-folder-one-recipe.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 1
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_read_bsmx_two_folders(recipes):
    filename = 'bsm-two-folders.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 2
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_read_bsmx_nested_folders(recipes):
    filename = 'bsm-nested-folders.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipe_list = recipes.read_recipes(filename=filename, path=path)

    assert recipe_list
    assert len(recipe_list) == 2
    assert recipe_list[0]['name'] == RECIPE_NAME

def test_reset_recipes(recipes):
    recipes.reset()

    assert True

def test_rebuild_one_recipe(recipes):
    filename = 'bsm-one-recipe.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipes.rebuild(filename, path)

    assert recipes.collection.count_documents({}) == 1

def test_rebuild_two_recipes(recipes):
    filename = 'bsm-two-recipes.bsmx'
    path = os.path.join(os.getcwd(), 'tests')
    recipes.rebuild(filename, path)

    assert recipes.collection.count_documents({}) == 2

def test_update_recipes(recipes):
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
    assert recipes.props.last_updated
    assert recipes.props.last_id

def test_read_rebuild_prop(recipes):
    assert 'rebuild' in recipes.props.props

def test_read_archive_one_action(recipes):
    filename = 'bsm-archive-add.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    archive_list = recipes.read_archive(filename=filename, path=path)

    assert len(archive_list) == 1

def test_read_archive_two_actions(recipes):
    filename = 'bsm-archive-two-actions.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    archive_list = recipes.read_archive(filename=filename, path=path)

    assert len(archive_list) == 2

def test_read_archive_add(recipes):
    filename = 'bsm-archive-add.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipes.reset()
    archive_list = recipes.update_recipes_from_archive(filename=filename, basepath=path)

    assert recipes.collection.count_documents({}) == 1

def test_read_archive_edit(recipes):
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
    filename = 'bsm-archive-delete.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipe_count = recipes.collection.count_documents({})

    recipes.update_recipes_from_archive(filename=filename, basepath=path)

    recipe = recipes.collection.find_one({'_id': RECIPE_NAME})
    assert not recipe
    assert recipes.collection.count_documents({}) == recipe_count - 1

def test_read_archive_paste(recipes):
    filename = 'bsm-archive-paste.bsmx'
    path = os.path.join(os.getcwd(), 'tests')

    recipes.props.rebuild = False
    recipes.props.update()

    recipes.update_recipes_from_archive(filename=filename, basepath=path)

    assert recipes.props.rebuild == True

def test_pull_filter_0(recipes):
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
    filename = 'Archive.bsmx'
    # path = os.path.join(os.getcwd(), 'tests')
    path = None

    archive_list = recipes.read_archive(filename=filename)

    assert len(archive_list) > 0
