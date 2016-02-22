#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# anaconda
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, ForeignKey, UniqueConstraint, \
                       String, Integer, Boolean, create_engine
from sqlalchemy.orm import relationship, sessionmaker
# installed
from passlib.hash import sha512_crypt
import keyring


## Globals
# =============================================================================

Base = declarative_base()

## Functions and Classes
# =============================================================================

roles_users = Table('roles_users', Base.metadata,
    Column('role_cid', Integer, ForeignKey('roles.cid')),
    Column('user_cid', Integer, ForeignKey('users.cid'))
)


class Status(Base):
    """ active|blacklisted|pending|deleted """
    __tablename__ = 'statuses'
    cid   = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False, unique=True)
    users = relationship('User', backref='status')

    def __init__(self, name):
        self.name = name


class Role(Base):
    """" admin|manager|user|guest """
    __tablename__ = 'roles'
    cid   = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False, unique=True)
    users = relationship('User', secondary=roles_users, backref='roles')

    def __init__(self, name):
        self.name = name

    def __check_name(self, name):
        ret = False
        if self.name.lower().strip() == name:
            ret = True
        return ret

    def is_admin(self):
        return self.__check_name('admin')

    def is_manager(self):
        return self.__check_name('manager')


class User(Base):
    __tablename__ = "users"
    cid          = Column(Integer, primary_key=True)
    pseudo       = Column(String, nullable=False, unique=True)
    passwhash    = Column(String, nullable=False)
    email        = Column(String)
    status_cid   = Column(Integer, ForeignKey('statuses.cid'))
    mail_servers = relationship('MailServer', backref='user')

    def __init__(self, pseudo, passw, status):
        self.pseudo     = pseudo
        self.passwhash  = sha512_crypt.encrypt(passw)
        self.status     = status

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.cid)

    def to_dict(self):
        ret = {}
        ret['pseudo']       = self.pseudo
        ret['email']        = self.email
        ret['status']       = self.status.name
        ret['mail_servers'] = [x.to_dict() for x in self.mail_servers]
        ret['roles']        = [x.name for x in self.roles]
        return ret

    def to_json(self):
        return json.dumps(self.to_dict())


class MailServer(Base):
    __tablename__ = 'mail_servers'
    cid      = Column(Integer, primary_key=True)
    hostname = Column(String, nullable=False)
    port     = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    sender   = Column(String, nullable=False)
    user_cid = Column(Integer, ForeignKey('users.cid'))
    __table_args__ = (UniqueConstraint(
                         'hostname',
                         'username',
                         name='uq_mail_server'
                      ),)

    def __init__(self, hostname, port, username, password, sender, user=None):
        self.hostname = hostname
        self.port     = port
        self.username = username
        self.sender   = sender
        keyring.set_password(hostname, username, password)
        if user is not None:
            self.user = user

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

    active      = Status('active')
    pending     = Status('pending')
    blacklisted = Status('blacklisted')
    disabled    = Status('disabled')
    session.add_all([active, pending, blacklisted, disabled])
    session.commit()

    admin   = Role('admin')
    manager = Role('manager')
    user    = Role('user')
    guest   = Role('guest')
    session.add_all([admin, manager, user, guest])
    session.commit()

    active_stat = session.query(Status).filter_by(name='active').first()
    admin_rol   = session.query(Role).filter_by(name='admin').first()
    guest_rol   = session.query(Role).filter_by(name='guest').first()

    administrator = User('admin', 'nimba', active_stat)
    administrator.roles.append(admin_rol)
    guest = User('guest', 'guest', active_stat)
    guest.roles.append(guest_rol)
    session.add_all([administrator, guest])
    session.commit()

#
