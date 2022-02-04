"""Class module to interface with Beersmith.
"""
import os
from collections import OrderedDict

from aracnid_logger import Logger
from bs4 import BeautifulSoup
import hjson
import xmltodict

# from beersmith_direct.recipes import Recipes

# initialize logging
logger = Logger(__name__).get_logger()


class BeersmithInterface:
    """Interface to Beersmith.

    Attributes:
        bsm: 
    """

    def __init__(self) -> None:
        """Initializes the Beersmith interface.

        Args:
            None.
        """
        self.default_filename = os.environ.get('BEERSMITH_DEFAULT_FILENAME')
        self.default_path = os.environ.get('BEERSMITH_DEFAULT_PATH')

    def read_bsmx(self, filename=None, path=None):
        """Reads a .bsmx file and returns a recipe folder of recipes.

        Args:
            filename: The supplied filename.
            path: The supplied directory.

        Returns:
            A list of recipes.
        """
        self.filename = filename if filename else self.default_filename
        self.path = path if path else self.default_path

        # read the file
        filepath = os.path.join(self.path, self.filename)
        if os.path.exists(filepath):
            with(open(filepath, 'r')) as bsmx_file:
                xml_string = bsmx_file.read()

                # replace some tag names from bsmx
                xml_string = xml_string.replace('_MOD_', 'last_modified')
                xml_string = xml_string.replace('_TExpanded', 'texpanded')
                xml_string = xml_string.replace('_XName', 'xname')
                xml_string = xml_string.replace('F_R_NAME', 'name')		# why do this here

                # replace archive tag names
                xml_string = xml_string.replace('F_AR_ACTION', 'action')
                xml_string = xml_string.replace('F_AR_NAME', 'name')		# why do this here
                xml_string = xml_string.replace('F_AR_DIRECTORY', 'directory')
                xml_string = xml_string.replace('F_AR_FILE', 'file')

                # process text
                if xml_string:
                    xml_beautiful = BeautifulSoup(xml_string, 'html.parser')

                    if xml_string.startswith('<Selections>') or xml_string.startswith('<Recipe>'):
                        parsed_obj = xmltodict.parse(xml_beautiful.prettify())
                        roottag, dict_items = parsed_obj.popitem()

                        if dict_items:
                            recipe_list = self.process_recipes(dict_items)

                            return recipe_list

                    elif xml_string.startswith('<Archive>'):
                        parsed_obj = xmltodict.parse(f'<root>{xml_beautiful}</root>')
                        roottag, dict_items = parsed_obj.popitem()

                        if dict_items:
                            archive_list = self.process_archive(dict_items)

                            return archive_list

        return []

    def process_recipes(self, dict_items):
        # To handle the recursive nature of embedded folders

        # set the folder name
        folder_name = dict_items['name']

        # bounce out if folder is empty
        if dict_items['data'] is None:
            return 0

        # get the data key, could be 'table' or 'recipe'
        data_key = list(dict_items['data'].keys())[0]

        # process folder data into items list
        item_dict = self.flatten_data(dict_items, data_key, 'items')

        recipe_list = []
        item_list = item_dict['items']
        for item in item_list:
            if 'xname' in item and item['xname'] == 'Folder':
                folder_recipe_list = self.process_folder(item)
                recipe_list.extend(folder_recipe_list)
            else:
                recipe = self.process_recipe(item, folder_name=folder_name)
                recipe_list.append(recipe)

        return recipe_list

    def process_archive(self, dict_items, **kwargs):
        archive_list = dict_items['archive']

        # process as list for one action
        if type(archive_list) is OrderedDict:
            archive_list = [archive_list]

        return archive_list

    def process_folder(self, props):
        # initialize return variable
        recipe_list = []
        # props_new = props
        # props_new['_type'] = 'folder'

        folder_name = props['name']

        # flatten sub data structures
        if 'data' in props:
            recipes_dict = self.flatten_data(props, 'recipe', 'recipes')
            # process each recipe
            recipe_num = 0
            while recipe_num < len(recipes_dict['recipes']):
                recipe_props = recipes_dict['recipes'][recipe_num]
                recipe_props = self.process_recipe(recipe_props, folder_name=folder_name)
                recipe_list.append(recipe_props)
                # recipes_dict['recipes'][recipe_num] = recipe_props
                recipe_num += 1

            # # add recipe props back
            # props_new.update(recipes_dict)

        # return folder
        return recipe_list

    def process_recipe(self, props, folder_name=None):
        # initialize return variable
        props_new = {}
        props_new['_type'] = 'recipe'
        
        # add recipe id
        props['_id'] = props['name']
        #print(props['name'])

        # add correct folder name
        # print('folder_name: {}'.format(folder_name))
        props['folder_name'] = '/{}/'.format(folder_name)

        # process sub data structures, flatten and remove key prefixes
        ingredients_props, ingredients_list = self.process_ingredients(props['ingredients'].pop('data'))
        props['ingredients_by_type'] = ingredients_props
        props['ingredients'] = ingredients_list

        props['mash'] = {}
        self.strip_key_prefixes('f_mh_', props.pop('f_r_mash'), props['mash'])
        mashsteps_dict = self.flatten_data(props['mash']['steps'], 'mashstep', 'mashsteps')
        self.strip_key_prefixes_list('f_ms_', mashsteps_dict['mashsteps'])
        props['mash'].update(mashsteps_dict)

        props['equipment'] = {}
        self.strip_key_prefixes('f_e_', props.pop('f_r_equipment'), props['equipment'])

        props['style'] = {}
        self.strip_key_prefixes('f_s_', props.pop('f_r_style'), props['style'])

        props['carb'] = {}
        self.strip_key_prefixes('f_c_', props.pop('f_r_carb'), props['carb'])

        props['base_grain'] = {}
        self.strip_key_prefixes('f_g_', props.pop('f_r_base_grain'), props['base_grain'])

        props['ferment'] = {}
        self.strip_key_prefixes('f_a_', props.pop('f_r_age'), props['ferment'])
        readings_dict = self.flatten_data(props['agedata'], 'agedata', 'readings')
        self.strip_key_prefixes_list('f_ad_', readings_dict['readings'])
        props['ferment'].update(readings_dict)
        props['ferment']['agedata'] = props.pop('agedata')

        # remove base key prefixes
        self.strip_key_prefixes('f_r_', props, props_new)

        # correct data types
        props_new = self.correct_type(props_new)

        # process notes
        notes = props_new['notes']
        if notes:
            notes_props = self.process_notes(notes)
            if type(notes_props) in (dict, OrderedDict):
                props_new.update(notes_props)

        return props_new

    def process_items(self, props, tag_old, tag_new=None):
        # initialize return variable
        props_new = {}
        items_new = []

        if not tag_new:
            tag_new = tag_old

        if props:
            # retrieve items
            items_old = props[tag_old]

            if type(items_old) == list:
                items_new.extend(items_old)
            elif type(items_old) in (dict, OrderedDict):
                items_new.append(items_old)

        # create the new properties
        props_new[tag_new] = items_new

        # return
        return props_new

    def process_ingredients(self, ingredients_props):
        # initialize return variable
        ingredients_by_type = ingredients_props
        ingredients_list = []

        # process ingredient subitems into lists
        for ingredient_type in ingredients_props:
            ingredient_dict = self.process_items(ingredients_props, ingredient_type)
            ingredient_list = ingredient_dict[ingredient_type]
            ingredient_num = 0
            while ingredient_num < len(ingredient_list):
                ingredient_props = ingredient_list[ingredient_num]
                ingredient_props = self.process_ingredient(ingredient_props, ingredient_type)
                ingredient_list[ingredient_num] = ingredient_props
                ingredients_list.append(ingredient_props)
                ingredient_num += 1

            ingredients_by_type[ingredient_type] = ingredient_list

        # sort the ingredients list
        ingredients_list = sorted(ingredients_list, key=lambda ingredient:ingredient['order'])

        return ingredients_by_type, ingredients_list

    def process_ingredient(self, ingredient_props, ingredient_type):
        # initialize new ingredient dict
        props_new = {}
        
        # determine the prefix, units
        if ingredient_type == 'grain':
            prefix = 'f_g_'
            units = 'oz'
        elif ingredient_type == 'hops':
            prefix = 'f_h_'
            units = 'oz'
        elif ingredient_type == 'yeast':
            prefix = 'f_y_'
            units = 'g'
        elif ingredient_type == 'misc':
            prefix = 'f_m_'
            units = ''
        elif ingredient_type == 'water':
            prefix = 'f_w_'
            units = 'oz'
        else:
            # print('[WARNING] Unhandled Ingredient Type: {}'.format(ingredient_type))
            prefix = ''
            units = ''

        # add 'units' tag
        props_new['units'] = units
        
        # rename f_order key
        if 'f_order' in ingredient_props:
            props_new['order'] = ingredient_props['f_order']

        # remove tag prefixes
        self.strip_key_prefixes(prefix, ingredient_props, props_new)

        # ingredient specific processing
        if ingredient_type == 'grain':
            subtype_code = self.correct_type(props_new['type'])
            subtype_list = ['grain', 'extract', 'sugar', 'adjunct', 'dry extract']
            props_new['subtype'] = subtype_list[subtype_code]

        elif ingredient_type == 'yeast':
            form_code = self.correct_type(props_new['form'])
            form_list = ['liquid', 'dry', 'slant', 'culture']
            props_new['form_text'] = form_list[form_code]
            props_new['subtype'] = '{} yeast'.format(props_new['form_text'])

        elif ingredient_type == 'hops':
            form_code = self.correct_type(props_new['form'])
            form_list = ['pellet', 'plug', 'leaf', 'extract (CO2)', 'extract (isomerized)']
            props_new['form_text'] = form_list[form_code]
            props_new['subtype'] = '{} hops'.format(props_new['form_text'])
            
        elif ingredient_type == 'misc':
            subtype_code = self.correct_type(props_new['type'])
            subtype_list = ['spice', 'fining', 'herb', 'flavor', 'other', 'water-agent']
            props_new['subtype'] = subtype_list[subtype_code]
        else:
            props_new['subtype'] = None

        # process notes
        notes = props_new['notes']
        if notes:
            notes_props = self.process_notes(notes)
            if type(notes_props) in (dict, OrderedDict):
                props_new.update(notes_props)

        # add 'type' tag
        props_new['ingredient_type'] = ingredient_type

        # replace the ingredients
        return props_new

    def process_notes(self, notes):
        # print('notes: {}'.format(notes))

        try:
            props = hjson.loads(notes)
            # print('hjson: {}'.format(props))
        except hjson.scanner.HjsonDecodeError:
            props = notes

        return props

    def flatten_data(self, props, tag_old, tag_new=None):
        props_data = props.pop('data')
        props_dict = self.process_items(props_data, tag_old, tag_new)
        return props_dict

    def strip_key_prefixes(self, prefix, props_from, props_to):
        # print('strip_key_prefixes()-->props_from: {}'.format(props_from))
        if type(props_from) in (dict, OrderedDict):
            for key in props_from:
                # if prefix == 'f_ms_':
                # 	print('strip_key_prefixes()-->key: {}'.format(key))
                # remove key prefix
                if key.startswith(prefix):
                    props_to[key[len(prefix):]] = props_from[key]
                # copy over all other keys
                else:
                    props_to[key] = props_from[key]
        else:
            print('strip_key_prefixes()-->cannot process {}'.format(type(props_from)))

    def strip_key_prefixes_list(self, prefix, props):
        item_num = 0
        while item_num < len(props):
            item_new = {}
            item = props[item_num]
            self.strip_key_prefixes(prefix, item, item_new)
            props[item_num] = item_new
            item_num += 1

    @classmethod
    def get_ingredient_amount(cls, ingredient):
        amount = float(ingredient['amount'])
        units = ingredient['units']
        ingredient_type = ingredient['ingredient_type']

        if ingredient_type == 'grain':
            if units == 'oz':
                amount /= 16
                units = 'lbs'
            
        return amount, units

    def read_xml():
        """
        Reads a BeerXML file and returns a RecipeFolder of recipes
        """
        pass

    def correct_type(self, invar):
        # initialize return variable
        outvar = None

        if type(invar) in (dict, OrderedDict):
            outvar = self.correct_type_dict(invar)
        elif type(invar) is list:
            outvar = self.correct_type_list(invar)

        else:
            try:
                float(invar)
                outvar = float(invar)
                if outvar.is_integer():
                    outvar = int(outvar)
            except (ValueError, TypeError):
                outvar = invar

        return outvar

    def correct_type_dict(self, invar):
        # initialize return variable
        outvar = {}

        for key in invar:
            outvar[key] = self.correct_type(invar[key])

        return outvar

    def correct_type_list(self, invar):
        # initialize return variable
        outvar = []

        index = 0
        while index < len(invar):
            outvar.append(self.correct_type(invar[index]))
            index += 1

        return outvar
