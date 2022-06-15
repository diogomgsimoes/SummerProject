from array import array
import logging
from HereApi import HereApi
import json
import pprint

class Geocode(HereApi):
    def __init__(self):
        super(Geocode, self).__init__()
        self.base_url = 'https://geocoder.ls.hereapi.com/6.2/geocode.json'
    
    def get_coords(self, location: str) -> list:
        location = location.replace(' ', '+')
        try:
            res = self.get(searchtext=location)
            coords = json.loads(res.text)["Response"]["View"][0]["Result"][0]["Location"]["DisplayPosition"]
            return [coords["Latitude"], coords["Longitude"]]
        except ValueError:
            return None

class MapPlace(HereApi):
    def __init__(self):
        super(MapPlace, self).__init__()
        self.base_url = 'https://places.ls.hereapi.com/places/v1/discover/here'
        
    def get_all_places_near(self, coords: list):
        try:
            res = self.get(at=f'{coords[0]},{coords[1]}')
            places = json.loads(res.text)["results"]["items"]
            pprint.pprint(json.loads(res.text))
            # pprint.pprint([p["title"] for p in places])
            # pprint.pprint(places[4])
        except ValueError:
            return None

geo = Geocode()
place = MapPlace()

rome_coords = geo.get_coords('Faro')
print(rome_coords)
place.get_all_places_near(rome_coords)

