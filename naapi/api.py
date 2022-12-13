"""NetActuate API Python client library naapi

Author: Dennis Durling<djdtahoe@gmail.com>
"""
import json
import requests as rq

API_HOSTS = {
    'v1': 'vapi.netactuate.com',
    'v2': 'vapi2.netactuate.com',
}

API_ROOT = {
    'v1': '',
    'v2': '/api'
}

class NetActuateException(Exception):
    """
        Basic exception class for API errors
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message
        self.args = (code, message)
        super(NetActuateException, self).__init__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            "<NetActuateException in {0} : {1}>"
            .format(self.code, self.message)
        )

def connection(key, api_version=None, api_host=None):
    """
        Conncetion wrapper
    """
    __key__ = key

    if not api_host:
        if api_version in API_HOSTS.keys():
            api_host = API_HOSTS[api_version]
        else: 
            api_host = API_HOSTS['v2']

    root_url = 'https://{0}'.format(api_host)

    if api_version in API_ROOT.keys():
        root_url = root_url + API_ROOT[api_version]
    else:
        root_url = root_url + API_ROOT['v2']

    def request(url, data=None, method=None):
        if method is None:
            method = 'GET'
        if data is None:
            data = {}
        if not url.startswith('/'):
            url = '/{0}'.format(url)

        # build full url
        url_root = '{0}{1}?key={2}'.format(root_url, url, __key__)

        try:
            if method == 'GET':
                for key, value in data.items():
                    url_root = "{0}&{1}={2}".format(url_root, key, value)
                response = rq.get(url_root)
            elif method == 'POST':
                response = rq.post(url_root, json=data)
        except rq.HTTPError:
            raise NetActuateException(
                response.status_code, response.content)

        if api_version == 'v1':
            return response
        else:
            # extract data or error
            resp_body = response.json()
            if resp_body['result'] == 'success':
                if 'data' in resp_body:
                    # extract the data response
                    # pylint: disable=protected-access
                    response._content = json.dumps(resp_body['data']).encode()
                return response
            else:
                error_message = resp_body['message']
                error_data = resp_body
                del(error_data['result'])
                del(error_data['message'])
                raise NetActuateException(
                    error_message, json.dumps(error_data))

    return request

# pylint: disable=too-many-public-methods
class NetActuateNodeDriver():
    """
        API wrapper for common calls
    """
    name = 'NetActuate'
    website = 'http://www.netactuate.com'

    def __init__(self, key, api_version=None, api_host=None):
        if api_version is None:
            self.api_version = 'v2'
        else:
            self.api_version = api_version
        self.key = key
        self.connection = connection(self.key, api_version=self.api_version, api_host=api_host)

    def locations(self):
        """Rewriting the dictionary into a list
        Also adding a key to each location named 'country'
        based off the flags value
        """
        locs_resp = self.connection('/cloud/locations/')

        if self.api_version == 'v1':
            locations = []
            locs_dict = locs_resp.json()

            # If we received an error pass it up now for handling
            if 'error' in locs_dict:
                if 'msg' in locs_dict:
                    return locs_dict

            for loc_key in locs_dict:
                locs_dict[loc_key]['country'] = locs_dict[loc_key]['flag'].upper()
                # put in list
                locations.append(locs_dict[loc_key])

            # update the response object so we can return it as a list
            # like other response objects. TODO: Update api to return a list
            # pylint: disable=protected-access
            locs_resp._content = json.dumps(locations).encode()
        return locs_resp

    def os_list(self):
        """
            Retrieve the list of available VM install images
        """
        return self.connection('/cloud/images/')

    def plans(self, location=False):
        """
            Retrieve the list of available VM plans in a location
        """
        if self.api_version == 'v1':
            if location:
                return self.connection('/cloud/sizes/' + str(location))
            return self.connection('/cloud/sizes/')
        else:
            plans_resp = self.connection('/cloud/sizes/' + str(location))
            # return values for improved compatibility
            plans_resp._content = json.dumps(list(plans_resp.json().values())).encode()
            return plans_resp

    def servers(self, mbpkgid=False):
        """
            Retrieve server details for one or all VM instances
        """
        if mbpkgid:
            return self.connection('/cloud/server/' + str(mbpkgid))
        return self.connection('/cloud/servers/')

    def packages(self, mbpkgid=False):
        """
            Retrieve package-specific details for one or all packages
        """
        if mbpkgid:
            return self.connection('/cloud/package/' + str(mbpkgid))
        return self.connection('/cloud/packages')

    def ipv4(self, mbpkgid):
        """
            Retrieve IPv4 assignment for a VM instance
        """
        return self.connection('/cloud/ipv4/' + str(mbpkgid))

    def ipv6(self, mbpkgid):
        """
            Retrieve IPv6 assignment for a VM instance
        """
        return self.connection('/cloud/ipv6/' + str(mbpkgid))

    def networkips(self, mbpkgid):
        """
            Retrieve IP assignments for a VM instance
        """
        return self.connection('/cloud/networkips/' + str(mbpkgid))

    def summary(self, mbpkgid):
        """
            Retrieve summary overview of a VM instance 
        """
        return self.connection('/cloud/serversummary/' + str(mbpkgid))

    def start(self, mbpkgid):
        """
            Start an offline VM instance
        """
        return self.connection(
            '/cloud/server/start/{0}'.format(mbpkgid), method='POST')

    def shutdown(self, mbpkgid, force=False):
        """
            Issue a shutdown signal to a VM instance or forcefully kill the instance
        """
        params = {}
        if force:
            params['force'] = 1
        return self.connection(
            '/cloud/server/shutdown/{0}'.format(mbpkgid), data=params, method='POST')

    def reboot(self, mbpkgid, force=False):
        """
            Reboot a VM instance
        """
        params = {}
        if force:
            params['force'] = 1
        return self.connection(
            '/cloud/server/reboot/{0}'.format(mbpkgid), data=params,
            method='POST')

    def rescue(self, mbpkgid, password):
        """
            Enable rescue mode on a VM instance
        """
        params = {'rescue_pass': str(password)}
        return self.connection(
            '/cloud/server/start_rescue/{0}'.format(mbpkgid), data=params,
            method='POST')

    def rescue_stop(self, mbpkgid):
        """
            Disable rescue mode on a VM instance
        """
        return self.connection(
            '/cloud/server/stop_rescue/{0}'.format(mbpkgid), method='POST')

    # pylint: disable=too-many-arguments
    def build(self, site=None, image=None, fqdn=None, passwd=None, mbpkgid=None, params=None):
        """
            Build a new VM to an existing instance
        """
        if not params:
            params = {'fqdn': fqdn, 'mbpkgid': mbpkgid,
                      'image': image, 'location': site,
                      'password': passwd}

        if self.api_version == 'v1':
            return self.connection('/cloud/server/build/', data=params, method='POST')
        else:
            return self.connection('/cloud/server/build/{0}'.format(params['mbpkgid']), data=params, method='POST')

    def delete(self, mbpkgid, extra_params=None):
        """Delete the vm
        If extra_params which defaults to cancel_billing=False
        add mbpkgid to extra_params and pass params, otherwise
        pass just the url with the mbpkgid
        Ansible role 'node.py' passes cancel_billing by default
        """
        if extra_params is not None:
            extra_params['mbpkgid'] = mbpkgid
            return self.connection(
                '/cloud/server/delete/{0}'.format(mbpkgid), data=extra_params, method='POST'
            )
        return self.connection(
            '/cloud/server/delete/{0}'.format(mbpkgid), method='POST'
        )

    def unlink(self, mbpkgid):
        """
            Release the assigned location and IP allocation for a VM instance
        """
        return self.connection(
            '/cloud/server/unlink/{0}'.format(mbpkgid), method='POST')

    def status(self, mbpkgid):
        """
            Check the status of a VM instance
        """
        return self.connection('/cloud/status/{0}'.format(mbpkgid))

    def bandwidth_report(self, mbpkgid):
        """
            Retrieve monthly bandwidth report
        """
        return self.connection('/cloud/servermonthlybw/' + str(mbpkgid))

    def cancel(self, mbpkgid):
        """
            Cancel a service immediately
        """
        if self.api_version == 'v1':
            return self.connection(
                '/cloud/cancel/{0}'.format(mbpkgid), method='POST'
            )
        else:
            params = {
                'mbpkgid': mbpkgid,
                'cancel_type': 'Immediate',
                'agree': 1
            }
            return self.connection('/cloud/package/cancel', data=params, method='POST')

    def buy(self, plan):
        """
            ! Deprecated !
            Acquire a new VM instance
        """
        if self.api_version == 'v1':
            return self.connection('/cloud/buy/' + plan)
        else:
            raise NotImplementedError("Deprecated")

    def buy_build(self, params):
        """
            Acquire and build to a new VM instance
        """
        if self.api_version == 'v1':
            endpoint = '/cloud/buy_build/'
        else:
            if 'mbpkgid' in params and params['mbpkgid']:
                # rebuilds should call the build endpoint instead
                params['mbpkgid'] = int(params['mbpkgid'])
                return self.build(params=params)
            endpoint = '/cloud/server/buy_build'

        return self.connection(endpoint, data=params, method='POST')

    def get_job(self, mbpkgid, job_id):
        """
            Gets all server jobs for this mbpkgid with the provided jobid
        """
        if self.api_version == 'v1':
            params = {'job_id': job_id, 'mbpkgid': mbpkgid}
            return self.connection('/cloud/serverjob/', data=params)
        else:
            return self.connection('/cloud/server/{0}/jobs/{1}'.format(mbpkgid, job_id))

    def get_jobs(self, mbpkgid):
        """
            Gets all server jobs for this mbpkgid
        """
        if self.api_version == 'v1':
            params = {'mbpkgid': mbpkgid}
            return self.connection('/cloud/serverjobs/', data=params)
        else:
            return self.connection('/cloud/server/{0}/jobs'.format(mbpkgid))

    def bgp_sessions(self, session_id=False):
        """
            Retrieve BGP session information
        """
        if self.api_version == 'v1':
            if session_id:
                endpoint = '/cloud/bgpsession2/{0}'.format(session_id)
            else:
                endpoint = '/cloud/bgpsessions2'
        else:
            if session_id:
                endpoint = '/bgp/bgpsession/{0}'.format(session_id)
            else:
                endpoint = '/bgp/bgpsessions'

        return self.connection(endpoint)


    def bgp_summary(self):
        """
            Retrieve BGP session summary
        """
        if self.api_version == 'v1':
            endpoint = '/cloud/bgpsummary'
        else:
            endpoint = '/bgp/bgpsummary'

        return self.connection(endpoint)

    def bgp_groups(self, group_id=False):
        """
            Retrieve BGP group information
        """
        if self.api_version == 'v1':
            if group_id:
                endpoint = '/cloud/bgpgroup/{0}'.format(group_id)
            else:
                endpoint = '/cloud/bgpgroups'
        else:
            if group_id:
                endpoint = '/bgp/bgpgroup/{0}'.format(group_id)
            else:
                endpoint = '/bgp/bgpgroups'

        return self.connection(endpoint)

    def bgp_asns(self):
        """
            Retrieve BGP group information
        """
        if self.api_version == 'v1':
            endpoint = '/cloud/bgpasns'
        else:
            endpoint = '/bgp/bgpasns'

        return self.connection(endpoint)

    def bgp_create_sessions(self, mbpkgid, group_id, ipv6=True, redundant=False):
        """
            Build BGP sessions for a node in a given BGP group
        """
        params = { "group_id": group_id }
        if ipv6:
            params['ipv6'] = 1
        if redundant:
            params['redundant'] = 1

        if self.api_version == 'v1':
            endpoint = '/cloud/bgpcreatesessions/{0}'.format(mbpkgid)
            return self.connection(endpoint, data=params, method='POST')
        else:
            params['mbpkgid'] = mbpkgid 
            endpoint = '/bgp/bgpcreatesessions'
            # backwards compatibility
            bgp_resp = self.connection(endpoint, data=params, method='POST')
            bgp_json = bgp_resp.json()
            if 'Sessions' in bgp_json:
                bgp_json['sessions'] = list(bgp_json.pop('Sessions').values())
            if 'Modified' in bgp_json:
                bgp_json['modified'] = bgp_json.pop('Modified')
            bgp_json['success'] = True
            bgp_resp._content = json.dumps(bgp_json).encode()
            return bgp_resp

    def bgp_buy_prefixes(self, name, agreement_id, group_id=None, asn_id=None, anycast_profile=1):
        """
            Build BGP sessions for a node in a given BGP group
        """
        params = {
            "name": name,
            "agreement_id": agreement_id,
        }

        if group_id:
            params['group_id'] = group_id
        else:
            params['asn_id'] = asn_id
            params['anycast_profile'] = anycast_profile

        if self.api_version == 'v1':
            raise NotImplementedError("Call not available in this version")
        else:
            endpoint = '/bgp/bgpbuyprefixes'

        return self.connection(endpoint, data=params, method='POST')
