from array import array
import logging
from HereApi import HereApi
import requests
import json
import pprint
import pandas as pd

class MapPlace(HereApi):
    def __init__(self):
        super(MapPlace, self).__init__()
        self.base_url = 'https://places.ls.hereapi.com/places/v1/discover/here'
        
    def get_all_places_near(self, coords: list):
        try:
            res = self.get(at=f'{coords[0]},{coords[1]}')
            places = json.loads(res.text)['results']['items']
            pprint.pprint(json.loads(res.text))
            # pprint.pprint([p['title'] for p in places])
            # pprint.pprint(places[4])
        except ValueError:
            return None

class NominatimApi:
    interp_url = 'https://nominatim.openstreetmap.org/search.php?format=jsonv2&q='
    add_data_url = 'https://nominatim.openstreetmap.org/details.php?format=json&'
    
    @staticmethod
    def get_area(location: str) -> list:
        '''
        Parameters:
                location (str): The location to geolocate
        Returns:
                preferred_boundaries (list): Ordered list from most preferred to least preferred matched bondary types
        '''
        
        # Replace whitespaces from the query string
        query = location.replace(' ', '+')
        res = requests.get(f'{NominatimApi.interp_url}{query}')
        data = json.loads(res.text)
        # pprint.pprint(data)
        
        preferred_boundaries = []
        
        # Concatenated data from https://nominatim.openstreetmap.org responses
        loc_weights = {
            'historic_0': 0, # Historic Center Only
            'administrative_16': 1, # Entire City Municipality
            'administrative_18': 2, # Entire County
            'administrative_12': 3, # Entire District
        }
        
        logging.info(f'Geolocating {location}...')
        
        # Try and get a boundary (or a city / village / if a boundary is not available)
        for loc_type in data:
            # Get additional data for each place
            tgt_id = loc_type['osm_id']
            logging.info(f'Getting additional data for found target id {tgt_id}...')
            add_data = json.loads(requests.get(
                NominatimApi.add_data_url + 
                'osmtype=' + loc_type['osm_type'][0].upper() + 
                '&osmid=' + str(loc_type['osm_id'])).text
                )
            if loc_type['category'] == 'boundary':
                preferred_boundaries.append({'data': loc_type, 'weight': loc_weights[loc_type['type'] + '_' + str(add_data['rank_address'])]})
            elif loc_type['type'] == 'city' or loc_type['type'] == 'village':
                preferred_boundaries.append({'data': loc_type, 'weight': 999})
                #TODO: Define bounds for a city
                
        # Sort by preference (weights)
        preferred_boundaries = [pb['data'] for pb in sorted(preferred_boundaries, key=lambda d: d['weight'])]
        
        # Swap coordinates to a more usefull way for the other APIs
        for i in range(len(preferred_boundaries)):
            preferred_boundaries[i]['boundingbox'][1], preferred_boundaries[i]['boundingbox'][2] = preferred_boundaries[i]['boundingbox'][2], preferred_boundaries[i]['boundingbox'][1]
        
        logging.info(f'Found {len(preferred_boundaries)} eligible candidates for keyword: {location}')
        return preferred_boundaries
        
class OverpassApi:
    interp_url = 'http://www.overpass-api.de/api/interpreter?data='
    
    @staticmethod
    def get_type_in_bounds(bounds: list, ltypes: list = ['tourism'], timeout: int = 30):
        '''
        Parameters:
                bounds (list): The location coordinates span
                ltypes (list): The types of POIs to find as 'keys' or 'keys=value' strings
                timeout (int): API timeout getting the data
        Returns:
                data (pd.DataFrame): Pandas dataframe with all of the nodes/relations containing ltypes
        '''
        # Find all tourist attractions in bounds
        q = '('
        for i in ltypes:
            if '=' not in i:
                q += f'node[\"{i}\"](' + ','.join(bounds) + ');'
            else:
                spl = i.split('=')
                q += f'node[\"{spl[0]}\"=\"{spl[1]}\"](' + ','.join(bounds) + ');'
        q += ');'
        
        query = f'[out:json][timeout:{timeout}];{q}out;'
        data = json.loads(requests.get(f'{OverpassApi.interp_url}{query}').text)
        elmnts = data['elements']
        logging.info(f'Found {len(elmnts)} elements for types: {ltypes}')
        return pd.json_normalize(elmnts, sep='_')

class GeocodePoint(HereApi):
    def __init__(self):
        super(GeocodePoint, self).__init__()
        self.base_url = 'https://geocoder.ls.hereapi.com/6.2/geocode.json'
    
    def get_coords(self, location: str) -> list:
        location = location.replace(' ', '+')
        try:
            res = self.get(searchtext=location)
            coords = json.loads(res.text)['Response']['View'][0]['Result'][0]['Location']['DisplayPosition']
            return [coords['Latitude'], coords['Longitude']]
        except ValueError:
            return None

logging.basicConfig(level=logging.INFO)
best_cadidate = NominatimApi.get_area('Lisboa')[0]
df = OverpassApi.get_type_in_bounds(best_cadidate['boundingbox'], ltypes=['tourism', 'amenity=restaurant'])
# df.to_csv('data.csv', sep=',', encoding='utf-8')
df.to_csv('data.csv', sep=',')
