import os
import sys
import json
import urllib
import urllib2

api_key = os.getenv("MAPS_API_KEY")
if api_key == "":
    sys.exit("Please obtain an API key from https://developers.google.com/maps/documentation/geocoding/start#get-a-key and set the environment variable MAPS_API_KEY")

#print api_key

url = 'https://maps.googleapis.com/maps/api/geocode/json?'
values = {'address' : 'Campbell Hall',
          'key' : api_key }

data = urllib.urlencode(values)
full_url = url + data
print full_url
response = urllib2.urlopen(full_url)
json_response = response.read()

data_dict = json.loads(json_response)

#print data_dict

lat = data_dict['results'][0]['geometry']['location']['lat']
lng = data_dict['results'][0]['geometry']['location']['lng']

print lat, lng
