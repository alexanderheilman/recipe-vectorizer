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
def search_allrecipes(search_item, browser, typo_rate=0.1):
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
    time.sleep(1+np.random.random())
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

def mark_as_viewed(recipe_id, collection):
    collection.update_one({'id':recipe_id},
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
    sel = 'div.summary-stats-box a.read--reviews'
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
    return rating_info

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
    directions['timing'] = _get_timing(browser)
    sel = 'div.directions--section li.step'
    steps = browser.find_elements_by_css_selector(sel)
    directions['steps'] = [step.text for step in steps if step.text]
    directions['servings'] = _get_servings(browser)
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

# Constants
units = ['pound', 'pounds', 'cup', 'cups', 'tablespoon', 'tablespoons', 'teaspoon', 'teaspoons',
         'clove', 'cloves', 'stalk', 'stalks', 'ounce', 'ounces', 'oz.', 'cubes', 'pint', 'pints',
         'quart', 'quarts']
phrases = [' - ',', or', ', for garnish', ', cut', ' such as', ' like', 'e.g.']
stopwords = ['and', 'into', 'very', 'hot', 'cold', 'fresh', 'large', 'medium', 'small', 'halves', 'torn', 'bulk']
suffixes = ['ed','less','ly']
flag_words = ['can', 'cans', 'package', 'packages', 'jar', 'jars', 'container', 'containers', 'bag', 'bags']

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
        # Check item for flag words (require special parsing treatment)
        flag = False
        for word in item.split():
            if word in flag_words:
                flag = True
        if item.split()[1][0] == '(':
            flag = True  
        # Parse quantities and units        
        if flag:
            quantity, unit, remainder = _parse_special(item, flag_words)
            item_dict['quantity'] = quantity
            item_dict['units'] = unit if unit[-1] != 's' else unit[:-1]
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
        item_dict['ingredient'] = _remove_descriptors(remainder)
        # Add item dictionary to list
        ing_list.append(item_dict)
    return ing_list

def _determine_quantity(item):
    quantity = 0
    for i, elem in enumerate(item.split()):
        if elem[0] in string.digits:
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
        if word in item.split():
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
    return ' '.join(words)