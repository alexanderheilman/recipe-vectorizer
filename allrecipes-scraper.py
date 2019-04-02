import selenium
from selenium.webdriver import Chrome
import string
from string import ascii_lowercase
import time
import numpy as np
import pandas as pd
from functions import *
from sys import argv, exit

if __name__ == '__main__':
    if len(argv) != 2:
        print("Usage: python {} <food_item>".format(argv[0]))
        exit(1)
    food = argv[1]
    browser = Chrome()
    search_allrecipes(food, browser, typo_rate=0.1)
    populate_search_page(browser, num_pages=1)
    names, hrefs = get_search_results(browser)
    recipes = []
    browser.get(hrefs[0])
    time.sleep(2)
    recipes.append(get_recipe_info(browser))
    print(recipes[0])
