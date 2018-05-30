"""
The client side of the PoC which sits in the middle of things doing API calls
to the DRAC and to the backend DB.
"""

import requests
import argparse
import logging
import configparser
import urllib.parse
import http
import os.path
import string

class Subsystem:
    """
    Network interface controller, as returned by RedFish
    """

    IgnoreAttributes = ['IgnoreAttributes', 'Description'] # Attributes to ignore from the class

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if self._isvalid(k, v):
                setattr(self, k, v)


    def __repr__(self):
        s = []
        for k in dir(self):
            if (k[0] not in string.ascii_letters) or (k.upper() in [w.upper() for w in Subsystem.IgnoreAttributes]):
                continue
            s.append("{:20} = {}".format(k, getattr(self, k)))
        return "\n".join(s)

    def _isvalid(self, k, v):
        """
        Determines whether a particular key/value (from kwargs) should be included in the
        object's attributes.

        So...

        1. Don't allow values which are lists or dicts
        2. Only allow keys which consist of ASCII letters
        3. Don't allow certain banal keys on a list.
        :param k: Key
        :param v: Value
        :return: bool
        """
        if v is None or isinstance(v, dict) or isinstance(v,list):
            return False

        for c in k:
            if c not in string.ascii_letters + string.digits:
                return False

        if k.upper in [w.upper() for w in Subsystem.IgnoreAttributes]:
            return False

        return True


class NIC(Subsystem):
    pass

class SC(Subsystem):
    pass

class CPU(Subsystem):
    pass

class Disk(Subsystem):
    pass

class System:
    """
    A System as returned by Redfish
    """
    ignoretags = ['Description']
    def __init__(self, parent, json):
        self.parent = parent # The parent DRAC
        self.json = json
        self.tags = []
        for k, v in self.json.items():
            if not isinstance(v, str) or k[0] not in string.ascii_letters or k in System.ignoretags:
                continue
            setattr(self, k, v)
            self.tags.append(k)
        try:
            self.MemoryGB = json['MemorySummary']['TotalSystemMemoryGiB']
        except KeyError:
            logging.error("Error getting memory size for {}".format(self.id))
        else:
            self.tags.append('MemoryGB')

        # Now get the information on the CPUs. Has to handle multiples, so we have a dictionary of
        # Processor objects...

        self.cpus={}
        try:
            self.getcpus(json['Processors']['@odata.id'])
        except KeyError as e:
            logging.error("Can't get CPU URL: {}".format(e))

        self.nics = {}
        try:
            self.getnics(json['EthernetInterfaces']['@odata.id'])
        except KeyError as e:
            logging.error("Can't get Ethernet Interfaces URL: {}".format(e))

        self.storagecontrollers = {}
        self.disks = [] # Yes a list, as they don't have identifiers supplied by the DRAC
        try:
            self.getstoragecontrollers(json['SimpleStorage']['@odata.id'])
        except KeyError as e:
            logging.error("Can't get Simple Storage URL: {}".format(e))


    def __repr__(self):
        s =  "\n".join(["{:20} = {}".format(t, getattr(self, t)) for t in self.tags if getattr(self, t)])
        s += "\n{} CPUs found:".format(len(self.cpus))
        for k, v in self.cpus.items():
            s += "\n{:20}\n{}".format(k, v)
        s += "\n{} NICs found:".format(len(self.nics))
        for k, v in self.nics.items():
            s += "\n{:20}\n{}".format(k, v)
        s += "\n{} Storage Controllers found:".format(len(self.storagecontrollers))
        for k, v in self.storagecontrollers.items():
            s += "\n{:20}\n{}".format(k, v)
        s += "\n{} Disks/SSDs found:".format(len(self.disks))
        for d in self.disks:
            s += "\n{}".format(d)
        return s

    def getcpus(self, path):
        """
        Gets the list of CPUs and the details for each
        """
        cpusjson = self.parent.get(path)
        for cpuid, cpujson in enumerate(cpusjson['Members'],1):
            cpudetailsjson = self.parent.get(cpujson['@odata.id'])
            cpuname = os.path.split(cpujson['@odata.id'])[1]
            self.cpus[cpuname] = CPU(**cpudetailsjson)

    def getnics(self, path):
        """
        Gets the list of NICSs and the details for each
        """
        nicsjson = self.parent.get(path)
        for nicid, nicjson in enumerate(nicsjson['Members'],1):
            nicdetailsjson = self.parent.get(nicjson['@odata.id'])
            nicname = os.path.split(nicjson['@odata.id'])[1]
            self.nics[nicname] = NIC(**nicdetailsjson)


    def getstoragecontrollers(self, path):
        scsjson = self.parent.get(path)
        for scid, scjson in enumerate(scsjson['Members'],1):
            scdetailsjson = self.parent.get(scjson['@odata.id'])
            scname = os.path.split(scjson['@odata.id'])[1]
            logging.debug("SC {}: {}".format(scname, scdetailsjson))
            self.storagecontrollers[scname] = NIC(**scdetailsjson)
            for device in scdetailsjson['Devices']:
                self.disks.append(Disk(**device))

