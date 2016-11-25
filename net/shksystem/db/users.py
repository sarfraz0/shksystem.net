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
from net.shksystem.common.constants import *

## Globals
# =============================================================================

Base = declarative_base()

## Functions and Classes
# =============================================================================

roles_users = Table('{0}_{1}'.format(ROLES_KEY, USERS_KEY), Base.metadata
        , Column('{0}_{1}'.format(ROLE_KEY, CID_KEY), Integer
            , ForeignKey('{0}.{1}'.format(ROLES_KEY, CID_KEY))
            )
        , Column('{0}_{1}'.format(USER_KEY, CID_KEY), Integer
            , ForeignKey('{0}.{1}'.format(USERS_KEY, CID_KEY))
            )
        , UniqueConstraint('{0}_{1}'.format(ROLE_KEY, CID_KEY)
            , '{0}_{1}'.format(USER_KEY, CID_KEY)
            , name='{0}_{1}_{2}'.format(UQ_KEY, ROLES_KEY, USERS_KEY)
            )
        )

namespaces_users = Table('{0}_{1}'.format(NAMESPACES_KEY, USERS_KEY)
        , Base.metadata
        , Column('{0}_{1}'.format(NAMESPACE_KEY, CID_KEY), Integer
            , ForeignKey('{0}.{1}'.format(NAMESPACES_KEY, CID_KEY))
            )
        , Column('{0}_{1}'.format(USER_KEY, CID_KEY), Integer
            , ForeignKey('{0}.{1}'.format(USERS_KEY, CID_KEY))
            )
        , UniqueConstraint('{0}_{1}'.format(NAMESPACE_KEY, CID_KEY)
            , '{0}_{1}'.format(USER_KEY, CID_KEY)
            , name='{0}_{1}_{2}'.format(UQ_KEY, NAMESPACES_KEY, USERS_KEY)
            )
        )

namespaces_roles = Table('{0}_{1}'.format(NAMESPACES_KEY, ROLES_KEY)
        , Base.metadata
        , Column('{0}_{1}'.format(NAMESPACE_KEY, CID_KEY), Integer
            , ForeignKey('{0}.{1}'.format(NAMESPACES_KEY, CID_KEY))
            )
        , Column('{0}_{1}'.format(ROLE_KEY, CID_KEY), Integer
            , ForeignKey('{0}.{1}'.format(ROLES_KEY, CID_KEY))
            )
        , UniqueConstraint('{0}_{1}'.format(NAMESPACE_KEY, CID_KEY)
            , '{0}_{1}'.format(ROLE_KEY, CID_KEY)
            , name='{0}_{1}_{2}'.format(UQ_KEY, NAMESPACES_KEY, ROLES_KEY)
            )
        )


class Status(Base):
    __tablename__ = STATUSES_KEY

    cid   = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False, unique=True)
    users = relationship(USER_KEY.capitalize(), backref=STATUS_KEY)

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        ret = {}
        ret[CID_KEY] = self.cid
        ret[NAME_KEY] = self.name
        ret[USERS_KEY] = [u.pseudo for u in self.users]
        return ret


class Role(Base):
    __tablename__ = ROLES_KEY

    cid   = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False, unique=True)
    users = relationship(USER_KEY.capitalize(), secondary=roles_users
            , backref=ROLES_KEY
            )

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        ret = {}
        ret[CID_KEY] = self.cid
        ret[NAME_KEY] = self.name
        ret[USERS_KEY] = [u.pseudo for u in self.users]
        ret[NAMESPACES_KEY] = [n.name for n in self.namespaces]
        return ret


class Namespace(Base):
    __tablename__ = NAMESPACES_KEY

    cid   = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False, unique=True)
    users = relationship(USER_KEY.capitalize(), secondary=namespaces_users,
                backref=NAMESPACES_KEY
                )
    roles = relationship(ROLE_KEY.capitalize(), secondary=namespaces_roles
            , backref=NAMESPACES_KEY
            )

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        ret = {}
        ret[CID_KEY] = self.cid
        ret[NAME_KEY] = self.name
        ret[USERS_KEY] = [u.pseudo for u in self.users]
        ret[ROLES_KEY] = [r.name for r in self.roles]
        return ret


class User(Base):
    __tablename__ = USERS_KEY
    cid          = Column(Integer, primary_key=True)
    pseudo       = Column(String, nullable=False, unique=True)
    passwhash    = Column(String, nullable=False)
    email        = Column(String)
    status_cid   = Column(Integer
            , ForeignKey('{0}.{1}'.format(STATUSES_KEY, CID_KEY))
            )

    def __init__(self, pseudo, passw, status):
        self.pseudo     = pseudo
        self.passwhash  = sha512_crypt.encrypt(passw)
        self.status     = status

    def to_dict(self):
        ret = {}
        ret[CID_KEY] = self.cid
        ret[PSEUDO_KEY] = self.pseudo
        ret[PASSWHASH_KEY] = self.passwhash
        ret[EMAIL_KEY]  = self.email
        ret[STATUS_KEY] = self.status.name
        ret[ROLES_KEY]  = [x.name for x in self.roles]
        ret[NAMESPACES_KEY] = [n.name for n in self.namespaces]
        return ret


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

    active      = Status(ACTIVE_KEY)
    pending     = Status(PENDING_KEY)
    blacklisted = Status(BLACKLISTED_KEY)
    disabled    = Status(DISABLED_KEY)
    session.add_all([active, pending, blacklisted, disabled])
    session.commit()

    admin   = Role(ADMIN_KEY)
    manager = Role(MANAGER_KEY)
    user    = Role(USER_KEY)
    guest   = Role(GUEST_KEY)
    session.add_all([admin, manager, user, guest])
    session.commit()


    active_stat = session.query(Status).filter_by(name=ACTIVE_KEY).first()
    admin_rol   = session.query(Role).filter_by(name=ADMIN_KEY).first()
    guest_rol   = session.query(Role).filter_by(name=GUEST_KEY).first()


    administrator = User(ADMIN_KEY, ADMIN_KEY, active_stat)
    administrator.roles.append(admin_rol)
    guest = User(GUEST_KEY, GUEST_KEY, active_stat)
    guest.roles.append(guest_rol)
    session.add_all([administrator, guest])
    session.commit()

    user_rol   = session.query(Role).filter_by(name=USER_KEY).first()
    manager_rol   = session.query(Role).filter_by(name=MANAGER_KEY).first()
    administrator_usr = session.query(User).filter_by(pseudo=ADMIN_KEY).first()
    guest_usr = session.query(User).filter_by(pseudo=GUEST_KEY).first()

    default = Namespace(DEFAULT_KEY)
    default.roles.extend([admin_rol, manager_rol, user_rol, guest_rol])
    default.users.extend([administrator_usr, guest_usr])
    session.add(default)
    session.commit()

#
