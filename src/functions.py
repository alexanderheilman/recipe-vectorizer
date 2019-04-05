'''
A collection of functions to assist it webscraping.
'''

import selenium
from selenium.webdriver import Chrome
import string
from string import ascii_lowercase
import time
import numpy as np
import pandas as pd
import pymongo

####################################
#   Searching and crawling functions
####################################
def search_allrecipes(search_item, browser, typo_rate=0.1, sleep=1):
    """
    Goes to the Allrecipes.com homepage and searches for
    item specified by 'search_item'
    Inputs:
        search_item(str): The item (food) to search for 
        browser(object):  Selenium browser object (e.g., Chrome())
        typo_rate(float): Rate of typing errors, between 0 (none) 
                          and 1 (commits error every letter). Also 
                          affects typing speed.
    """
    url='https://www.allrecipes.com'
    browser.get(url)
    time.sleep(sleep+np.random.random())
    sel = 'input#searchText'
    search_bar = browser.find_element_by_css_selector(sel)
    search_bar.click()
    type_word(search_item, search_bar, typo_rate)
    search_bar.send_keys('\n')

def type_word(word, field, typo_rate=0.1):
    '''
    Simulates typing of "word" into input field.
    Inputs:
        word(str): Word(s) to type
        field(object): Selenium object associated with an input field
        typo_rate(float): Rate of typing errors, between 0 (none) 
                          and 1 (commits error every letter). Also 
                          affects typing speed.
    ''' 
    for char in word:
        if np.random.random() < typo_rate:
            field.send_keys(make_typo(char))
            time.sleep(0.2 * np.random.random() + typo_rate)
            field.send_keys('\b')
        field.send_keys(char)
        time.sleep(0.05 * np.random.random() + typo_rate)

def make_typo(key):
    '''
    Returns a letter adjacent or identical to the input key.
    Inputs:
        key(str): A string of length 1 containing a single ascii letter 
    '''
    key = key.lower()
    row2 = list('qwertyuiop[')
    row3 = list("asdfghjkl;")
    row4 = list('zxcvbnm,.')
    adj_keys = [key]
    if key in row2:
        idx = row2.index(key)
        if idx > 0:
            adj_keys += [row2[idx-1] , row2[idx+1]] + row3[idx-1:idx+1]
        else:
            adj_keys += list('was')
    elif key in row3:
        idx = row3.index(key)
        if idx > 0:
            adj_keys += row2[idx:idx+2] + [row3[idx-1] , row3[idx+1]] + row4[idx-1:idx+1]
        else:
            adj_keys += list('qwsz')
    elif key in row4:
        idx = row4.index(key)
        if idx > 0:
            adj_keys += row3[idx:idx+2] + [row4[idx-1] , row4[idx+1]]
        else:
            adj_keys += list('asx')
    return np.random.choice(adj_keys)

def clear_field(field):
    '''Simulates deletion of text in an input field'''
    contents = field.get_attribute('value')
    for _ in contents:
        field.send_keys('\b')
        time.sleep(0.02 * np.random.random() + 0.05)

def get_search_results(browser):
    '''
    Finds and returns all recipe ids, names, and hyperlinks on current browser page.
    '''
    sel = 'article.fixed-recipe-card'
    search_results = browser.find_elements_by_css_selector(sel)
    hrefs = []
    names = []
    for element in search_results:
        try:
            sel = 'div.fixed-recipe-card__info h3 a'
            info = element.find_element_by_css_selector(sel)
            href = info.get_attribute('href')
            hrefs.append(href.split('/?')[0])
            names.append(info.text)
        except:
            continue
    ids = []
    for href in hrefs:
        id_and_name = href.split('recipe/')[1]
        ids.append(int(id_and_name.split('/')[0]))
    return ids, names, hrefs

def populate_search_page(browser, num_pages=10, scroll_delay=4):
    '''Populates browser page with specified number of pages of search results'''
    for _ in range(num_pages):
        try:
            sel = 'button#btnMoreResults'
            more_button = browser.find_element_by_css_selector(sel)
            more_button.click()
        except:
            browser.execute_script('window.scrollTo(0, document.body.scrollHeight - 1000);')
        time.sleep(scroll_delay + scroll_delay*np.random.random())

