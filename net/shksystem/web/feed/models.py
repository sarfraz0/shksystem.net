# -*- coding: utf-8 -*-

""""
    OBJET            : Flask SQLAlchemy models
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 08.06.1015
    LICENSE          : GPL-3
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# standard
import os
import json
# installed
import keyring
from passlib.hash import sha512_crypt
from flask.ext.sqlalchemy import SQLAlchemy
# custom
from net.shksystem.common.utils import get_current_timestamp

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

db = SQLAlchemy()

# ------------------------------------------------------------------------------
# Classes and Functions
# ------------------------------------------------------------------------------


class User(db.Model):
    """Flask-Login User class"""
    __tablename__ = "users"
    k = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String, nullable=False, unique=True)
    passwhash = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    feeds = db.relationship('Feed', backref='user')

    def __init__(self, pseudo, passw, is_admin):
        self.pseudo = pseudo
        self.passwhash = sha512_crypt.encrypt(passw)
        self.is_admin = is_admin

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.k)

    def to_dict(self):
        ret = {}
        ret['PSEUDO'] = self.pseudo
        ret['IS_ADMIN'] = self.is_admin
        return ret

    def to_json(self):
        return json.dumps(self.to_dict())


class MailServer(db.Model):
    __tablename__ = 'mail_servers'
    k = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String, nullable=False)
    port = db.Column(db.Integer, default=587)
    username = db.Column(db.String, nullable=False)
    sender = db.Column(db.String, nullable=False)

    def __init__(self, hostname, username, password, sender):
        self.hostname = hostname
        self.username = username
        self.sender = sender
        keyring.set_password(hostname, username, password)

    def to_dict(self):
        ret = {}
        ret['HOSTNAME'] = self.hostname
        ret['PORT'] = self.port
        ret['USERNAME'] = self.username
        ret['SENDER'] = self.sender
        return ret

    def to_json(self):
        return json.dumps(self.to_dict())


class Feed(db.Model):
    __tablename__ = 'feeds'
    k = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    regex = db.Column(db.String, nullable=False)
    strike_url = db.Column(db.String, nullable=False)
    kickass_url = db.Column(db.String, nullable=False)
    has_episodes = db.Column(db.Boolean, default=False)
    has_seasons = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    dest = db.Column(db.String)
    rules = db.relationship('Rule', backref='feed')
    user_k = db.Column(db.Integer, db.ForeignKey('users.k'), nullable=False)

    def __init__(self, name, cat, regex, strike_url, kickass_url, user_k,
                 has_episodes=False, has_seasons=False, is_active=True,
                 dest=''):
        self.name = name
        self.category = cat
        self.regex = regex
        self.strike_url = strike_url
        self.kickass_url = kickass_url
        self.has_episodes = has_episodes
        self.has_seasons = has_seasons
        self.is_active = is_active
        self.dest = dest
        self.user_k = user_k

    def to_dict(self):
        ret = {}
        ret['NAME'] = self.name
        ret['CATEGORY'] = self.category
        ret['REGEX'] = self.regex
        ret['STRIKE_URL'] = self.strike_url
        ret['KICKASS_URL'] = self.kickass_url
        ret['HAS_EPISODES'] = self.has_episodes
        ret['HAS_SEASONS'] = self.has_seasons
        ret['IS_ACTIVE'] = self.is_active
        ret['DEST'] = self.dest
        ret['USER_K'] = self.user_k
        return ret

    def to_json(self):
        return json.dumps(self.to_dict())


class Rule(db.Model):
    __tablename__ = 'rules'
    k = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    dlleds = db.relationship('DLLed', backref='rule')
    feed_k = db.Column(db.Integer, db.ForeignKey('feeds.k'), nullable=False)

    def __init__(self, name, feed_k, is_active=True):
        self.name = name
        self.is_active = is_active
        self.feed_k = feed_k

    def to_dict(self):
        ret = {}
        ret['NAME'] = self.name
        ret['IS_ACTIVE'] = self.is_active
        ret['FEED_K'] = self.feed_k
        return ret

    def to_json(self):
        return json.dumps(self.to_dict())


class DLLed(db.Model):
    __tablename__ = 'dlleds'
    k = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    magnet_uri = db.Column(db.String, nullable=False)
    dayofdown = db.Column(db.String, nullable=False)
    rule_k = db.Column(db.Integer, db.ForeignKey('rules.k'))

    def __init__(self, name, magnet_uri):
        self.name = name
        self.magnet_uri = magnet_uri
        self.dayofdown = get_current_timestamp()

# ------------------------------------------------------------------------------
#
