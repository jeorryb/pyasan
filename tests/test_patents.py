from pyasan import patents, Patents
import vcr
from pytest import fixture

@fixture
def patent_keys():
    #Responsible only for returning the test data.
    return ['patent_number', 'center', 'patent_expiration_date',
            'case_number', 'title', 'application_sn',
            'status']

@vcr.use_cassette('tests/vcr_cassettes/Patent_req.yml')
def test_Patent_req_successful(patent_keys):
    """Tests and API call to return a patent from the NASA API"""
    
    patent_params = {'$q': 'fuel'}
    p = Patents(params=patent_params)
    test_query = p.req()

    assert isinstance(test_query[1], dict)
    assert set(patent_keys).issubset(test_query[1].keys()), 'All keys should be in the response'
    assert 'fuel' in test_query[1]['title'].lower(), 'Query should be in the title'

@vcr.use_cassette('tests/vcr_cassettes/Patent_req.yml')
def test_patent_get_successful(patent_keys):
    """Tests get call to query patent database from NASA API"""

    test_get = patents.get(query='fuel')

    assert isinstance(test_get[1], dict)
    assert set(patent_keys).issubset(test_get[1].keys()), 'All keys should be in the response'
    assert 'fuel' in test_get[1]['title'].lower(), 'Query should be in the title'


