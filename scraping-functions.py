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

def get_name():
    '''Finds the name of the recipe and returns it as a string'''
    sel = 'h1#recipe-main-content'
    name = browser.find_element_by_css_selector(sel)
    return name.text

def get_ingredients():
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

def get_rating():
    '''
    Finds the rating of the current recipe and returns it as a float
    '''
    sel = 'div.rating-stars'
    rating = browser.find_element_by_css_selector(sel)
    return float(rating.get_attribute('data-ratingstars'))

def get_categories():
    '''
    Finds the hierarchy of categories to which the recipe belongs
    and returns it as a list of strings
    '''
    sel = 'ol.breadcrumbs li'
    categories = browser.find_elements_by_css_selector(sel)
    return [category.text for category in categories]

def get_search_results(browser):
    '''
    Finds and returns all recipe names and hyperlink references on current browser page.
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
    return names, hrefs