class DRAC:
    """
    An instance of a Dell iDRAC
    """
    def __init__(self, host, user, password, port=443):
        """
        Dell iDRAC
        """

        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.baseurl = "https://{}:{}".format(host, port)
        self.version = None
        self.systems = {}

    def __repr__(self):
        s =  "{}@{}:{}/{} {} systems detected:".format(self.user, self.host, self.port, Obscure(self.password), len(self.systems))
        for sysid, system in self.systems.items():
            s += "\n{}:\n{}".format(sysid, system)
        return s

    def url(self, path):
        url = urllib.parse.urljoin(self.baseurl, path)
        return url

    def get(self, path):
        """
        Gets the specified relative URL and returns JS
        :param path:
        :return:
        """
        auth = (self.user, self.password)
        url = self.url(path)
        logging.debug("Getting {}".format(url))
        try:
            r = requests.get(url, auth=auth, verify=False)
        except ConnectionError as e:
            logging.error("Error connecting to {}: {}".format(self.baseurl, e))
        else:
            if r.status_code == http.HTTPStatus.OK:
                return r.json()
            else:
                logging.error("Error {} ({}) getting {}".format(r.status_code, http.HTTPStatus(r.status_code).name, url))

    def explore(self):
        """
        Go through the hierarchy of information on the DRAC
        :return: None
        """
        chassisjson = self.get('/redfish/v1/')
        self.version = chassisjson.get('RedfishVersion')

        try:
            syspath = chassisjson['Systems']['@odata.id']
        except KeyError as e:
            logging.error("Error finding system URL")
        else:
            sysjson = drac.get(syspath)
            for system in sysjson['Members']:
                sysurl = system['@odata.id']
                sysname = os.path.split(sysurl)[1]
                self.systems[sysname] = System(self, self.get(sysurl))

def Obscure(text, num=1, symbol='*'):
    """
    Obscures `text`, replacing everything but the leading and trailing `num` characters
    with `symbol`. So Obscure('swordfish', '2', '+') would return 'sw+++++sh'.
    """
    if len(text) <= 2*num: # Too short to obscure anything
        return text
    else:
        return text[:num]+(len(text)-2*num)*symbol+text[-num:]

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)-8s: %(message)s")
    logging.captureWarnings(True)
    ap = argparse.ArgumentParser(description='Test the CLI', epilog="Copyright \N{COPYRIGHT SIGN} 2018 UKFast")
    ap.add_argument("--config", metavar='filename', help="Config file", default="apitest.cfg")
    args = ap.parse_args()

    cp = configparser.ConfigParser()
    read = cp.read(args.config)
    if cp.getboolean('DEFAULT', 'DEBUG'):
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug mode enabled")
    if len(read) == 0:
        logging.critical("Can't open {} for reading!".format(args.config))
    else:
        if "DRAC" in cp.sections() and "API" in cp.sections():
            if cp['DRAC']['user'] and cp['DRAC']['password'] and cp['DRAC']['host']:
                drac = DRAC(cp['DRAC']['host'], cp['DRAC']['user'], cp['DRAC']['password'])
                drac.explore()
                print(drac)

        else:
            logging.critical("Configuration file must have [DRAC] and [API] sections defined!")