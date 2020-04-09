import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as colors
from sklearn.cluster import KMeans
import folium as folium
import numpy as np

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
df['Neighborhood'] = neighborhood_clean

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


attractions = getNearbyVenues(names=toronto_only['Neighborhood'],
                              latitudes=toronto_only['Latitude'], longitudes=toronto_only['Longitude'])
attractions.head()


Toronto_encoded = pd.get_dummies(
    attractions[['Venue Category']], prefix="", prefix_sep="")

Toronto_encoded['Neighborhood'] = attractions['Neighborhood']

fixed_columns = [Toronto_encoded.columns[-1]] + \
    list(Toronto_encoded.columns[:-1])
Toronto_encoded = Toronto_encoded[fixed_columns]

Toronto_grouped = Toronto_encoded.groupby('Neighborhood').mean().reset_index()

Toronto_grouped.head()

kclusters = 5

toronto_grouped_clustering = Toronto_grouped.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(
    toronto_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10]


num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

Toronto_grouped.head()

# create a new dataframe
neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighborhood'] = Toronto_grouped['Neighborhood']

for ind in np.arange(Toronto_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(
        Toronto_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()


def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)

    return row_categories_sorted.index.values[0:num_top_venues]


neighborhoods_venues_sorted.insert(0, 'Cluster Labels', kmeans.labels_)

toronto_merged = toronto_only

neighborhoods_venues_sorted.head()
toronto_merged.head()
toronto_merged['Cluster Labels']


# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
toronto_merged = toronto_merged.join(
    neighborhoods_venues_sorted.set_index('Neighborhood'), on='Neighborhood')

toronto_merged.head()  # check the last columns!

toronto_merged['Cluster Labels']

toronto_merged = toronto_merged[toronto_merged['Cluster Labels'].isna(
) == False]

latitude = 43.653963
longitude = -79.387207

map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)


# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

toronto_merged.head()

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(toronto_merged['Latitude'], toronto_merged['Longitude'], toronto_merged['Neighborhood'], toronto_merged['Cluster Labels']):
    label = folium.Popup(str(poi) + ' Cluster ' +
                         str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[cluster-1],
        fill=True,
        fill_color=rainbow[cluster-1],
        fill_opacity=0.7).add_to(map_clusters)

map_clusters
