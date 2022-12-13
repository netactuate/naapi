"""Namespace for AsynicIO version of the sdk

It is very basic, like the plain one
"""
import json
import aiohttp

async def get_path(url=None, data=None):
    """TODO"""
    if data is None:
        data = {}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, data=data) as resp:
            response = await resp.text()

    return response

async def post_path(url=None, data=None):
    """TODO"""
    if data is None:
        data = {}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            response = await resp.text()

    return response

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
        super().__init__(message)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            "<NetActuateException in {0} : {1}>"
            .format(self.code, self.message)
        )


# pylint: disable=useless-object-inheritance, too-few-public-methods
class HVFromDict(object):
    """Takes any dict and creates an object out of it
    May behave weirdly if you do multiple level dicts
    So don't...
    """
    def __init__(self, kwargs):
        self.__dict__ = kwargs

    def __len__(self):
        return len(self.__dict__)


class HVJobStatus:
    """TODO"""
    def __init__(self, conn=None, node_id=None, job_result=None):
        if job_result is None:
            self.job_result = {}
        else:
            self.job_result = job_result
        self.conn = conn
        self.node_id = node_id
        self._job = None

    async def _get_job_status(self):
        """TODO"""
        params = {'mbpkgid': self.node_id,
                  'job_id': self.job_result['id']}
        result = await self.conn.connection(
            '/cloud/serverjob',
            data=params)
        return json.loads(result) # json.loads(result)

    async def status(self):
        """TODO"""
        if self._job is None:
            await self.refresh()
        return int(self._job['status'])

    async def job_id(self):
        """TODO"""
        if self._job is None:
            await self.refresh()
        return int(self._job.get('id', '0'))

    async def command(self):
        """TODO"""
        if self._job is None:
            await self.refresh()
        return self._job.get('command', '')

    async def inserted(self):
        """TODO"""
        if self._job is None:
            await self.refresh()
        return self._job.get('ts_insert', '0')

    async def is_success(self):
        """TODO"""
        if self._job is None:
            await self.refresh()
        return int(await self.status()) == 5

    async def is_working(self):
        """TODO"""
        if self._job is None:
            await self.refresh()
        return int(await self.status()) <= 3

    async def is_failure(self):
        """TODO"""
        if self._job is None:
            await self.refresh()
        return int(await self.status()) == 6

    async def refresh(self):
        """TODO"""
        self._job = await self._get_job_status()
        return self


