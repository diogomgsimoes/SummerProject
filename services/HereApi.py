import os
import logging
from dotenv import load_dotenv
import requests
import random

ENV_VAR_NAME = 'HERE_API_KEY'

class HereApi:
    def __init__(self):
        self.KEY = ''
        self.base_url = ''
        
        # Load the .env file with local environment variables
        self._load_keys()
        
    def get(self, *args, **kwargs) -> requests.Response:
        if not self.base_url:
            raise ValueError('HereApi contains no base url.')
            
        url = self.base_url
        
        for a in args:
            url += f'/{a}'
        
        url += '?'
        for k, v in kwargs.items():
            url += f'{k}={v}&'
        
        url += f'apiKey={self.KEY}'
        
        return requests.get(url)
    
    def _load_keys(self):
        load_dotenv()
        api_key = os.getenv(ENV_VAR_NAME)
        if api_key == None:
            logging.error(f'Could not find a API key named \'{ENV_VAR_NAME}\'.')
            logging.error('Did you set it inside .env?')
        else:
            logging.info(f'Found API key for \'{ENV_VAR_NAME}\'.')
            self.KEY = api_key
        
    # # According to https://developer.here.com/documentation/map-tile/dev_guide/topics/load-balancing-and-urls.html
    # def _get_random_maptile_load_server_url(self, type='base'):
    #     return f'https://{random.randint(1, 4)}.{self.base_url[type]}'


