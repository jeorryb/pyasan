import configparser
import os
import requests


class NasaApiException(Exception):
    """Raised for any exception caused by a call to the Nasa API"""


def create_config(path):
    """
    Create pyasan config file
    """
    config = configparser.ConfigParser()
    config.add_section('Global')
    config.set('Global', 'APP_TOKEN', '')
    config.add_section('PATENT')
    config.set('PATENT', 'URL', 'https://data.nasa.gov/resource/nasa-patents.json')

    with open(path, 'w') as config_file:
        config.write(config_file)
    
def get_config(path):
    """
    Return config object.
    """
    if not os.path.exists(path):
        create_config(path)
    config = configparser.ConfigParser()
    return config

def init_config():
    path = 'config.ini'
    config = get_config(path)
    return config

def get_app_token():
    config = init_config()
    config.read('config.ini')
    app_token = config['Global']['app_token']
    return app_token

def get_url(api):
    """Grabs URL from config.ini for the corresponding API."""
    config = init_config()
    config.read('config.ini')
    url = config[api]['url']
    return url

def app_token_exists():
    token = get_app_token()
    if token != '':
        return True


def api_get(url, payload):
    payload = dict((k, v) for k, v in payload.items() if v)
    if app_token_exists():
        payload['$$app_token'] = get_app_token()
    response = requests.get(url, params=payload)
    response.raise_for_status()
    body = response.json()

    if 'error' in body:
        raise NasaApiException(body['error'])

    return body