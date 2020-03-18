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
}


class NetActuateException(Exception):
    """TODO"""
    def __init__(self, code, message):
        self.code = code
        self.message = message
        self.args = (code, message)
        super().__init__(message)

    async def __str__(self):
        return self.__repr__()

    async def __repr__(self):
        return "<NetActuateException in %d : %s>" % (self.code, self.message)


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

    async def status(self):
        if self._job is None:
            await self.refresh()
        return int(self._job['status'])

    async def job_id(self):
        if self._job is None:
            await self.refresh()
        return int(self._job.get('id', '0'))

    async def command(self):
        if self._job is None:
            await self.refresh()
        return self._job.get('command', '')

    async def inserted(self):
        if self._job is None:
            await self.refresh()
        return self._job.get('ts_insert', '0')

    async def is_success(self):
        if self._job is None:
            await self.refresh()
        return int(await self.status()) == 5

    async def is_working(self):
        if self._job is None:
            await self.refresh()
        return int(await self.status()) <= 3

    async def is_failure(self):
        if self._job is None:
            await self.refresh()
        return int(await self.status()) == 6

    async def _get_job_status(self):
        params = {'mbpkgid': self.node_id,
                  'job_id': self.job_result['id']}
        result = await self.conn.connection(
            '/cloud/serverjob',
            data=params)
        return json.loads(result) # json.loads(result)

    async def refresh(self):
        self._job = await self._get_job_status()
        return self


# This is a closure that returns the request method below pre-configured
def connection(key, api_version):
    """TODO"""
    __key__ = key
    if api_version in ['v1', 'v1.1', 'v2']:
        root_url = 'http://{0}'.format(API_HOSTS[api_version])
    else:
        root_url = 'http://{0}'.format(API_HOSTS['v1'])

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
                response = post_path(url_root, data=data)
        except aiohttp.ClientError:
            raise NetActuateException(
                response.status_code, response.content)

        return response

    return request


class NetActuateNodeDriver():
    """TODO"""
    name = 'NetActuate'
    website = 'http://www.netactuate.com'

    def __init__(self, key, api_version=None):
        if api_version is None:
            self.api_version = 'v1'
        else:
            self.api_version = api_version
        self.key = key
        self.connection = connection(
            self.key,
            api_version=api_version)

    async def locations(self):
        """TODO"""
        return await self.connection('/cloud/locations/')

    async def os_list(self):
        """TODO"""
        return await self.connection('/cloud/images/')

    async def plans(self, location=False):
        """TODO"""
        if location:
            return await self.connection('/cloud/sizes/' + str(location))
        else:
            return await self.connection('/cloud/sizes/')

    async def servers(self, mbpkgid=False):
        """TODO"""
        if mbpkgid:
            result = await self.connection('/cloud/server/' + str(mbpkgid))
        else:
            result = await self.connection('/cloud/servers/')
        return result

    async def packages(self):
        """TODO"""
        return await self.connection('/cloud/packages')

    async def package(self, mbpkgid):
        """TODO"""
        return await self.connection('/cloud/package/' + str(mbpkgid))

    async def ipv4(self, mbpkgid):
        """TODO"""
        return await self.connection('/cloud/ipv4/' + str(mbpkgid))

    async def ipv6(self, mbpkgid):
        """TODO"""
        return await self.connection('/cloud/ipv6/' + str(mbpkgid))

    async def networkips(self, mbpkgid):
        """TODO"""
        return await self.connection('/cloud/networkips/' + str(mbpkgid))

    async def summary(self, mbpkgid):
        """TODO"""
        return await self.connection('/cloud/serversummary/' + str(mbpkgid))

    async def start(self, mbpkgid):
        """TODO"""
        return await self.connection(
            '/cloud/server/start/{0}'.format(mbpkgid), method='POST')

    async def shutdown(self, mbpkgid, force=False):
        """TODO"""
        params = {}
        if force:
            params['force'] = 1
        return await self.connection(
            '/cloud/server/shutdown/{0}'.format(mbpkgid), data=params, method='POST')

    async def reboot(self, mbpkgid, force=False):
        """TODO"""
        params = {}
        if force:
            params['force'] = 1
        return await self.connection(
            '/cloud/server/reboot/{0}'.format(mbpkgid), data=params,
            method='POST')

    async def rescue(self, mbpkgid, password):
        """TODO"""
        params = {'rescue_pass': str(password)}
        return await self.connection(
            '/cloud/server/start_rescue/{0}'.format(mbpkgid), data=params,
            method='POST')

    async def rescue_stop(self, mbpkgid):
        """TODO"""
        return await self.connection(
            '/cloud/server/stop_rescue/{0}'.format(mbpkgid), method='POST')

    async def build(self, dc, image, fqdn, passwd, mbpkgid):
        """TODO"""
        params = {'fqdn': fqdn, 'mbpkgid': mbpkgid,
                  'image': image, 'location': dc,
                  'password': passwd}

        return await self.connection(
            '/cloud/server/build/', data=params, method='POST')

    async def delete(self, mbpkgid):
        """TODO"""
        return await self.connection(
            '/cloud/server/delete/{0}'.format(mbpkgid), method='POST')

    async def unlink(self, mbpkgid):
        """TODO"""
        return await self.connection(
            '/cloud/unlink/{0}'.format(mbpkgid), method='POST')

    async def status(self, mbpkgid):
        """TODO"""
        return await self.connection('/cloud/status/{0}'.format(mbpkgid))

    # root password call is not enabled for api key use yet,
    # however you can auth with the account password to verify & submit
    # params['email']= 'abc@cde.com'
    # params['password']= 'abc!@#'
    async def bandwidth_report(self, mbpkgid):
        """TODO"""
        return await self.connection('/cloud/servermonthlybw/' + str(mbpkgid))

    async def cancel(self, mbpkgid):
        """TODO"""
        return await self.connection(
            '/cloud/cancel/{0}'.format(mbpkgid), method='POST')

    async def buy(self, plan):
        """TODO"""
        return await self.connection('/cloud/buy/' + plan)

    async def buy_build(self, plan, site, image, fqdn, passwd, mbpkgid):
        """TODO"""
        params = {'fqdn': fqdn, 'mbpkgid': mbpkgid,
                  'image': image, 'location': site,
                  'password': passwd, 'plan': plan}

        return await self.connection(
            '/cloud/buy_build/', data=params, method='POST')

    async def root_password(self, mbpkgid, passwd):
        """TODO"""
        params = {'rootpass': passwd}
        return await self.connection(
            '/cloud/server/password/' + mbpkgid, data=params, method='POST')