def create_search_url(keyword, page_num, sort_order='p'):
    '''
    sort_order options:'p' = Popular, 're' = Best Match, 'n' = Newest
    '''
    if page_num == 1:
        url = 'https://www.allrecipes.com/search/results/?wt={0}&sort={1}'.format(keyword, sort_order)
    else:
        url = 'https://www.allrecipes.com/search/results/?wt={0}&sort={1}&page={2}'.format(keyword, sort_order, page_num)
    return url

########################################
#   Database management functions
########################################
def add_results_to_collection(browser, collection):
    ids, names, hrefs = get_search_results(browser)
    for i, name, href in zip(ids, names, hrefs):
        # If 'id' is not in database, add entry
        if len(list(collection.find({'id':i}))) == 0:
            item = {'id':i,
                    'name': name,
                    'href': href,
                    'viewed': 0}
            collection.insert_one(item)

def mark_as_viewed(recipe_id, collection, error=False):
    indicator = -1 if error else 1
    collection.update_one({'id':recipe_id},
                          {"$set":{'viewed': indicator}}, upsert=False)

def get_next_recipe(collection, reverse=False):
    direction = -1 if reverse else 1
    cursor = collection.find({'viewed':0}).sort([('_id',direction)]).limit(1)
    return next(cursor)

def remove_duplicates_and_update_serach_results():
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    results_coll = db['search_results']

    while True:
        cursor = recipes_coll.find()
        repeats = set()
        for recipe in cursor:
            
            if len(list(recipes_coll.find({'id':recipe['id']}))) > 1:
                repeats.add(recipe['id'])
        print('{} repeats found in "recipes" collection.'.format(len(repeats)))
        if len(repeats) == 0:
            break
        for recipe_id in repeats:
            recipes_coll.delete_one({'id':recipe_id})

    len_prev = 0
    while True:
        cursor = results_coll.find()
        repeats = set()
        len_current = 0
        for result in cursor:
            if len(list(results_coll.find({'id':result['id']}))) > 1:
                repeats.add(result['id'])
            len_current += 1
        print('{} repeats found in "search_results" collection.'.format(len(repeats)))
        if len(repeats) == 0:
            break
        # Remove 'unviewed' repeats before removing 'viewed' repeats
        # (only remove 'viewed' if we aren't making progress removing
        # 'unviewed' entries.)
        if len_prev == len_current:
            for result_id in repeats:
                del_result = results_coll.delete_one({'id':result_id, 'viewed':-1})
                if del_result.deleted_count == 0:
                    results_coll.delete_one({'id':result_id, 'viewed':1})
        else:
            for result_id in repeats:
                results_coll.delete_one({'id':result_id, 'viewed':0})
        
        len_prev = len_current

    cursor = recipes_coll.find()
    for recipe in cursor:
        results_coll.update_one({'id':recipe['id']},
                          {"$set":{'viewed': 1}}, upsert=False)


########################################
#   Recipe scraping functions
########################################
def get_recipe_info(browser):
    recipe_info = {}
    recipe_info['id'] = _get_id(browser)
    recipe_info['name'] = _get_name(browser)
    recipe_info['href'] = browser.current_url.split('?')[0]
    recipe_info['category'] = _get_categories(browser)
    recipe_info['rating_info'] = _get_rating_info(browser)
    try:
        recipe_info['submitter_info'] = _get_submitter_info(browser)
    except:
        recipe_info['submitter_info'] = None
    ingredients = _get_ingredients(browser)
    recipe_info['ingredients'] = parse_ingredients(ingredients)
    recipe_info['ingredients_raw'] = ingredients
    recipe_info['directions'] = _get_directions(browser)
    return recipe_info

def _get_id(browser):
    id_and_name = browser.current_url.split('recipe/')[1]
    return int(id_and_name.split('/')[0])
    
def _get_name(browser):
    sel = 'h1#recipe-main-content'
    name = browser.find_element_by_css_selector(sel)
    return name.text

def _get_categories(browser):
    sel = 'ol.breadcrumbs li'
    categories = browser.find_elements_by_css_selector(sel)
    cat_list = [category.text for category in categories]
    cat_dict = {}
    cat_dict['lvl_1'] = cat_list[2]
    try:
        cat_dict['lvl_2'] = cat_list[3]
    except:
        cat_dict['lvl_2'] = None
    try:
        cat_dict['lvl_3'] = cat_list[4]
    except:
        cat_dict['lvl_3'] = None
    return cat_dict

