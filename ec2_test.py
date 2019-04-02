import selenium
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
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
    options = Options()
    options.headless = True
    browser = Chrome(options=options)
    search_allrecipes(food, browser, typo_rate=0.1)
    populate_search_page(browser, num_pages=0)
    names, hrefs = get_search_results(browser)
    time.sleep(3)
    recipes = []
    browser.get(hrefs[0])
    recipes.append(get_recipe_info(browser))
    print(recipes[0])