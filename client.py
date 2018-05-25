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

class Processor:
    """
    A processor, as returned by Redfish
    """

class System:
    """
    A System as returned by Redfish
    """
    ignoretags = ['description', 'indicatorled', 'name']
    def __init__(self, parent, json):
        self.parent = parent # The parent DRAC
        self.json = json
        self.tags = []
        for k, v in self.json.items():
            if not isinstance(v, str) or k.startswith('@') or k.lower() in System.ignoretags:
                continue
            setattr(self, k.lower(), v)
            self.tags.append(k.lower())
        try:
            self.memory = json['MemorySummary']['TotalSystemMemoryGiB']
        except KeyError:
            logging.error("Error getting memory size for {}".format(self.id))
        else:
            self.tags.append('memory')

        # Now get the information on the CPUs. Has to handle multiples, so we have a dictionary of
        # Processor objects...

        self.cpus = self.getcpus

    def __repr__(self):
        return "\n".join(["{:15} = {}".format(t, getattr(self, t)) for t in self.tags if getattr(self, t)])

    def getcpus(self):
        """
        Gets the list of CPUs and the details for each
        :return: Dictionary of Processor objects
        """
        cpulistjson = self.parent.get()


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
        return "{}@{}:{}/{}".format(self.user, self.host, self.port, Obscure(self.password))

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
        logging.debug("Got Redfish version {}".format(self.version))
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

        else:
            logging.critical("Configuration file must have [DRAC] and [API] sections defined!")