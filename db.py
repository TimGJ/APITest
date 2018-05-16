import logging

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import create_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://tim:White&Dog22@localhost/inventory')
metadata = MetaData(bind=engine)

class Racks(Base):
    __table__ = Table('racks', metadata, autoload=True)

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.commentary = kwargs.get('commentary')

    def __repr__(self):
        return "{}: {} {}".format(self.id, self.name, self.commentary)

Session = sessionmaker(bind=engine)
session = Session()
r = Racks()
r.name='RACK456'
r.commentary='Racky McRackface'
s = Racks(name='Snowy', commentary='Douche bag')
session.add(r)
session.add(s)
session.commit()
session.close()
