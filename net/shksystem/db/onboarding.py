# -*- coding: utf8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'


# standard
# installed
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, String, Integer, Boolean, ForeignKey, \
        UniqueConstraint, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from passlib.hash import sha512_crypt
# custom
from net.shksystem.common.constants import *


## Globals
# =============================================================================

Base = declarative_base()

## Functions and Classes
# =============================================================================


class Phone(Base):
    __tablename__ = PHONES_KEY

    cid = Column(Integer, primary_key=True)
    country_code = Column(String, nullable=False)
    region_code = Column(String)
    number = Column(String, nullable=False)
    # FAX, LANDLINE, MOBILE
    number_type = Column(String, nullable=False)
    profile_cid   = Column(Integer
            , ForeignKey('.'.join([ PROFILES_KEY, CID_KEY ]))
            )

    def __init__(self, country_code: str, number: str, number_type: str
            , region_code: str =None):

        self.country_code = country_code
        self.number = number
        self.number_type = number_type
        if region_code is not None:
            self.region_code = region_code

    def to_dict(self):
        ret = {}
        ret[COUNTRY_CODE_KEY] = self.country_code
        ret[NUMBER_KEY] = self.number
        ret[REGION_CODE_KEY] = self.region_code
        ret[NUMBER_TYPE_KEY] = self.number_type
        return ret


class Address(Base):
    __tablename__ = ADDRESSES_KEY

    cid           = Column(Integer, primary_key=True)
    appartment    = Column(Integer)
    building      = Column(String)
    street_number = Column(Integer, nullable=False)
    street_name   = Column(String, nullable=False)
    postal_code   = Column(String, nullable=False)
    town          = Column(String, nullable=False)
    region        = Column(String)
    country       = Column(String, nullable=False)
    profile_cid   = Column(Integer
            , ForeignKey('.'.join([ PROFILES_KEY, CID_KEY ]))
            )

    def __init__(self, appartment: int, street_number: int , street_name: str
            , postal_code: str, town: str , country: str, building: str =None
            , region: str =None):

        self.appartment = appartment
        self.building = building
        self.street_number = street_number
        self.street_name = street_name
        self.postal_code = postal_code
        self.town = town
        self.region = region
        self.country = country

    def to_dict(self):
        ret = {}
        ret[APPARTMENT_KEY] = self.appartment_number
        ret[STREET_NUMBER_KEY] = self.street_number
        ret[STREET_NAME_KEY] = self.street_name
        ret[POSTAL_CODE_KEY] = self.postal_code
        ret[TOWN_KEY] = self.town_name
        ret[COUNTRY_KEY] = self.country
        if self.building is not None:
            ret[BUILDING_KEY] = self.building
        if self.region_name is not None:
            ret[REGION_KEY] = self.region_name
        return ret


class Profile(Base):
    __tablename__ = PROFILES_KEY

    cid         = Column(Integer, primary_key=True)
    name        = Column(String, nullable=False)
    lastname    = Column(String, nullable=False)
    pseudo      = Column(String, nullable=False)
    address     = relationship(ADDRESS_KEY.capitalize(), backref=PROFILE_KEY
            , uselist=False
            )
    phones     = relationship(PHONE_KEY.capitalize(), backref=PROFILE_KEY)

    def __init__(self, name: str, lastname: str, pseudo: str):
        self.name = name
        self.lastname = lastname
        self.pseudo = pseudo

    def to_dict(self):
        ret = {}
        ret[NAME_KEY] = self.name
        ret[LASTNAME_KEY] = self.lastname
        ret[PSEUDO_KEY] = self.pseudo
        return ret


class MailServer(Base):
    __tablename__ = MAILSERVERS_KEY

    cid         = Column(Integer, primary_key=True)
    hostname    = Column(String, nullable=False)
    port        = Column(Integer, nullable=False)
    username    = Column(String, nullable=False)
    password    = Column(String, nullable=False)
    sender      = Column(String, nullable=False)
    configuration_cid = Column(Integer
            , ForeignKey('.'.join([ CONFIGURATIONS_KEY, CID_KEY ]))
            )

    __table_args__ = (UniqueConstraint(HOSTNAME_KEY, USERNAME_KEY
        , name='_'.join([ UQ_KEY, HOSTNAME_KEY, USERNAME_KEY ])),)

    def __init__(self, hostname: str, port: int, username: str
            , password: str, sender: str):
        self.hostname = hostname
        self.port     = port
        self.username = username
        self.password = password
        self.sender   = sender

    def to_dict(self):
        ret = {}
        ret[HOSTNAME_KEY] = self.hostname
        ret[PORT_KEY]     = self.port
        ret[USERNAME_KEY] = self.username
        ret[SENDER_KEY]   = self.sender
        return ret


class Configuration(Base):
    __tablename__ = CONFIGURATIONS_KEY

    cid         = Column(Integer, primary_key=True)
    mailservers = relationship(MAILSERVER_KEY.capitalize()
            , backref=CONFIGURATION_KEY
            )


def init_db(easy_connect):
    """
        init_db :: String -> IO ()
        ==========================
        Initialize the database schema
    """
    engine = create_engine(easy_connect)
    Base.metadata.create_all(engine)

def populate_db(easy_connect):
    """
        populate_db :: String -> IO ()
        ==============================
        Initialize the database schema and adds the standard columns
    """
    engine = create_engine(easy_connect)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.commit()

#
