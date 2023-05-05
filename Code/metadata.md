The code of this app is [available here](https://github.com/jimmy-feng/Dissertation_App/blob/heroku/Visualize_POI_Dash.py).

Lead researchers: Jimmy Feng & Shih-Lung Shaw at the University of Tennessee, Knoxville

 * To share feature suggestions, changes, and/or issues with the
   app, please feel free to contact Jimmy Feng at jfeng12@vols.utk.edu.


### Introduction
This is a demo of an interactive GIS to better understand food access. Users can examine movements over space-time of synthetic people, visualize food opportunities relative to locations of people and their daily travels, query food stores based on different characteristics perceived as desirable, visualize different census variables depicting social vulnerability and socioeconomic characteristics of block groups in Knox County, Tennessee, and identify the food opportunities accessible to people along different shopping modalities.

Each of the four panels are interlinked and depict a different perspective into the food opportunities available to people inspired by four conceptualizations of space in Shaw and Sui [(2021)](https://doi.org/10.1080/24694452.2019.1631145)'s splatial framework. Any user interaction in one panel results in sychronized changes across all other panels. Colors for each individual and store type are uniform across the 2D Map, 3D Plot, and Food Network.

##### Upper-Left: 2-D Map of Food Stores and People
An interactive 2-D map depicts all the potential food opportunities accessible by all individuals shown. Food opportunities are colored by a main POI type with a manual classification system described below. Users can zoom in/out and pan the map interface, set the time period, and add contextual layers from the United States Census at the block-group level related to food access and social vulnerability. Legend interaction is disabled here.
##### Upper-Right: 3-D Space-Time Plot of Human Trajectories
The interactive 3-D plot illustrates individuals' movements over space (x- + y-axes) and time (z-axis.) All potential food opportunities are similarly shown as colored circles at the bottom of the plot. The legend contains each individual represented with a unique color and their respective ID.
* Clicking once on an individual in the legend removes them from all other panels and renders them inactive in the legend. Clicking once again renders them active and visible in all panels.
* Double-clicking an individual in the legend reduces all individuals shown to just the clicked individual. In other words, all other individuals are rendered inactive. To reset the view and make all individuals visible, simply double-click the legend.
* Clicking at a specific location in the plot will coerce the view of the 2-D Map to focus on the latitude and longitude of that location. In this sense, a relative-space perspective is depicted whereby any nearby food opportunities based on one's given location at a point in time are shown.
##### Lower-Left: Food Network
A food network reflects the relationships (i.e., potential connections) between individuals and stores and with other individuals.
* Clicking on any node isolates all visible lines to all potential connections to and from that node. For example, clicking on a store will show all individuals who can access that store with line connections depicting the modality of potential access. All clicked and visible nodes are labelled; stores are labelled according to their store name and their Google Plus Code while individuals are labelled according to their unique ID.
* All user clicks of nodes are retained until the Reset Network button is clicked. This helps to explore first, second, ... n-order food opportunities whereby connections between people can be visualized and expanded to visually examine the potential opportunities available to both an individual as well as the individual's first, second, ..., n-order connections.
- *Layout*: Click any option in the dropdown menu to set the network to a different layout. 
- *Person Shape*: Click any option in the dropdown menu to set the shape of nodes representing individuals.
- *Store Shape*: Click any option in the dropdown menu to set the shape of nodes representing stores.
- *Reset Network*: Click the button to reset the view of the network to the original state.
- *Line Legend*
    - Green lines indicate that the connection between an individual to a store or another individual only exists physically (e.g., a person can only visit a store in-person.)
    - Blue lines indicate that the connection between an individual to a store or another individual only exists virtually (e.g., a person can only access a grocery store online.)
    - Yellow lines indicate that the connection between an individual to a store or another individual can exist both physically and virtually (e.g., a person can access a store both in-person or online.)
    
##### Lower-Right: Socioeconomic, Demographic, and Perceived Data Tables
Interactive tables containing detailed socioeconomic, demographic, and perceived characteristics of people and attributes of food stores. These can be queried to subset either or both. Stores can be filtered based on user preferences while individuals can be subset based on their specific attributes. Users can enter queries in the cells in the first row below the header of each table. Traditional mathematical notation can be used, e.g., in the 'Price' for the Food Stores table, if someone only desired cheap stores, they could enter the following query: '=$'; if someone only sought stores with a rating greater than 4.5, they could enter: '>4.5'.

### Accessible Opportunities Counter
Located at the top-middle is a grid of four boxes that tracks the number of accessible opportunities by modality. Changes based on user interaction (e.g., subsetting individuals and/or stores) will subsequently change the number of accessible opportunities shown in the 'Physical', 'Virtual', and 'Hybrid' counters.
- *Total Food Stores* reflects the total number of food stores in and around the county.
- *Physical* reflects the total number of accessible food stores that all individuals shown can exclusively reach in person and not online.
- *Virtual* reflects the total number of accessible food stores that all individuals shown can exclusively reach online and not in person.
- *Hybrid* reflects the total number of accessible food stores that all individuals shown can reach either in person or online.

### Data
There are four datasets associated with this project:

1. Individuals and their socioeconomic, demographic, and perceived characteristics
2. Individuals and their travel trajectories over a two-day (Friday + Saturday) period
3. 2016-2020 5-Year ACS Estimates of variables related to food access and in the Centers for Disease Control and Prevention [(CDC)'s Social Vulnerability Index](https://www.atsdr.cdc.gov/placeandhealth/svi/index.html)
4. Food stores within and around (+10 miles beyond the border of) [Knox County](https://www.knoxcounty.org/)

The following `Data Tables Dictionary` section provides a description of each attribute in the tables while the `Methodology` section provides a description for how data were retrieved and processed.

### Data Tables Dictionary

##### Individuals
* Person ID: Unique ID for the individual
* Age: Age of the individual
* Sex: Sex of the individual
* Race/Ethnicity: Race/ethnicity of the individual
* Annual Income: Annual income of the individual
* Language: Spoken languages by the individual
* Dietary Preferences: Dietary preferences of the individual
* Digital Literacy: Whether the individual is 
digitally literate or not (yes/no)
* Job: Job of the individual
* Housing: Housing situation of the individual
* Household Size: Size of the household an individual lives in
* Kids at home: Number of kids in the household an individual lives in
* Marital Status: Marital status of the individual
* Travel Modes: Feasible travel modes for the individual
* Physical Disability: Any physical disabilities of the individual
* SNAP Benefits: Whether the individual has Supplemental Nutrition Assistance Program (SNAP) (formerly known as food stamps) benefits
* Cost Preference: Cost preference of the individual in accordance with the 1 to 4 $ rating system by Google
* Other Preferences: Any other preferences by the individual
* Physical Opportunities: Total number of potential physical food opportunities accessible by the individual
* Virtual Opportunities: Total number of potential virtual food opportunities accessible by the individual
* Hybrid Opportunities: Total number of potential hybrid (physical-virtual) food opportunities accessible by the individual

##### Food Stores

###### General Store Attributes
* Store Name: Name of place of interest (POI)
* Rating: Average user rating of POI
* Price: Price indication of items ranging from 1 to 4 dollar signs, suggested by Google
* Type: General POI type
* Specific Type: POI type by Google
###### Perceived Store Attributes
* Convenience: Average user rating for store convenience
* Checkout Process: Average user rating for checkout process
* Employees: Average user rating for employees
* Food Quality: Average user rating for quality of food
* Food Variety: Average user rating for variety of food
###### Service Options
* In-Store Shopping: Whether POI offers in-store shopping
* Online Shopping: Whether POI offers online shopping
* Delivery: Whether POI offers delivery
* Curbside Pickup: Whether POI offers curbside pickup
* Store Pickup: Whether POI offers in-store pickup
* Drive Thru: Whether POI offers drive-thru services
* No-Contact Delivery: Whether POI offers no-contact delivery
* Same-Day Delivery: Whether POI offers same-day delivery
###### Health and Safety
* Masks Required: Whether POI requires masks
###### Service
* Great Service: Whether POI has great service based on proprietary Google Maps algorithm 
###### Accessibility
* Wheelchair Accessible: Whether POI is wheelchair accessible
###### Offerings
* Good for Quick Visit: Whether POI is good for quick visits based on proprietary Google Maps algorithm
* Organic Food: Whether POI offers organic food
* Prepared Food: Whether POI offers prepared food
###### Payment Options
* Accepts Check: Whether POI accepts check as payment
* Accepts Debit Card: Whether POI accepts debit card as payment
* Accepts NFC Mobile Payment: Whether POI accepts NFC Mobile Payment
* Accepts SNAP/EBT: Whether POI accepts SNAP/EBT as payment
* Accepts Credit Card: Whether POI accepts credit card as payment
###### Amenities
* Restroom: Whether POI has restroom(s)
###### Atmosphere
* [LGBTQ+ Friendly](https://www.blog.google/outreach-initiatives/small-business/adding-lgbtq-friendly-and-transgender-safe-space-attributes-google-my-business/): Whether the POI owner has marked their POI as LGBTQ-friendly and/or a Transgender Safe Space
* Family Friendly: Whether the POI owner has marked their POI as family-friendly
###### Address Details
* Longitude: World Geodetic System 1984 (WGS84) Longitude of place of interest
* Latitude: WGS84 Latitude of place of interest
* Address: Address of place of interest
* [Plus Code](https://maps.google.com/pluscodes/): Unique identifiers for places around the world developed by Google

### Methodology

###### What tools are used?
* All data retrieval and processing were carried out with scripts and notebooks written in Python and R.
    * Python libraries: [dash](https://github.com/plotly/dash), [plotly](https://plotly.com/), [pandas](https://pandas.pydata.org/), [geopandas](https://geopandas.org/en/stable/), [beautifulsoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/), [selenium](https://selenium-python.readthedocs.io/), [nltk](https://www.nltk.org/), [gensim](https://radimrehurek.com/gensim/), [TextBlob](https://textblob.readthedocs.io/en/dev/quickstart.html), [urbanaccess](https://udst.github.io/urbanaccess/index.html), [osmnx](https://osmnx.readthedocs.io/en/stable/)
    * R libraries: [tidycensus](https://walker-data.com/tidycensus/)
* All front and backend web development and visualization were carried out with dash and plotly.
* The dash application is hosted with [Heroku](https://www.heroku.com/) with the [Heroku Buildpack Geo](https://github.com/heroku/heroku-geo-buildpack). 

###### How are the data derived? Where are the data collected from?
* [Code](https://github.com/jimmy-feng/Dissertation_App/blob/heroku/Code/Extract_Census.Rmd) Individuals, their socioeconomic, demographic, and perceived characteristics, and their trajectories were created by the researchers to represent the scenarios and lives of real-world individuals. Different scenarios were envisioned for residents in Knox County, Tennessee, with an emphasis on the lives of disadvantaged peoples, e.g., low-income, minorities, single parents, renters, and those without personal vehicles. We understand that these are not actual people but we tried to the best of our abilities to explicitly include the voices and situations of those who are especially marginalized in today's society and likely facing issues with accessing nutritious and healthy food(s) in today's society.
    * One spreadsheet contained each individual and their different characteristics.
    * Another spreadsheet contained information about their different locations over time.
* All 2016-2020 ACS 5-Year Estimates block-group data of various socioeconomic, demographic, and food access-related characteristics were retrieved with the [tidycensus](https://walker-data.com/tidycensus/) package.
* [Code](https://github.com/jimmy-feng/Dissertation_App/blob/heroku/Code/Google_Maps_POI_Retrieval_Cleaning.ipynb) All food stores were first retrieved from the [Google Maps Places API](https://developers.google.com/maps/documentation/places/web-service/overview). 
* [Code](https://github.com/jimmy-feng/Dissertation_App/blob/heroku/Code/Scrape_Google_Maps.py) Because the data offerred by the API is limited to just five reviews for each store and only a few attributes, an additional script was developed leveraging Selenium and BeautifulSoup to scrape additional reviews and business attributes not obtainable from the Places API.
    * [Code](https://github.com/jimmy-feng/Dissertation_App/blob/heroku/Code/Reviews_Analysis.ipynb) Aspect-based sentiment analysis of reviews was carried out in a two-step process to understand how people perceived specific characteristics related to food stores.
        1. Text preprocessing (stopwords removal, tokenization, lemmatization, etc.)
        2. Topic modelling with Latent Dirichlet Allocation (LDA); topics were identified based on lowest perplexity score, highest coherence value, and researcher's interpretations of the mixtures of words and their relative proportions in discovered topics
        3. Sentiment analysis of each topic; the polarity of each topic identified in each review was obtained using TextBlob and re-scaled between 1 to 5 in accordance with Google's rating system.
    * Overall, an LDA model resulting in 6 topics was considered optimal based on its relatively highest coherence value, low perplexity score, and ease of interpretation of the mixture of words. One topic, price, was omitted in the final table because there is already a price attribute. These five topics relate to different aspects of food stores people discussed in reviews.
        1. Convenience
        2. Checkout Process & Customer Service
        3. Employees
        4. Food Quality
        5. Food Variety
* [Code](https://github.com/jimmy-feng/Dissertation_App/blob/heroku/Code/OSM_Data_Retrieval.ipynb) Network analysis of individuals and their relative proximity (travel time) to all food opportunities was calculated at every point in their two-day trajectories. This was carried out with the [osmnx](https://osmnx.readthedocs.io/en/stable/) package.

###### How are food opportunities classified?
* Google Maps provides a unique type for each POI but for simplicity's sake, we re-classified (aggregated) each food-related POI according to a manual classification scheme as follows based on the nomenclature adopted by Google, and manual ground-truthing of stores based on our knowledge of the retail food landscape in Knox County. In total, there are seven classes of food stores; the left-hand side are the classes in our GIS while the right-hand side contains the POI types of all stores scraped from Google Maps:
    * Ethnic grocery store = Asian grocery store, Cafe, Gourmet grocery store, Mexican grocery store, Mexican restaurant (e.g., Chinese supermarkets)
    * Specialty food store = Butcher Shop, Furniture store, Lunch restaurant, Produce market (e.g., farmer's markets, butcher shops)
    * Discount store = Dollar store, Discount supermarket (e.g., dollar stores such as Dollar Tree)
    * Convenience store = Gas station, Market, Store (e.g., gas stations, convenience stores, bodegas such as Weigels)
    * Grocery store = Health food store, Supermarket (e.g., supermarkets, grocery stores such as Kroger)
    * Warehouse store = Warehouse club (e.g., bulk retailers such as Costco)
    * Department store = Department store (e.g., Walmart, Target)
    
###### How are physical, virtual, and hybrid opportunities distinguished?
* Food opportunities can be reached in-person, online, or by both modalities; these are referred to as, respectively, 'physical', 'virtual', and 'hybrid' opportunities.
* [Code](https://github.com/jimmy-feng/Dissertation_App/blob/heroku/Dashboard.py) - Lines 541-618. For each individual, given the start of their discretionary time period(s), and for each potential opportunity, if the time required to travel to a potential opportunity AND the time required to participate in food shopping by their preferred modality AND the time required to travel to the location of their next fixed period is equal to or less than their total discretionary time, then the opportunity is physically accessible. If the person is also digitally literate (i.e, able and willing to order food online) and the store offers online services (e.g., delivery), then, the store can also be reached online and thus, the opportunity is considered as a hybrid opportunity. In other words:
    * If a person can only reach the store physically but is not digitally literate and/or not willing to buy food online, the store is a physical opportunity.
    * If a person cannot reach the store physically (e.g., not enough time and/or not willing to buy food in-person) but is willing and able to buy food online, the store is a virtual opportunity.
    * If a person can both reach the store physically and online, the store is a hybrid opportunity.
    * Otherwise, if a person cannot reach the store in person nor online, the store is not considered an accessible opportunity.
    * The counters at the top-middle of the GIS application reflect the opportunities of all activated/shown individuals.
* [Code](https://github.com/jimmy-feng/Dissertation_App/blob/heroku/Code/Process_Scenarios_Nonfixed_Times.ipynb) Discretionary time periods were identified and calculated based on a person's daily activities -- work, sleep, school, and other similar activities are mandatory while working out, shopping, etc., are discretionary activities.