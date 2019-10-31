
import requests
import json

class invalidCredentials(Exception):

    def __init__(self, message):
        self.message = message

class SHCAPI:

    _API_PATH = '/remote/json-rpc'

    def __init__(self, url, username, password):
        self.url = url
        self.sessionId = self.connect(url, username, password)

    def connect(self, url, username, password):

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        #session = requests.Session()
        #session.get(url)

        res = requests.post(url, headers=headers, auth=(username, password))
        if res.status_code != 200:
            if res.status_code == 401:
                raise invalidCredentials("The username or password is wrong")
            else:
                raise res.raise_for_status()
        else:
            return requests.utils.dict_from_cookiejar(res.cookies)['JSESSIONID']

    def query(self, method, params=['', '']):
        apiUrl = self.url + self._API_PATH

        data = {
			"jsonrpc": "2.0",
			'method': method,
			'params': params,
			'id': 1
		}

        headers = {
			'Cookie': 'JSESSIONID=' + self.sessionId,
			'Accept-Encoding': 'gzip, deflate',
			'Content-Type': 'application/json',
			'Accept': 'application/json, text/javascript, */*; q=0.01',
		}

        try:
            res = requests.post(apiUrl, data=json.dumps(data), headers=headers).json()
        except ValueError as err:
            if err == 'Expecting value: line 1 column 1 (char 0)':
                print('The SHC gave an invalid response. Most likely, this is due to an incorrect URL in your INI-file')
                print('Please verify that your URL is of the format "http://IP:port", or just "http://IP" if you use default port 80')
            raise

        return res['result']

    def getSystemInfo(self):
        return self.query("Settings/getSystemInfo")

    def getDiagnostics(self):
        return self.query("Diagnostics/getAllSystemStates")

    def getZones(self):
        return self.query("HFM/getZones")

    def getDevices(self, zone=[]):
        if(type(zone) == list):
            ret = []
            if(len(zone) == 0):
                zone = self.getZones()
            for i in zone:
                ret += self.query('StatusControlFunction/getDevices', [i['zoneId'], ''])
            return ret
        else:
            return self.query('StatusControlFunction/getDevices', [zone['zoneId'], ''])
