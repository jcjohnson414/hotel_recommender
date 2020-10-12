import streamlit as st
import pandas as pd
pd.set_option('display.max_colwidth', None)
import numpy as np

import en_core_web_lg
from spacy.lang.en import English
from spacy.lang.en.stop_words import STOP_WORDS

from sklearn.metrics.pairwise import cosine_similarity

from geopy import distance
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
nlp = en_core_web_lg.load()

import textwrap
import plotly.express as px
import plotly.offline as pyo
import plotly.graph_objs as go

st.title("Let's Find You a Hotel")


# st.text("""Enter a description of your upcoming trip. Will it be business or
# leisure? Where will you go? How will you get there(plane, train, automobile)?
# Who will you travel with? Where will you visit, such as businesses, offices,
# museums, universites, arenas/stadiums, beaches, historical sites?""")

@st.cache
def load_data(str):
    start = "start"
    data = pd.read_csv('../Data/data_with_geocodes.csv')
    data = data.drop(columns=['Unnamed: 0', 'Unnamed: 0.1'])
    # data['rating'] = data['rating'].replace({'New Hotel' : 6})
    return data

# st.write(data)

def text_input(text):
    if text == '':
        text = ' '
    return text

user_input = text_input(st.text_input("""Enter a description of your upcoming trip. Will it be business or
leisure? Where will you go? How will you get there(plane, train, automobile)?
Who will you travel with? Where will you visit, such as businesses, offices,
museums, universites, arenas/stadiums, beaches, historical sites?"""))

city_input = text_input(st.text_input("Enter your city here"))

state_input = st.selectbox('Select your state here', ('AL', 'AK', 'AZ', 'AR', 'CA',
'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA',
'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NY', 'NJ', 'NM', 'NY',
'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA',
'WA', 'WV', 'WI', 51))

radius_input = st.selectbox('Select your radius here, in KM', ('5', '10', '15',
'20', '25', '50', '100'))

cat_input = st.multiselect('What are your the types of hotels you prefer?',
['Luxury', 'Vacation Club Condos', 'Boutique Lifestyle', 'Full-Service Upper-Scale',
'Full-Service Mid-Scale', 'Full-Service Entry', 'Extended-Stay All-Suites',
'Limited-Service Mid-Scale', 'Budget'])

rewards_input = st.multiselect('Are you a member of any hotel loyalty programs?',
['Hilton', 'Hyatt', 'IHG', 'Marriott', 'Radisson', 'Wyndham'])
# st.write('You selected:', rew_input)

rate_input = st.selectbox('Select your minimum guest rating', (5, 4.5, 4, 3.5,
3, 2.5, 2, 1.5, 1, .5, 0))
# st.write('You selected:', rate_input)

# function to convert user input into a geocode
# loosely based off of https://stackoverflow.com/questions/42686300/how-to-check-if-coordinate-inside-certain-area-python

def get_user_geo(city_input, state_input):
    locator = Nominatim(user_agent="myGeocoder")
    location = city_input + ', ' + state_input
    locationcode = locator.geocode(location)
    location = {}
    location['latitude'] = locationcode.latitude
    location['longitude'] = locationcode.longitude
    user_geocode = tuple(location.values())
    return user_geocode

# function to compare the distance of the hotel geocode against the geocode for user input and return only hotels
# in a certain radius
# loosely based off of https://stackoverflow.com/questions/42686300/how-to-check-if-coordinate-inside-certain-area-python

def get_radius_hotels(userinput, df, user_radius):
    locator = Nominatim(user_agent="myGeocoder")
    radiushotels = []
    radius = int(user_radius)
    for index, row in data.iterrows():
        geocode = tuple([row['latitude'], row['longitude']])
        try:
            dis = distance.distance(userinput, geocode).km
            if dis <= radius:
                radiushotels.append(row)
            else:
                pass
        except:
            pass
    newdata = pd.DataFrame(radiushotels)
    return newdata

# function to filter based on category input from user

def trim_cat(userinput, df):
    # catlist = userinput.split(',')
    userinput = [x.strip() for x in userinput]
    newcats= []
    notmet = []
    for index, row in df.iterrows():
        category = row['category']
        # category = category.split(' ')
        # for x in category:
            # x = x.replace(',','').strip()
        if category in userinput:
            newcats.append(row)
        else:
            notmet.append(row)
    newcats_df = pd.DataFrame(newcats)
    newcats_df = newcats_df.drop_duplicates()
    notmet_df = pd.DataFrame(notmet)
    notmet_df = notmet_df.drop_duplicates()
    return newcats_df, notmet_df

