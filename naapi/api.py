"""NetActuate API Python client library naapi

Author: Dennis Durling<djdtahoe@gmail.com>
"""
import requests as rq

API_HOSTS = {
    'v1': 'vapi.netactuate.com',
}

class NetActuateException(Exception):
    """TODO"""
    def __init__(self, code, message):
        self.code = code
        self.message = message
        self.args = (code, message)
        super(NetActuateException, self).__init__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<NetActuateException in %d : %s>" % (self.code, self.message)

def connection(key, api_version):
    """TODO"""
    __key__ = key
    if api_version in API_HOSTS.keys():
        root_url = 'http://{}'.format(API_HOSTS[api_version])
    else:
        root_url = 'http://{}'.format(API_HOSTS['v1'])

    def request(url, data=None, method=None):
        if method is None:
            method = 'GET'
        if data is None:
            data = {}
        if not url.startswith('/'):
            url = '/{}'.format(url)

        # build full url
        url_root = '{}{}?key={}'.format(root_url, url, __key__)

        try:
            if method == 'GET':
                for key, value in data.items():
                    url_root = "{}&{}={}".format(url_root, key, value)
                response = rq.get(url_root)
            elif method == 'POST':
                response = rq.post(url_root, json=data)
        except rq.HTTPError:
            raise NetActuateException(
                response.status_code, response.content)

        return response

    return request

# pylint: disable=too-many-public-methods
class NetActuateNodeDriver():
    """Todo"""
    name = 'NetActuate'
    website = 'http://www.netactuate.com'

    def __init__(self, key, api_version=None):
        if api_version is None:
            self.api_version = 'v1'
        else:
            self.api_version = api_version
        self.key = key
        self.connection = connection(self.key, api_version=api_version)

    def locations(self):
        """Todo"""
        return self.connection('/cloud/locations/')

    def os_list(self):
        """Todo"""
        return self.connection('/cloud/images/')

    def plans(self, location=False):
        """Todo"""
        if location:
            return self.connection('/cloud/sizes/' + str(location))
        return self.connection('/cloud/sizes/')

    def servers(self, mbpkgid=False):
        """Todo"""
        if mbpkgid:
            return self.connection('/cloud/server/' + str(mbpkgid))
        return self.connection('/cloud/servers/')

    def packages(self):
        """Todo"""
        return self.connection('/cloud/packages')

    def package(self, mbpkgid):
        """Todo"""
        return self.connection('/cloud/package/' + str(mbpkgid))

    def ipv4(self, mbpkgid):
        """Todo"""
        return self.connection('/cloud/ipv4/' + str(mbpkgid))

    def ipv6(self, mbpkgid):
        """Todo"""
        return self.connection('/cloud/ipv6/' + str(mbpkgid))

    def networkips(self, mbpkgid):
        """Todo"""
        return self.connection('/cloud/networkips/' + str(mbpkgid))

    def summary(self, mbpkgid):
        """Todo"""
        return self.connection('/cloud/serversummary/' + str(mbpkgid))

    def start(self, mbpkgid):
        """Todo"""
        return self.connection(
            '/cloud/server/start/{}'.format(mbpkgid), method='POST')

    def shutdown(self, mbpkgid, force=False):
        """Todo"""
        params = {}
        if force:
            params['force'] = 1
        return self.connection(
            '/cloud/server/shutdown/{}'.format(mbpkgid), data=params, method='POST')

    def reboot(self, mbpkgid, force=False):
        """Todo"""
        params = {}
        if force:
            params['force'] = 1
        return self.connection(
            '/cloud/server/reboot/{}'.format(mbpkgid), data=params,
            method='POST')

    def rescue(self, mbpkgid, password):
        """Todo"""
        params = {'rescue_pass': str(password)}
        return self.connection(
            '/cloud/server/start_rescue/{}'.format(mbpkgid), data=params,
            method='POST')

    def rescue_stop(self, mbpkgid):
        """Todo"""
        return self.connection(
            '/cloud/server/stop_rescue/{}'.format(mbpkgid), method='POST')

    # pylint: disable=too-many-arguments
    def build(self, site, image, fqdn, passwd, mbpkgid):
        """Todo"""
        params = {'fqdn': fqdn, 'mbpkgid': mbpkgid,
                  'image': image, 'location': site,
                  'password': passwd}

        return self.connection(
            '/cloud/server/build/', data=params, method='POST')

    def delete(self, mbpkgid):
        """Todo"""
        return self.connection(
            '/cloud/server/delete/{}'.format(mbpkgid), method='POST')

    def unlink(self, mbpkgid):
        """Todo"""
        return self.connection(
            '/cloud/unlink/{}'.format(mbpkgid), method='POST')

    def status(self, mbpkgid):
        """Todo"""
        return self.connection('/cloud/status/{0}'.format(mbpkgid))

    def bandwidth_report(self, mbpkgid):
        """Todo"""
        return self.connection('/cloud/servermonthlybw/' + str(mbpkgid))

    def cancel(self, mbpkgid):
        """Todo"""
        return self.connection(
            '/cloud/cancel/{}'.format(mbpkgid), method='POST')

    def buy(self, plan):
        """Todo"""
        return self.connection('/cloud/buy/' + plan)

    def buy_build(self, plan, site, image, fqdn, passwd, mbpkgid):
        """Todo"""
        params = {'fqdn': fqdn, 'mbpkgid': mbpkgid,
                  'image': image, 'location': site,
                  'password': passwd, 'plan': plan}
        return self.connection(
            '/cloud/buy_build/', data=params, method='POST')

