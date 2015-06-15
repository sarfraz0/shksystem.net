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
# installed
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


class Feed(db.Model):
    __tablename__ = 'feeds'
    k = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    regex = db.Column(db.String, nullable=False)
    strike_url = db.Column(db.String, nullable=False)
    kickass_url = db.Column(db.String, nullable=False)
    has_episodes = db.Column(db.Boolean, default=False)
    has_seasons = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    rules = db.relationship('Rule', backref='feed')
    user_k = db.Column(db.Integer, db.ForeignKey('users.k'))

    def __init__(self, name, regex, strike_url, kickass_url, user_k,
                 has_episodes=False, has_seasons=False, is_active=True):
        self.name = name
        self.regex = regex
        self.strike_url = strike_url
        self.kickass_url = kickass_url
        self.has_episodes = has_episodes
        self.has_seasons = has_seasons
        self.is_active = is_active
        self.user_k = user_k

class Rule(db.Model):
    __tablename__ = 'rules'
    k = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    dlleds = db.relationship('DLLed', backref='rule')
    feed_k = db.Column(db.Integer, db.ForeignKey('feeds.k'))

    def __init__(self, name, feed_k, is_active=True):
        self.name = name
        self.is_active = is_active
        self.feed_k = feed_k

class DLLed(db.Model):
    __tablename__ = 'dlleds'
    k = db.Column(db.Integer, primary_key=True)
    magnet_uri = db.Column(db.String, nullable=False)
    dayofdown = db.Column(db.String, nullable=False)
    in_filesytem = db.Column(db.Boolean, default=False)
    rule_k = db.Column(db.Integer, db.ForeignKey('rules.k'))

    def __init__(self, magnet_uri, filepath):
        self.magnet_uri = magnet_uri
        self.dayofdown = get_current_timestamp()
        self.in_filesystem = os.path.isfile(filepath)



# ------------------------------------------------------------------------------
#
