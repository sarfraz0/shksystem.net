#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# installed
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, ForeignKey, String, Integer, Boolean, \
        create_engine
from sqlalchemy.orm import relationship, sessionmaker
from passlib.hash import sha512_crypt


## Globals
# =============================================================================

Base = declarative_base()

## Functions and Classes
# =============================================================================

class MailServer(Base):
    __tablename__ = 'mail_servers'
    cid      = Column(Integer, primary_key=True)
    hostname = Column(String, nullable=False)
    port     = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    sender   = Column(String, nullable=False)
    password = Column(String, nullable=False)
    user_cid = Column(Integer, ForeignKey('users.cid'))
    __table_args__ = (UniqueConstraint(
                         'hostname',
                         'username',
                         name='uq_mail_server'
                      ),)

    def __init__(self, hostname, port, username, password, sender, owner=None):
        self.hostname = hostname
        self.port     = port
        self.username = username
        self.sender   = sender
        self.password = password
        #keyring.set_password(hostname, username, password)
        if owner is not None:
            self.owner = user

    def to_dict(self):
        ret = {}
        ret['hostname']  = self.hostname
        ret['port']      = self.port
        ret['username']  = self.username
        ret['sender']    = self.sender
        if self.user is not None:
            ret['owner'] = self.user.pseudo
        return ret

    def to_json(self):
        return json.dumps(self.to_dict())
class
class Collab(Base):
    __tablename__ = 'collabs'

    owner_pseudo = Column(String, nullable=False)


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
