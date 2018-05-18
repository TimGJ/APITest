import logging

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, validates
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.exc

import re

Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://tim:White&Dog22@localhost/inventory')
metadata = MetaData(bind=engine)

class Server(Base):
    """
    Auto-discovered SQLAlchemy class for the servers table in the DB
    """
    __table__ = Table('servers', metadata, autoload=True)

    def __repr__(self):
        return "{}: SID: {} StockID: {}".format(self.servicetag, self.sid, self.stockid)

class NIC(Base):
    """
    Auto-discovered SQLAlchemy class for the nics table in the DB
    """
    __table__ = Table('nics', metadata, autoload=True)

    def __repr__(self):
        return "{}: {}".format(self.mac, self.serverid)

class IP(Base):
    """
    Auto-discovered SQLAlchemy class for the ips table in the DB
    """
    __table__ = Table('ips', metadata, autoload=True)

    def __repr__(self):
        return self.ip

class User(Base):
    """
    Auto-discovered SQLAlchemy class for the users table in the DB
    """
    __table__ = Table('users', metadata, autoload=True)

def GetHashedPassword(user):
    """
    Retrieves a hashed password from the database for a particular user or None if the user doesn't exist
    :param user: str
    :return: hash: str
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(User).filter(User.name == user)
    session.close()
    if u.count() == 0:
        logging.warning("Can't find user {} in database".format(user))
    elif u.count() == 1:
        logging.debug("User {} : {}".format(user, u[0].hash))
        return u[0].hash
    else:
        logging.error("User {} has mutiple ({}) entries in the user table!".format(user, u.count()))

def GetServer(id):
    """
    Gets details of a server from the database
    
    :param id: The ID of the server.
    :return: A server object or None if ID can't be matched.
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(Server).filter(Server.id == id)
    session.close()
    if u.count():
        return u[0]


def GetServers():
    """
    Gets details of all servers from the database

    :return: A list of server objects
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(Server).all()
    session.close()
    return u


def GetNIC(id):
    """
    Gets details of a NIC from the database

    :param id: The ID of the server.
    :return: A server object or None if ID can't be matched.
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(NIC).filter(NIC.id == id)
    session.close()
    if u.count():
        return u[0]


def GetNICs():
    """
    Gets details of all NICs from the database

    :return: Alist of NIC objects
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(NIC).all()
    session.close()
    return u


def GetIP(id):
    """
    Gets details of a IP address from the database

    :param id: The ID of the ip address.
    :return: An IP object or None if ID can't be matched.
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(IP).filter(IP.id == id)
    session.close()
    if u.count():
        return u[0]


def GetIPs():
    """
    Gets details of all IPs from the database

    :return: A server object or None if ID can't be matched.
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(IP).all()
    session.close()
    return u



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Did you really want to call this?")