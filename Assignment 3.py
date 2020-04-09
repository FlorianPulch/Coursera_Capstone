import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as colors
from sklearn.cluster import KMeans
import folium

website_url = requests.get(
    'https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M').text
soup = BeautifulSoup(website_url, 'lxml')

my_table = soup.find('table', {'class': 'wikitable'})
row_entries = my_table.findAll('tr')


postal_code = []
borough = []
neighborhood = []

for item in row_entries:
    column_entries = item.findAll('td')
    if column_entries:
        postal_code.append(column_entries[0].text)
        borough.append(column_entries[1].text)
        neighborhood.append(column_entries[2].text)

postal_code_clean = [item.replace('\n', '') for item in postal_code]
borough_clean = [item.replace('\n', '') for item in borough]
neighborhood_clean = [item.replace('\n', '') for item in neighborhood]

df = pd.DataFrame()
df['postal_code'] = postal_code_clean
df['borough'] = borough_clean
df['neighborhood'] = neighborhood_clean

df_final = df[df['borough'] != 'Not assigned']
df_final.shape

geo_location_data = pd.read_csv(
    r'C:\Users\flpulch\OneDrive - Deloitte (O365D)\Desktop\Geospatial_Coordinates.csv')

df_final = df_final.merge(geo_location_data, how='left',
                          left_on='postal_code', right_on='postcode')


toronto_only = df_final[df_final['borough'].str.contains("Toronto")]


CLIENT_ID = '3RKHIO3RVWOF1O1HJOXHQ5OO5YHBMWE2JHBMRAQ05JOVFZE2'
CLIENT_SECRET = '4UGGZNKNWJNNHQVWOBTHZZIZ1NFTIYKMQ1J2IKTQGB53OPYA'
LIMIT = 100
VERSION = '20190303'


def getNearbyVenues(names, latitudes, longitudes, radius=500):

    venues_list = []
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)

        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID,
            CLIENT_SECRET,
            VERSION,
            lat,
            lng,
            radius,
            LIMIT)

        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']

        # return only relevant information for each nearby venue
        venues_list.append([(
            name,
            lat,
            lng,
            v['venue']['name'],
            v['venue']['location']['lat'],
            v['venue']['location']['lng'],
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame(
        [item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood',
                             'Neighborhood Latitude',
                             'Neighborhood Longitude',
                             'Venue',
                             'Venue Latitude',
                             'Venue Longitude',
                             'Venue Category']

    return(nearby_venues)


attractions = getNearbyVenues(names=toronto_only['neighborhood'],
                              latitudes=toronto_only['Latitude'], longitudes=toronto_only['Longitude'])
attractions.head()
