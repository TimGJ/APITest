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
        return "{}: {}".format(self.mac, self.sid)

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
        return {'id': u[0].id, 'tag': u[0].servicetag, 'sid': u[0].sid, 'stockid': u[0].stockid}


def GetServers():
    """
    Gets details of all servers from the database

    :return: A list of server objects
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(Server).all()
    session.close()
    return [{'id': r.id, 'tag': r.servicetag, 'sid': r.sid, 'stockid': r.stockid, 'comment': r.comment} for r in u]

def CreateServer(server):
    """
    Creates a server record in the database

    :param server: Dictionary containing servicetag, sid and stockid
    :return:
    """
    logging.debug("Got server: {}".format(server))
    Session = sessionmaker(bind=engine)
    session = Session()
    record = Server(servicetag=server.get('tag'), sid=server.get('sid'), stockid=server.get('stockid'), comment=server.get('comment'))
    session.add(record)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        rv = {"error": e}
    else:
        rv = server
        rv['id'] = record.id
    logging.debug("Inserted server ID {}".format(record.id))
    session.close()
    logging.debug("Returning {}".format(server))
    return rv

def DeleteServer(id):
    """
    Deletes a server fromt he database
    :param id: id (PK) of the server to delete. integer
    :return: boolean. True if deletion was successful, else False
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    server = session.query(Server).filter(Server.id == id)
    deleted = False
    if server.count():
        logging.debug("Deleting server ID {}".format(id))
        server.delete()
        deleted = True
    session.commit()
    session.close()
    return deleted

def UpdateServer(id, details):
    """
    Updates the server with fields in the values dictionary
    :param id:
    :param values:
    :return:
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    server = session.query(Server).filter(Server.id == id).first()
    for k, v in details.items():
        if v:
            setattr(server, k, v)
    session.commit()
    session.close()


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
        return {'id': u[0].id, 'mac': u[0].mac, 'sid': u[0].sid}


def GetNICs():
    """
    Gets details of all NICs from the database

    :return: Alist of NIC objects
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    u = session.query(NIC).all()
    session.close()
    return [{'id': r.id, 'mac': r.mac, 'sid': r.sid, 'comment': r.comment} for r in u]

def CreateNIC(nic):
    """
    Creates a server record in the database

    :param nic: Dictionary containing mac and sid
    :return: dict
    """
    logging.debug("Got nic: {}".format(nic))
    Session = sessionmaker(bind=engine)
    session = Session()
    record = NIC(mac=nic.get('mac'), sid=nic.get('sid'), comment=nic.get('comment'))
    session.add(record)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        rv = {"error": e}
    else:
        rv = nic
        rv['id'] = record.id
    logging.debug("Inserted nic ID {}".format(record.id))
    session.close()
    logging.debug("Returning {}".format(nic))
    return rv

def DeleteNIC(id):
    """
    Deletes a NIC from the database
    :param id: id (PK) of the nic to delete. integer
    :return: boolean. True if deletion was successful, else False
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    nic = session.query(NIC).filter(NIC.id == id)
    deleted = False
    if nic.count():
        logging.debug("Deleting NIC ID {}".format(id))
        nic.delete()
        deleted = True
    session.commit()
    session.close()
    return deleted

def UpdateNIC(id, details):
    """
    Updates the server with fields in the values dictionary
    :param id:
    :param values:
    :return:
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    nic = session.query(NIC).filter(NIC.id == id).first()
    for k, v in details.items():
        if v:
            setattr(nic, k, v)
    session.commit()
    session.close()



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
    create = False
    if create:
        CreateServer({'tag':'xlerb', 'sid':22222, 'stockid':33333})
        CreateServer({'tag':'xyzzy', 'sid':22223, 'stockid':33334})
        CreateServer({'tag':'foo',   'sid':22224, 'stockid':33335})
        CreateServer({'tag':'bar',   'sid':22225, 'stockid':33336})

    UpdateServer(1, {"comment": "Foo!"})