def _get_rating_info(browser):
    rating_info = {}
    sel = 'div.rating-stars'
    rating = browser.find_element_by_css_selector(sel)
    rating_info['rating'] = float(rating.get_attribute('data-ratingstars'))
    sel = 'div.summary-stats-box'
    reviews = browser.find_element_by_css_selector(sel).text.split()
    try:
        n_made = int(reviews[0])
    except:
        n_made = int(reviews[0][:-1]) * 1000
    try:
        n_reviews = int(reviews[4])
    except:
        n_reviews = int(reviews[4][:-1]) * 1000    
    rating_info['made_by'] = n_made
    rating_info['reviews'] = n_reviews

def _get_submitter_info(browser):
    submitter_info = {}
    sel = 'div.summary-background div.submitter'
    submitter = browser.find_element_by_css_selector(sel)
    followers = submitter.find_element_by_css_selector('div.submitter__img span').text
    name = submitter.find_element_by_css_selector('p span.submitter__name').text
    href = (submitter.find_element_by_css_selector('div.submitter__img a')
                     .get_attribute('href'))
    id_num = href.split('/')[-2]
    submitter_info['id'] = int(id_num)
    submitter_info['name'] = name
    submitter_info['followers'] = int(followers)
    submitter_info['href'] = href
    return submitter_info

def _get_ingredients(browser):
    '''
    Finds all ingredients required for the recipe on the current page
    and returns them as a list of strings
    '''
    all_items = []
    count = 1
    while True:
        try:
            sel = 'ul#lst_ingredients_{0}'.format(count)
            ing_list = browser.find_element_by_css_selector(sel)
            all_items += ing_list.text.split('\n')
            count += 1
        except:
            break
    ingredients = []
    for item in all_items:
        if item[0] in string.digits:
            ingredients.append(item)
    return ingredients

def _get_directions(browser):
    directions = {}
    try:
        directions['timing'] = _get_timing(browser)
    except:
        directions['timing'] = None
    sel = 'div.directions--section li.step'
    steps = browser.find_elements_by_css_selector(sel)
    directions['steps'] = [step.text for step in steps if step.text]
    try:
        directions['servings'] = _get_servings(browser)
    except:
        directions['servings'] = None
    return directions

def _get_timing(browser):
    timing = {}
    sel = 'div.directions--section ul.prepTime li.prepTime__item'
    timing_list = browser.find_elements_by_css_selector(sel)
    time_str = timing_list[1].get_attribute('aria-label').split(': ')[1]
    timing['prep'] = _parse_timing_string(time_str)
    time_str = timing_list[2].get_attribute('aria-label').split(': ')[1]
    timing['cook'] = _parse_timing_string(time_str)
    time_str = timing_list[3].get_attribute('aria-label').split('Ready in ')[1]
    timing['total'] = _parse_timing_string(time_str)
    return timing

def _parse_timing_string(string):
    total = 0
    if len(string.split('Hours')) > 1:
        total += 60 * int(string.split('Hours')[0])
        string = string.split('Hours')[1]
    if len(string.split('Hour')) > 1:
        total += 60 * int(string.split('Hour')[0])
        string = string.split('Hour')[1]
    if len(string.split('Minutes')) > 1:
        total += int(string.split('Minutes')[0])
    return total

def _get_servings(browser):
    sel = 'span.servings-count span.ng-binding'
    servings = browser.find_element_by_css_selector(sel)
    return int(servings.text)

########################################
#   Ingredient parsing functions
########################################

### CONSTANTS ###

units = ['pound', 'pounds', 'cup', 'cups', 'tablespoon', 'tablespoons', 'teaspoon', 'teaspoons',
         'clove', 'cloves', 'stalk', 'stalks', 'ounce', 'ounces', 'oz.', 'oz', 'cubes', 'pint', 'pints',
         'quart', 'quarts', 'dash', 'dashs', 'dashes', 'rib', 'ribs', 'bunch', 'bunches', 'pinch', 'head',
         'heads']

manual = ['2 to 3 pound', 'finely chopped from 1 can', 'onion soup, prepared from']

phrases = [' - ',', or ', ' for garnish', 'cut ', 'such as', ' like ', 'e.g.', 'with', ' or ', 'see note', 
           'to taste']

