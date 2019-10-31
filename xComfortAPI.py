
import requests
import json

class invalidCredentials(Exception):

    def __init__(self, message):
        self.message = message

class Device:

    def __init__(self, SHC, deviceInfo, zone):
        self._SHC = SHC
        self.info = deviceInfo
        self.zone = zone

    def id(self):
        return self.info['id']

    def printInfo(self):
        print("{:<15} {:>40} {:>4}".format(self.info['id'], self.info['name'], "{}{}".format(self.info['value'], self.info['unit'])))

    def setState(self, state):
        if (state in self.info['operations']):
            return self._SHC.query("StatusControlFunction/controlDevice", [self.zone['zoneId'], self.id(), state])
        raise Exception("The current device has no operation {}".format(operation))

    def turnOn(self):
        return self.setState('on')

    def turnOff(self):
        return self.setState('off')

    def switchOn(self):
        return self.setState('directSwitchOn')

    def switchOff(self):
        return self.setState('directSwitchOff')

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

        def convertDeviceArray(arr, zone):
            ret = []
            for i in arr:
                ret.append(Device(self, i, zone))
            return ret

        if(type(zone) == list):
            ret = []
            if(len(zone) == 0):
                zone = self.getZones()
            for i in zone:
                ret += convertDeviceArray(self.query('StatusControlFunction/getDevices', [i['zoneId'], '']), i)
            return ret
        elif (type(zone) == str):
            zoneInfo = None
            for i in self.getZones():
                if (i['zoneId'] == zone):
                    zoneInfo = i
            if (zoneInfo == None):
                raise Exception("The zone string {} is not a valid zone on the SHC".format(zone))
            return convertDeviceArray(self.query('StatusControlFunction/getDevices', [zone, '']), zoneInfo)
        else:
            return convertDeviceArray(self.query('StatusControlFunction/getDevices', [zone['zoneId'], '']), zone)

    def getDevice(self, deviceId, arr=[]):
        if(len(arr) == 0):
            arr = self.getDevices()

        for i in arr:
            if (i.id() == deviceId):
                return i

        raise Exception("The Device id {} is not found".format(deviceId))