# function to filter based on rating input from user

def trim_rating(userinput, df1, df2):
    for x in df1['rating']:
        df1['rating'] = [float(x) for x in df1['rating']]
    for x in df2['rating']:
        df2['rating'] = [float(x) for x in df2['rating']]
    data2 = df1[(df1['rating'] >= float(userinput))]
    lowerrating = float(userinput) - .6
    notmet_df = df2[(df2['rating']>= lowerrating)]
    return data2, notmet_df

# function to filter based on rewards program input from user

def trim_rewards(userinput, df1, df2):
    # rewardslist = userinput.split(',')
    # rewardslist = [x.strip() for x in rewardslist]
    newrewards= []
    newrewards1 = []
    try:
        for index, row in df1.iterrows():
            rewards = row['rewards']
            # rewards = rewards.split(',')
            # for x in rewards:
            if rewards in userinput:
                newrewards.append(row)
            else:
                newrewards1.append(row)

        notmet_df = df2
        if len(newrewards) > 1:
            return pd.DataFrame(newrewards), notmet_df
        else:
            return pd.DataFrame(newrewards1), notmet_df
    except:
        return df1, df2

# function to create a spacydocs from a concatonated string of features. Then create the vectors for the spacydoc for each hotel

def create_spacydocs(df1, df2):
    bagofwords = []
    columns = ['rewards', 'brand', 'description', 'city', 'category']
    for index, row in df1.iterrows():
        words = ''
        bagofwordsdict = {}
        for col in columns:
            words += ''.join(row[col]) + ' '
        bagofwordsdict['name'] = row['name']
        bagofwordsdict['Bag_of_words'] = words
        bagofwords.append(bagofwordsdict)
    bagofwords_df = pd.DataFrame(bagofwords)

    spacydocs = []
    for index, row in bagofwords_df.iterrows():
        x = row['Bag_of_words']
        spacydocsdict = {}
        spacydocsdict['name'] = row['name']
        spacydocsdict['spacydocs'] = nlp(x)
        spacydocs.append(spacydocsdict)
    spacydocs_df = pd.DataFrame(spacydocs)

    vectorlist = []
    for index, row in spacydocs_df.iterrows():
        doc = row['spacydocs']
        vectordict = {}
        vectordict['name'] = row['name']
        vectordict['vector'] = doc.vector
        vectorlist.append(vectordict)
    vectorlist_df = pd.DataFrame(vectorlist)

    newdata = pd.merge(df1, vectorlist_df, on='name')
# -----------------------------------------------------------------------
    bagofwords2 = []
    columns = ['rewards', 'brand', 'description', 'city', 'category']
    for index, row in df2.iterrows():
        words = ''
        bagofwordsdict = {}
        for col in columns:
            words += ''.join(row[col]) + ' '
        bagofwordsdict['name'] = row['name']
        bagofwordsdict['Bag_of_words'] = words
        bagofwords2.append(bagofwordsdict)
    bagofwords_df2 = pd.DataFrame(bagofwords2)

    spacydocs2 = []
    for index, row in bagofwords_df2.iterrows():
        x = row['Bag_of_words']
        spacydocsdict = {}
        spacydocsdict['name'] = row['name']
        spacydocsdict['spacydocs'] = nlp(x)
        spacydocs2.append(spacydocsdict)
    spacydocs_df2 = pd.DataFrame(spacydocs2)

    vectorlist2 = []
    for index, row in spacydocs_df2.iterrows():
        doc = row['spacydocs']
        vectordict = {}
        vectordict['name'] = row['name']
        vectordict['vector'] = doc.vector
        vectorlist2.append(vectordict)
    vectorlist_df2 = pd.DataFrame(vectorlist2)

    notmet_df = pd.merge(df2, vectorlist_df2, on='name')
    return newdata, notmet_df

# function to take in the user input description of their trip and convert to spacydocs and create vectors.
# then perform cosine similarity between the user input and each of the hotels in the filtered dataset,
# and return the top 10 results

