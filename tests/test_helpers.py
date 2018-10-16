import configparser
import os
import vcr
from pyasan import helpers
from pytest import fixture

def test_create_config_successfull(tmpdir):
    """Tests that creation of config.ini is successfull"""

    print(tmpdir)
    fh = tmpdir.join("config.ini")
    helpers.create_config(fh)

    filename = os.path.join(fh.dirname, fh.basename)

    config = configparser.ConfigParser()
    config.read(filename)

    assert config.sections() == ['Global', 'PATENT']

def test_get_config_successfull(tmpdir):
    fh = tmpdir.join('config.ini')
    helpers.get_config(fh)

    filename = os.path.join(fh.dirname, fh.basename)

    config = configparser.ConfigParser()
    config.read(filename)

    assert os.path.exists(fh)
    assert config.sections() == ['Global', 'PATENT']

def test_init_config_successfull():
    config = helpers.init_config()

    assert config == configparser.ConfigParser()

def test_get_app_token_successfull():
    app_token = helpers.get_app_token()

    assert app_token == ''

def test_get_url_successfull():
    patent_url = helpers.get_url('PATENT')

    assert patent_url == 'https://data.nasa.gov/resource/nasa-patents.json'


@fixture
def patent_keys():
    #Responsible only for returning the test data.
    return ['patent_number', 'center', 'patent_expiration_date',
            'case_number', 'title', 'application_sn',
            'status']

@vcr.use_cassette('tests/vcr_cassettes/api_get.yml')
def test_api_get_successful(patent_keys):
    """Tests and API call to return a patent from the NASA API"""

    test_url = 'https://data.nasa.gov/resource/nasa-patents.json'
    test_payload = {'patent_number': '5694939'}
    test_response = helpers.api_get(test_url, test_payload)

    assert isinstance(test_response[0], dict)
    assert test_response[0]['patent_number'] == '5694939', 'The patent_number should be in the response'
    assert set(patent_keys).issubset(test_response[0].keys()), 'All keys should be in the response'