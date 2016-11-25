#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
# installed
from sqlalchemy import create_engine, Table, Column, Integer, String, \
                       ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from passlib.hash import sha512_crypt
# custom
import net.shksystem.common.constants as cst
import net.shksystem.constants.fsend as fcst

## Globals
# =============================================================================

Base = declarative_base()

## Functions and Classes
# =============================================================================

roles_users = Table(
                  '_'.join([fcst.ROLES_KEY, fcst.USERS_KEY]),
                  Base.metadata,
                  Column(
                      '_'.join([fcst.ROLES_KEY, cst.CID_KEY]),
                      Integer,
                      ForeignKey('.'.join([fcst.ROLES_KEY, cst.CID_KEY]))
                  ),
                  Column(
                      '_'.join([fcst.USERS_KEY, cst.CID_KEY]),
                      Integer,
                      ForeignKey('.'.join([fcst.USERS_KEY, cst.CID_KEY]))
                  ),
                  UniqueConstraint(
                      '_'.join([fcst.ROLE_KEY, cst.CID_KEY]),
                      '_'.join([fcst.USER_KEY, cst.CID_KEY]),
                      name='_'.join([ cst.UQ_KEY
                                    , fcst.ROLES_KEY
                                    , fcst.USERS_KEY ])
                  )
              )

namespaces_users = Table('namespaces_users', Base.metadata,
    Column('namespace_cid', Integer, ForeignKey('namespaces.cid')),
    Column('user_cid', Integer, ForeignKey('users.cid')),
    UniqueConstraint(
        'namespace_cid',
        'user_cid',
        name='uq_namespaces_users'
    )
)

namespaces_roles = Table('namespaces_roles', Base.metadata,
    Column('namespace_cid', Integer, ForeignKey('namespaces.cid')),
    Column('role_cid', Integer, ForeignKey('roles.cid')),
    UniqueConstraint(
        'namespace_cid',
        'role_cid',
        name='uq_namespaces_roles'
    )
)


class Status(Base):
    __tablename__ = 'statuses'
    cid   = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False, unique=True)
    users = relationship('User', backref='status')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        ret = {}
        ret['cid'] = self.cid
        ret['name'] = self.name
        ret['users'] = [u.pseudo for u in self.users]
        return ret


class Role(Base):
    __tablename__ = 'roles'
    cid   = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False, unique=True)
    users = relationship('User', secondary=roles_users, backref='roles')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        ret = {}
        ret['cid'] = self.cid
        ret['name'] = self.name
        ret['users'] = [u.pseudo for u in self.users]
        ret['namespaces'] = [n.name for n in self.namespaces]
        return ret


class Namespace(Base):
    __tablename__ = 'namespaces'
    cid   = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False, unique=True)
    users = relationship(
                'User',
                secondary=namespaces_users,
                backref='namespaces'
            )
    roles = relationship(
                'Role',
                secondary=namespaces_roles,
                backref='namespaces'
            )

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        ret = {}
        ret['cid'] = self.cid
        ret['name'] = self.name
        ret['users'] = [u.pseudo for u in self.users]
        ret['roles'] = [r.name for r in self.roles]
        return ret


class User(Base):
    __tablename__ = 'users'
    cid          = Column(Integer, primary_key=True)
    pseudo       = Column(String, nullable=False, unique=True)
    passwhash    = Column(String, nullable=False)
    email        = Column(String)
    status_cid   = Column(Integer, ForeignKey('statuses.cid'))

    def __init__(self, pseudo, passw, status):
        self.pseudo     = pseudo
        self.passwhash  = sha512_crypt.encrypt(passw)
        self.status     = status

    def to_dict(self):
        ret = {}
        ret['cid'] = self.cid
        ret['pseudo'] = self.pseudo
        ret['passwhash'] = self.passwhash
        ret['email']  = self.email
        ret['status'] = self.status.name
        ret['roles']  = [x.name for x in self.roles]
        ret['namespaces'] = [n.name for n in self.namespaces]
        return ret


class Profile(Base):
    __tablename__ = fcst.PROFILES_KEY
    cid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    letter = Column(String, nullable=False)
    motivation = Column(String, nullable=False)
    email = Column(String, nullable=False)
    cv = Column(String, nullable=False)

    def __init__(self, name, letter, motivation, email, cv)::w




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

    user_rol   = session.query(Role).filter_by(name='user').first()
    manager_rol   = session.query(Role).filter_by(name='manager').first()
    administrator_usr = session.query(User).filter_by(pseudo='admin').first()
    guest_usr = session.query(User).filter_by(pseudo='guest').first()

    default = Namespace('default')
    default.roles.extend([admin_rol, manager_rol, user_rol, guest_rol])
    default.users.extend([administrator_usr, guest_usr])
    session.add(default)
    session.commit()

#