stopwords = ['and', 'into', 'very', 'hot', 'cold', 'warm', 'fresh', 'frozen', 'large', 'medium', 'small', 'halves', 'torn', 'bulk',
             'optional', 'fatfree', 'lowsodium', 'low', 'sodium', 'reducedsodium', 'reducedfat', 'ripe', 'lean',
             'extra', 'pure', 'goya', 'whole', 'ground', 'domestic']

suffixes = ['ed','less','ly']

flag_words = ['can or bottle', 'can', 'cans', 'package', 'packages', 'jar', 'jars', 'container', 'containers', 'bag', 'bags',
              'bottle', 'bottles', 'envelope', 'envelopes', 'carton','cartons', 'packet', 'packets']
flag_words.sort(key=len)
flag_words.reverse()

identicals = {'bell pepper':['green bell pepper', 'red bell pepper', 'yellow bell pepper', 'orange bell pepper'],
              'chicken': ['whole chicken', 'chicken breast', 'chicken thigh'],
              'onion': ['yellow onion', 'white onion', 'sweet onion', 'red onion']}

conversion_dict = {}
conversion_dict['ounce'] = {'other':1}
conversion_dict['cup'] = {'other':8}
conversion_dict['pint'] = {'other':16}
conversion_dict['quart'] = {'other':32}
conversion_dict['gallon'] = {'other':128}
conversion_dict['fluid ounce'] = {'other':1}
conversion_dict['milliliter'] = {'other':0.034}
conversion_dict['pound'] = {'other': 16}
conversion_dict['tablespoon'] = {'other': 1/2}
conversion_dict['teaspoon'] = {'other': 1/6}
conversion_dict['pinch'] = {'other': 0.1}
conversion_dict['dash'] = {'other': 0.1}

conversion_dict['bunch'] =  {'green onion': 3,
                             'cilantro': 2.8,
                             'parsley': 2,
                             'other': 3}
conversion_dict['bunche'] = conversion_dict['bunch']
conversion_dict['clove'] = {'garlic': 0.5, 'other': 0.5}
conversion_dict['cube'] = {'chicken bouillon': 0.4,
                           'beef bouillon': 0.4,
                           'vegetable bouillon': 0.4,
                           'other': 0.4}
conversion_dict['packet'] = {'other':1}
conversion_dict['head'] = {'other': 20,
                             'escarole': 10,
                             'garlic clove': 1.5,
                             'cabbage': 30,
                             'cauliflower': 30,
                             'broccoli': 20}
conversion_dict['rib'] = {'celery': 2, 'other': 2}
conversion_dict['stalk'] = {'celery': 2, 'other': 2}
conversion_dict['each'] = {'onion': 8,
                             'bell pepper': 6,
                             'potato': 6,
                             'carrot': 4,
                             'jalapeno pepper': 0.7,
                             'chicken': 10,
                             'bay leaf': 1,
                             'tomato': 6,
                             'green onion': 0.5,
                             'zucchini': 5,
                             'bay leave': 1,
                             'slices bacon': 1,
                             'lime': 1.5,
                             'head cabbage': 30,
                             'habanero pepper': 0.1,
                             'sweet potato': 6,
                             'eggs': 1,
                             'green chile pepper': 1,
                             'other': 1}

### MAIN FUNCTIONS ###

def parse_ingredients(ingredients, units=units, flag_words=flag_words):
    '''
    Parses a list of ingredients into a list of dictionaries with the following format: 
        {'quantity': (float),
         'units': (str),
         'ingredient': (str)}
    Also takes argument 'units', a list of accepted units (e.g., ['cups', 'tablespoon']).
    If an ingredident does not specify a unit in this list, the label 'each' will be applied.
    '''
    ing_list = []
    for item in ingredients:
        item_dict = {}
        # Check item for flag words/phrases(require special parsing treatment)
        manual_flag = False
        for man_phrase in manual:
            if len(item.split(man_phrase)) > 1:
                manual_flag = True
        sp_flag = False
        for word in item.split():
            if word in flag_words:
                f_word = word
                sp_flag = True
        if item.split()[1][0] == '(':
            f_word = '('
            sp_flag = True  
        # Parse quantities and units        
        if manual_flag:
            quantity, unit, remainder = _parse_manual(item)
            item_dict['quantity'] = quantity
            item_dict['units'] = unit if unit[-1] != 's' else unit[:-1]
        elif sp_flag:
            try:
                quantity, unit, remainder = _parse_special(item, flag_words)                
                item_dict['quantity'] = quantity
                item_dict['units'] = unit if unit[-1] != 's' else unit[:-1]
            except:
                # Exception for special units of unspecified size
                item_dict['quantity'] = float(item.split()[0])
                item_dict['units'] = f_word if f_word[-1] != 's' else f_word[:-1]
                remainder = ' '.join(item.split()[2:])
        else:
            quantity, remainder = _determine_quantity(item) 
            item_dict['quantity'] = quantity
            if remainder.split()[0] in units:
                unit = remainder.split()[0]
                item_dict['units'] = unit if unit[-1] != 's' else unit[:-1]
                remainder = ' '.join(remainder.split()[1:])
            else:
                item_dict['units'] = 'each'
        # Remove preparation instructions from remaining text to isolate ingredient
        parsed = _remove_descriptors(remainder)
        if not parsed:
            continue
        item_dict['ingredient'] = _merge_identicals(parsed, identicals)
        item_dict['normalized_qty'] = _normalize_ingredient_quantity(item_dict, conversion_dict)
        # Add item dictionary to list
        ing_list.append(item_dict)
    return ing_list


