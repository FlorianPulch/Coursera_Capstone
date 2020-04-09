import requests
from bs4 import BeautifulSoup

website_url = requests.get(
    'https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M').text
soup = BeautifulSoup(website_url, 'lxml')

print(soup.prettify())

my_table = soup.find('table', {'class': 'wikitable'})
print(my_table)

row_entries = my_table.findAll('tr')
print(row_entries)
postal_code = []
borough = []
neighborhood = []

for item in row_entries:
    column_entries = item.findAll('td')
    if column_entries:
        postal_code.append(column_entries[0].text)
        borough.append(column_entries[1].text)
        neighborhood.append(column_entries[2].text)
