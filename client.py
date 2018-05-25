"""
The client side of the PoC which sits in the middle of things doing API calls
to the DRAC and to the backend DB.
"""

import requests
import argparse
import logging
import configparser
import urllib.parse

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
        self.baseurl = "https://{}:{}/redfish/v1/".format(host, port)


    def __repr__(self):
        return "{}@{}:{}/{}".format(self.user, self.host, self.port, Obscure(self.password))

    def url(self, path):
        url = urllib.parse.urljoin(self.baseurl, path)
        logging.debug("{} + {} = {}".format(self.baseurl, path, url))
        return url

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
                url = drac.url('Chassis/System.Embedded.1')
                auth = (drac.user, drac.password)
                logging.debug("Attempting to Get {} as {}/{}".format(url, drac.user, Obscure(drac.password)))
                r = requests.get(url, auth=auth, verify=False)
                j = r.json()
                for item in ['Manufacturer', 'Model', 'SKU', 'SerialNumber']:
                    print("{:15}: {}".format(item, j.get(item, "UNKNOWN")))


        else:
            logging.critical("Configuration file must have [DRAC] and [API] sections defined!")