def similarity(user_input, df1, df2):

    # convert user input to spacydoc and create vectors
    doc = nlp(user_input)
    doc = doc.vector

    # Calculate similarity with each hotel and create dicitonary of similarities and sentiments
    similarity_list = []
    for index, row in df1.iterrows():
        similarity  = {}
        vector = row['vector']
        sim = doc
        similarity['name'] = row['name']
        similarity['similarity'] = cosine_similarity(vector.reshape(1,-1), sim.reshape(1,-1))[0][0]
        similarity['rating'] = row['rating']
        similarity['category'] = row['category']
        similarity['address'] = row['address_x']
        similarity['url'] = row['url']
        similarity['latitude'] = row['latitude']
        similarity['longitude'] = row['longitude']
        similarity_list.append(similarity)
    similarities = pd.DataFrame(similarity_list)

    similarity_list2 = []
    for index, row in df2.iterrows():
        similarity  = {}
        vector = row['vector']
        sim = doc
        similarity['name'] = row['name']
        similarity['rating'] = row['rating']
        similarity['category'] = row['category']
        similarity['address'] = row['address_x']
        similarity['url'] = row['url']
        similarity['latitude'] = row['latitude']
        similarity['longitude'] = row['longitude']
        similarity['similarity'] = cosine_similarity(vector.reshape(1,-1), sim.reshape(1,-1))[0][0]
        similarity_list2.append(similarity)
    similarities2 = pd.DataFrame(similarity_list2)

    similarities = similarities.sort_values(by='similarity', ascending=False)
    similarities2 = similarities2.sort_values(by='similarity', ascending=False)
    final_output = pd.concat([similarities, similarities2])[:20]

    return similarities, similarities2

# function that combines all of the functions to produce top ten recommended hotels

def hotelfilter(city_input, state_input, radius_input, cat_input, rate_input, rewards_input, user_input):
    userlocation = get_user_geo(city_input, state_input)
    radiushotels = get_radius_hotels(userlocation, data, radius_input)
    cathotels, notmet_df = trim_cat(cat_input, radiushotels)
    ratinghotels, notmet_df = trim_rating(rate_input, cathotels, notmet_df)
    rewardshotels, notmet_df = trim_rewards(rewards_input, ratinghotels, notmet_df)
    filtereddata, notmet_df = create_spacydocs(rewardshotels, notmet_df)
    recommendations = similarity(user_input, filtereddata, notmet_df)
    return recommendations

def map_hotels(input):
    fig = px.scatter_mapbox(input, lat = 'latitude', lon = 'longitude',
        color_discrete_sequence = ['navy'],hover_data = ['name', 'address', 'url'],
         zoom = 10, height = 500)
    fig.update_layout(mapbox_style = 'open-street-map')
    fig.update_layout(margin = {'r': 0, 't': 0, 'l': 0, 'b':0})
    # pyo.iplot(fig)
    return fig

data_load_state = st.text('Loading data...')
data = load_data('start')
data_load_state.text("Done! (using st.cache)")
# st.write(data)

recommendations, recommendations2 = hotelfilter(city_input, state_input, radius_input, cat_input, rate_input, rewards_input, user_input)
# st.write(recommendations['name', 'similarity', 'url'])
slimrec = recommendations[['name', 'similarity', 'url']]
slimrec2 = recommendations2[['name', 'similarity', 'url']]

st.write(slimrec)

# def print_results(input):
#     for index, row in input.iterrows():
#         name = row['name']
#         score = row['similarity']
#         website = row['url']
#         print(name)
#
# results = print_results(recommendations)
# st.write(results)

# def make_clickable(link):
#     # target _blank to open new window
#     # extract clickable text to display for your link
#     text = link
#     return f'<a target="_blank" href="{link}"{text}></a>'
#
# # link is the column with hyperlinks
# recommendations['url'] = recommendations['url'].apply(make_clickable)
# recommendations = recommendations.to_html(escape=False)
# st.write(recommendations, unsafe_allow_html=True)

# st.write(recommendations.to_html(escape=False, index=False), unsafe_allow_html=True)


map = map_hotels(recommendations)
st.write(map)

# userlocation = get_user_geo(city_input, state_input)
# radiushotels = get_radius_hotels(userlocation, data, radius_input)
# cathotels, notmet_df = trim_cat(cat_input, radiushotels)
# st.write(cathotels)

st.write("These hotels don't match your filters, but do have a high matching score")

if len(recommendations) < 20:
    st.write(slimrec2)