### HELPER FUNCTIONS ###

def _determine_quantity(item):
    quantity = 0
    for i, elem in enumerate(item.split()):
        if elem[0] in string.digits + '.':
            try:
                quantity += float(elem)
            except:
                numer, denom = elem.split('/')
                quantity += float(numer) / float(denom)
        else:
            idx = i
            break
    remainder = ' '.join(item.split()[idx:])
    return quantity, remainder

def _parse_special(item, flag_words):
    # Determine special word
    sp_word = ')'
    for word in flag_words:
        if len(item.split(word)) > 1:
            sp_word = ' ' + word + ' '
            break
    
    # Parse item 
    count_and_size = item.split(sp_word)[0]
    remainder = item.split(sp_word)[1]
    count, rest = _determine_quantity(count_and_size)
    if sp_word == ')':
        size, unit = _determine_quantity(rest[1:])
    else:
        size, unit = _determine_quantity(rest[1:-1])
    quantity = count * size
    return quantity, unit, remainder

def _parse_manual(item):
    if len(item.split('2 to 3 pound')) > 1:
        quantity = float(item.split()[0]) * 2.5
        unit = 'pound'
        remainder = item.split('2 to 3 pound')[1]
        return quantity, unit, remainder
    if len(item.split('finely chopped from 1 can')) > 1:
        quantity = 1.0
        unit = 'ounce'
        remainder = 'chipotle chile'
        return quantity, unit, remainder
    if len(item.split('onion soup, prepared from')) > 1:
        quantity = 1.5
        unit = 'cup'
        remainder = 'onion soup'
        return quantity, unit, remainder

def _remove_descriptors(item,
                        phrases=phrases,
                        stopwords=stopwords,
                        suffixes=suffixes):
    # Remove common/unnecessary ending phrases
    for phrase in phrases:
        if len(item.split(phrase)) > 1:
            item = item.split(phrase)[0]
    # Remove punctuation and stopwords
    words = []
    for elem in item.split():
        word = ''.join([letter for letter in elem.lower() if letter in string.ascii_lowercase])
        if word not in stopwords:
            words.append(word)
    # Remove adjectives and adverbs    
    for suffix in suffixes:
        for word in words.copy():
            try:
                if (word[-len(suffix):] == suffix) and word != 'red':
                    words.remove(word)
            except:
                continue    
    # Remove trailing spaces
    result = ' '.join([word for word in words if word])
    # Singularize (when not beans)...also, this code is asinine
    if result[-3:] == 'oes':
        result = result[:-2]
    if len(result) < 5:
        return result
    if result[-5:] == 'beans':
        return result
    else:
        return result if result[-1] != 's' else result[:-1]
    
def _normalize_ingredient_quantity(ingredient_dict, conversion_dict):
    ing = ingredient_dict['ingredient']
    qty = ingredient_dict['quantity']
    units = ingredient_dict['units']
    if units in conversion_dict.keys():
        conv_factor_dict = conversion_dict[units]
        if ing in conv_factor_dict.keys():
            conv_factor = conv_factor_dict[ing]
        else:
            conv_factor = conv_factor_dict['other']
        return qty * conv_factor
    else:
        return qty
    
def _merge_identicals(ingredient, identicals):
    for key, val in identicals.items():
        if ingredient in val:
            return key
    return ingredient