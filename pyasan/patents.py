from . import helpers
import pprint


class Patents(object):
    def __init__(self, url=helpers.get_url('PATENT'), params=None, **kwargs):
        self.url = url
        self.params = params

    def req(self):

        self.response = helpers.api_get(self.url, self.params)
        return self.response

    def __str__(self):
        return pprint.pformat(self.req())


def get(query=None, patent_num=None,
        center=None, patent_exp=None,
        case_num=None, title=None,
        app_sn=None, status=None, **kwargs):

    params = {'$q': query,
              'patent_number': patent_num,
              'center': center,
              'case_number': case_num,
              'title': title,
              'application_sn': app_sn,
              'status': status}

    pat = Patents(params=params)

    return pat.req()
