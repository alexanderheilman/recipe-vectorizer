## Recipe Aggregator

## Recipe Aggregator

### Overview
Finding reliable recipes on the internet can be a challenge. Despite the abundance of information and options available, there is rarely a consensus on what ingredients belong in any given dish, and multiple highly-rated recipes for the same dish will sometimes differ dramatically. Which recipe is _actually_ the best? The most authentic? In all likelihood, the best version of the recipe is likely somewhere in the middle ground between a number of 'nearby' options.

With this in mind, my goal was to create a tool that would simplify and improve the online recipe search by condensing the overwhelming range of choices into a small handful of reliable and authentic recipes, each representing a common variation of the desired dish (e.g., search: 'chili' --> results: 'beef/tomato/bean chili', 'white chicken chili', 'vegetarian chili', etc.). Ultimately, I achieved this by collecting and vectorizing several thousand recipes from _allrecipes.com_, quantifying their mutual similarity using unsupervised learning algorithms--namely DBSCAN and graph-based clustering--and combining the results of this analysis with user ratings and reviews to generate 'optimized' versions of several different recipes.

### Data
#### Data collection
Though there are a variety of APIs available that provide access to recipe data for a reasonable price, I chose instead to scrape the data maunally from a single site, in part because it provided consistency in formatting between recipes (which proved invaluable), but more so because it represented a challenging yet valuable learning opportunity. Using a Selenium-based Python script, two EC2 instances were set up to crawl _allrecipes.com_ in parallel, scrape recipe data (i.e., name, cuisine (sub-)category, user reviews, and ingredients/proportions), and store it in a Mongo database. Approximately 2500 recipes were collected for this proof-of-concept project, most of them being slow-cooked dishes (e.g., soups, chilis, stews, curries, etc.), the rationale being that the quality of such dishes stems more from the ingredients and their proportions than it does the skill of the chef, thus making them ideal for a model that seeks to optimize the former, irrespective of the latter.

#### Ingredient parsing and normalization
Perhaps the largest challenge of this project was that, in order to compare recipes to one another on the basis of their ingredient proportions, it was necessary that all recipes' ingredient bills first be reduced to some standard form. While this is straightforward when directly comparing units of mass or volume, it is decidedly less so when comparing ingredients that are occasionally/often measured in counts (e.g., 1 medium onion vs. 1 cup onion vs. 1/2 pound onion). The issue is further complicated by the fact that ingredient lists commonly include unwanted descriptors (boneless, seedless) and preparation instructions (chopped, diced, grated) that make normalization of recipes all the more difficult. Nonetheless, using a complex parsing methodology that (i) identified quantitites/units, (ii) removed adjectives, adverbs and other unwanted words/phrases, (iii) merged similar ingredients, and (iv) converted all quantities to the same units, I was able to successfully convert the ingredient strings scraped from _allrecipes.com_ (e.g., `2 (14.5 oz.) cans diced tomatoes, 1 large yellow onion, chopped`) into a standard form consisting of only the ingredient and its approximate mass, in ounces (`{'tomato': 29, 'onion':8}`)

### Modeling
Once the recipes were 'vectorized' via the procedure described above, I was able to visualize, explore, and model the data using graph-based techniques and a modified version of the DBSCAN clustering algorithm.
#### Graph-based modeling


#### Modified DBSCAN


#### Recipe generation
