import logging
from HereApi import HereApi
import requests
import json
import pprint
import pandas as pd
import re
import itertools

from db.Database import Database

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
        response = requests.get(f'{NominatimApi.interp_url}{query}')
        data = json.loads(response.text)
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
                '&osmid=' + str(loc_type['osm_id'])).text)

            if loc_type['category'] == 'boundary':
                preferred_boundaries.append({'data': loc_type, 'weight': loc_weights[loc_type['type'] + '_' + str(add_data['rank_address'])]})
            elif loc_type['type'] == 'city' or loc_type['type'] == 'village':
                preferred_boundaries.append({'data': loc_type, 'weight': 999})
                #TODO: Define bounds for a city
                
        # Sort by preference (weights)
        preferred_boundaries = [pb['data'] for pb in sorted(preferred_boundaries, key=lambda d: d['weight'])]
        
        # Swap coordinates to a more useful way for the other APIs (long, lat)(long, lat)
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

class Ratings:
    @staticmethod
    def get_rating(name: str, location: str) -> float:
        db = Database()
        
        if not db.is_table_empty('RESTAURANT'):
            # TODO: This location name must be something fixed for certain coordinates
            # For now location=Lisboa and location=Lisbon are different db tables
            local_record = db.get_restaurant_by_name(name, location)
            
            if local_record:
                logging.info(f'Found {name} in local database, returning.')
                return local_record[0][3]
        
        pname = name.replace(' ', '+')
        location = location.replace(' ', '+')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36 OPR/87.0.4390.45'
        }
        ddg_url = f'https://html.duckduckgo.com/html/?q={pname}+{location}+tripadvisor'
        r = requests.get(ddg_url, headers=headers)
        
        # Go to first available site in the search
        found_indices = [m.start() - 3 for m in re.finditer('class=\"result__url\"', r.text)]
        
        # Search only top three urls
        for idx in found_indices[:3]:
            data = r.text[idx:idx+1024].replace('\n', '')
            place_tripadvisor_url = ''
            match = re.search(r'>(.*.html)', data)
            if match:
                place_tripadvisor_url = ''.join(itertools.takewhile(lambda x: x!="<", match.group(1).lstrip()))
                url_dir_list = place_tripadvisor_url.split('/')
                
                if len(url_dir_list) < 2:
                    logging.error(f'Not Found (Skipping): {place_tripadvisor_url}')
                    continue
                
                url_directory = place_tripadvisor_url.split('/')[1]
                
                if place_tripadvisor_url.find('tripadvisor') != -1 and place_tripadvisor_url.find('Restaurant_Review') != -1:
                    # Always bypass to .com domain
                    place_tripadvisor_url = f'www.tripadvisor.com/{url_directory}'
                    logging.info(f'Found: {place_tripadvisor_url}')
                    r = requests.get(f'https://{place_tripadvisor_url}', headers=headers)
                    
                    REVIEW_STR = '<h2>Ratings and reviews</h2>'
                    rating_idx = r.text.find(REVIEW_STR) + 67
                    
                    # We found a rating, return
                    rating_text = r.text[rating_idx:rating_idx+3]
                    
                    if rating_text == ' fo':
                        # There are new reviews in the page yet
                        return -1.0
                    
                    rating = float(rating_text)
                    db.add_restaurant_entry(name, location, rating, -1)
                    return rating
                
                # Keep searching the list
                logging.warning(f'Not Found (Skipping): {place_tripadvisor_url}')
        
        return -1.0

logging.basicConfig(level=logging.INFO)
best_cadidate = NominatimApi.get_area('Lisboa')[0]
df = OverpassApi.get_type_in_bounds(best_cadidate['boundingbox'], ltypes=['tourism', 'amenity=restaurant'])
location = df.loc[
    df['tags_name'].notnull() &
    df['tags_amenity'].str.contains('restaurant', case=False, na=False)]

for i, tar in enumerate(location.iloc):
    if i > 50: break
    
    tripadvisor_rating = Ratings.get_rating(tar['tags_name'], 'Lisboa')
    logging.info(f'Fetched rating: {tripadvisor_rating}')