# This is a closure that returns the request method below pre-configured
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

    async def request(url, data=None, method=None):
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
                for key, val in data.items():
                    url_root = "{0}&{1}={2}".format(url_root, key, val)
                response = await get_path(url_root)
            elif method == 'POST':
                response = await post_path(url_root, data=data)
        except aiohttp.ClientError:
            raise NetActuateException(
                response.status_code, response.content)

        if api_version == 'v1':
            return response
        else:
            # extract data or error
            response = json.loads(response)
            if response['result'] == 'success':
                if 'data' in response:
                    # extract the data response
                    # pylint: disable=protected-access
                    response = response['data']
                return response
            else:
                error_message = response['message']
                error_data = response
                del(error_data['result'])
                del(error_data['message'])
                raise NetActuateException(
                    error_message, json.dumps(error_data))

    return request


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

    async def locations(self):
        """Rewriting the dictionary into a list
        Also adding a key to each location named 'country'
        based off the flags value
        """
        locs_resp = await self.connection('/cloud/locations/')

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

    async def os_list(self):
        """
            Retrieve the list of available VM install images
        """
        return await self.connection('/cloud/images/')

    async def plans(self, location=False):
        """
            Retrieve the list of available VM plans in a location
        """
        if self.api_version == 'v1':
            if location:
                return await self.connection('/cloud/sizes/' + str(location))
            return await self.connection('/cloud/sizes/')
        else:
            # return a value list for consistency
            plans_resp = await self.connection('/cloud/sizes/' + str(location))
            return list(plans_resp.values())

    async def servers(self, mbpkgid=False):
        """
            Retrieve server details for one or all VM instances
        """
        if mbpkgid:
            return await self.connection('/cloud/server/' + str(mbpkgid))
        return await self.connection('/cloud/servers/')

    async def packages(self, mbpkgid=False):
        """
            Retrieve package-specific details for one or all packages
        """
        if mbpkgid:
            return await self.connection('/cloud/package/' + str(mbpkgid))
        return await self.connection('/cloud/packages')

    async def ipv4(self, mbpkgid):
        """
            Retrieve IPv4 assignment for a VM instance
        """
        return await self.connection('/cloud/ipv4/' + str(mbpkgid))

    async def ipv6(self, mbpkgid):
        """
            Retrieve IPv6 assignment for a VM instance
        """
        return await self.connection('/cloud/ipv6/' + str(mbpkgid))

    async def networkips(self, mbpkgid):
        """
            Retrieve IP assignments for a VM instance
        """
        return await self.connection('/cloud/networkips/' + str(mbpkgid))

    async def summary(self, mbpkgid):
        """
            Retrieve summary overview of a VM instance 
        """
        return await self.connection('/cloud/serversummary/' + str(mbpkgid))

    async def start(self, mbpkgid):
        """
            Start an offline VM instance
        """
        return await self.connection(
            '/cloud/server/start/{0}'.format(mbpkgid), method='POST')

    async def shutdown(self, mbpkgid, force=False):
        """
            Issue a shutdown signal to a VM instance or forcefully kill the instance
        """
        params = {}
        if force:
            params['force'] = 1
        return await self.connection(
            '/cloud/server/shutdown/{0}'.format(mbpkgid), data=params, method='POST')

    async def reboot(self, mbpkgid, force=False):
        """
            Reboot a VM instance
        """
        params = {}
        if force:
            params['force'] = 1
        return await self.connection(
            '/cloud/server/reboot/{0}'.format(mbpkgid), data=params,
            method='POST')

    async def rescue(self, mbpkgid, password):
        """
            Enable rescue mode on a VM instance
        """
        params = {'rescue_pass': str(password)}
        return await self.connection(
            '/cloud/server/start_rescue/{0}'.format(mbpkgid), data=params,
            method='POST')

    async def rescue_stop(self, mbpkgid):
        """
            Disable rescue mode on a VM instance
        """
        return await self.connection(
            '/cloud/server/stop_rescue/{0}'.format(mbpkgid), method='POST')

    # pylint: disable=too-many-arguments
    async def build(self, site, image, fqdn, passwd, mbpkgid, params=None):
        """
            Build a new VM to an existing instance
        """
        if not params:
            params = {'fqdn': fqdn, 'mbpkgid': mbpkgid,
                      'image': image, 'location': site,
                      'password': passwd}

        if self.api_version == 'v1':
            return await self.connection('/cloud/server/build/', data=params, method='POST')
        else:
            return await self.connection('/cloud/server/build/{0}'.format(mbpkgid), data=params, method='POST')

    async def delete(self, mbpkgid, extra_params=None):
        """Delete the vm
        If extra_params which defaults to cancel_billing=False
        add mbpkgid to extra_params and pass params, otherwise
        pass just the url with the mbpkgid
        Ansible role 'node.py' passes cancel_billing by default
        """
        if extra_params is not None:
            extra_params['mbpkgid'] = mbpkgid
            return await self.connection(
                '/cloud/server/delete/{0}'.format(mbpkgid), data=extra_params, method='POST'
            )
        return await self.connection(
            '/cloud/server/delete/{0}'.format(mbpkgid), method='POST'
        )

    async def unlink(self, mbpkgid):
        """
            Release the assigned location and IP allocation for a VM instance
        """
        return await self.connection(
            '/cloud/server/unlink/{0}'.format(mbpkgid), method='POST')

    async def status(self, mbpkgid):
        """
            Check the status of a VM instance
        """
        return await self.connection('/cloud/status/{0}'.format(mbpkgid))

    async def bandwidth_report(self, mbpkgid):
        """
            Retrieve monthly bandwidth report
        """
        return await self.connection('/cloud/servermonthlybw/' + str(mbpkgid))

    async def cancel(self, mbpkgid):
        """
            Cancel a service immediately
        """
        if self.api_version == 'v1':
            return await self.connection(
                '/cloud/cancel/{0}'.format(mbpkgid), method='POST'
            )
        else:
            params = {
                'mbpkgid': mbpkgid,
                'cancel_type': 'Immediate',
                'agree': 1
            }
            return await self.connection('/cloud/package/cancel', data=params, method='POST')

    async def buy(self, plan):
        """
            ! Deprecated !
            Acquire a new VM instance
        """
        if self.api_version == 'v1':
            return await self.connection('/cloud/buy/' + plan)
        else:
            raise NotImplementedError("Deprecated")

    async def buy_build(self, params):
        """
            Acquire and build to a new VM instance
        """
        if self.api_version == 'v1':
            endpoint = '/cloud/buy_build/'
        else:
            if 'mbpkgid' in params and params['mbpkgid']:
                # rebuilds should call the build endpoint instead
                params['mbpkgid'] = int(params['mbpkgid'])
                return await self.build(params=params)
            endpoint = '/cloud/server/buy_build'

        return await self.connection(endpoint, data=params, method='POST')

    async def get_job(self, mbpkgid, job_id):
        """
            Gets all server jobs for this mbpkgid with the provided jobid
        """
        if self.api_version == 'v1':
            params = {'job_id': job_id, 'mbpkgid': mbpkgid}
            return await self.connection('/cloud/serverjob/', data=params)
        else:
            return await self.connection('/cloud/server/{0}/jobs/{1}'.format(mbpkgid, job_id))

    async def get_jobs(self, mbpkgid):
        """
            Gets all server jobs for this mbpkgid
        """
        if self.api_version == 'v1':
            params = {'mbpkgid': mbpkgid}
            return await self.connection('/cloud/serverjobs/', data=params)
        else:
            return await self.connection('/cloud/server/{0}/jobs'.format(mbpkgid))

    async def bgp_sessions(self, session_id=False):
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

        return await self.connection(endpoint)


    async def bgp_summary(self):
        """
            Retrieve BGP session summary
        """
        if self.api_version == 'v1':
            endpoint = '/cloud/bgpsummary'
        else:
            endpoint = '/bgp/bgpsummary'

        return await self.connection(endpoint)

    async def bgp_groups(self, group_id=False):
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

        return await self.connection(endpoint)

    async def bgp_asns(self):
        """
            Retrieve BGP group information
        """
        if self.api_version == 'v1':
            endpoint = '/cloud/bgpasns'
        else:
            endpoint = '/bgp/bgpasns'

        return await self.connection(endpoint)

    async def bgp_create_sessions(self, mbpkgid, group_id, ipv6=True, redundant=False):
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
            return await self.connection(endpoint, data=params, method='POST')
        else:
            params['mbpkgid'] = mbpkgid 
            endpoint = '/bgp/bgpcreatesessions'
            # backwards compatibility
            bgp_resp = await self.connection(endpoint, data=params, method='POST')
            bgp_json = bgp_resp.json()
            if 'Sessions' in bgp_json:
                bgp_json['sessions'] = list(bgp_json.pop('Sessions').values())
            if 'Modified' in bgp_json:
                bgp_json['modified'] = bgp_json.pop('Modified')
            bgp_json['success'] = True
            bgp_resp._content = json.dumps(bgp_json).encode()
            return bgp_resp

    async def bgp_buy_prefixes(self, name, agreement_id, group_id=None, asn_id=None, anycast_profile=1):
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

        return await self.connection(endpoint, data=params, method='POST')
