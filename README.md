# Hotel Recommendation System

## Problem Statement

Most hotel aggregating websites, known as Online Travel Agents rely on the user to type in the destination and tehn scroll through all of the hotel options provided. The user can filter their searches with various parameters, but there is currently no mainstream service in place that allows for the user to provide a description of their trip. By having a user provide input in the form of a text description of their trip, the system will perform NLP on the user input and compare the input against the descriptions provided on hotel websites. The system will find the most similar pairs between the user input and the hotels the system will provide top recommendations for potential guests.

## Data Collection

To complete the project had to collect data from websites for various hotel brands. In this case neither of the major hotel companies have API's to assist in this process, with this in mind I would need to build from scratch code that would crawl the internet and scrape the data needed from each hotel website. For this project I utilized Selenium and Beautiful Soup to complete this process. For each hotel I collected the Name, hotel url, address, tripadvisor rating, geocoordinates. Ultimately data was collected from the following hotel companies and their respective brands for a total of over 21,000 hotel properties in the United states:

- Hilton Hotels
- Hyatt Hotels
- IHG Hotels
- Marriott Hotels
- Radisson Hotels
- Wyndham Hotels

Most of the hotel brands followed a similar template for their hotel websites, however there where a significant number of brands that had different templates in use. This resulted in creating over 10 different web scraping codes to collect the data. The majority of the sites I was able to utilize requests plus BeautifulSoup to navigate through all of the hotels, however with Marriott and Wyndham I needed to incorporate Selenium to utilize Selenium's automated web manipulation tools such as scrolling, clicking buttons, and navigating back to the main page to go to the next hotel. 

## Data Cleaning

As part of my collection process each of the hotel brands were collected seperatedly since the output of the webscraping was different for each brand this made it easier to conduct data cleaning. For example some of the brands were unable to collect geocoordinates, while others collected the text descriptions in a manner which needed to be cleaned. For each brand's web scraping I implemented various forms of cleaning into the webscraping. For example as part of collecting the text description, I included removing non ASCII characters, and striping white spaces from the description. Once I had each of the six hotel companies portfolio collected into their on dataframe, I then applied labeling to the data to assign the Brand Name, Category Class, Rewards Program, and Hotel Category to each hotel.

During the data collection process the single component that I was not able to collect for most hotels was the tripadvisor rating. With this in mind I created a dataframe for each brand that collected the hotels which were unable to collect the tripadvisor ratings. With this dataframe I maanually went through tripadvisor to collect the ratings. Once collected I then combined all of the dataframes together for the next step. As previously mentioned many of the hotel brands were not able to accurately scrape the geocoordinates, the decision was made to remove this feature from the orginal dataframes that were collected. Once the final dataframe was pieced together we then create a function to collect the geocoordinates from Geopy by feeding the concatonated address to Geopy. We returned the geocoordinates to the respective columns of latitude and longitude to later be used for the purposes of filtering by location and plotting recommendations on a map for users.

## Processing

The final piece of the puzzle for the recommnender was to perform NLP on the text descriptions for each hotel. For this I utilized spaCy, which is a free library for advanced NLP that has been found to be the fastest in the world. With spaCy I used the en_core_web_lg model of over 685,000 unique vectors to conduct NLP on the dataset. Prior to using spaCy I combined the following features into one feature called Bag of Words; Brand, Name, City, Description, and City. With this new feature I created a spaCy doc for each Bag of Words. This spaCy doc function tokenizes each word and also assigns Part of Speech tags, lemmas (origins of the word), and dependancies based on the part of speech. For the purposes of this project these features were not used but can be considered for future steps. Once the spaCy Docs have been created for each hotel, then the vectors for the words are created. We store these vectors in a column of the dataframe to be used later to compare against the vectors of user input to our recommender system. For the purposes of learning and potential future steps, we decided to gather the sentiment of each of the hotel descriptions and store them in the dataframe as well. Since these descriptions are created by the hotels, it is not surprising that the majority of the hotels have a positive sentiment score, however for the purposes of recommending hotels it is not useful to use the sentiment at this time.

Now we have a finished cleaning and processing our data we have a dataset which consists of Rewards System, Brand, Hotel Name, Street Address, City, State, Zip Code, URL, Class Ranking, TripAdvisor Rating, Category, spaCy docs, vectors, sentiment score, and geocoordinates. We can now build out our recommender.

## Recommender System

The recommender system allows the user to select:
- any rewards systems they are a member of
- any cateogry of hotel they are interested in
- a minimum star rating from tripadvisor
- City, State of trip
- Brief description of their trip

The first paramaters are used to filter the dataset to appropriate choices, and then the system converts the user input into a spaCy doc to perform the same NLP steps used on our dataset. Ultimately creating vectors to compare against the dataset. The recommender returns the 10 highest ranked hotels based on the cosine similarity between the user input and the hotel dataset.

## Future Development
