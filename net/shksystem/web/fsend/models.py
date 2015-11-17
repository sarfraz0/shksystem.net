# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import json
# installed
import keyring
from passlib.hash import sha512_crypt
from flask.ext.sqlalchemy import SQLAlchemy

# Globals
# =============================================================================

db = SQLAlchemy()

# Classes and Functions
# =============================================================================


class User(db.Model):
    """Flask-Login User class"""
    __tablename__ = "users"
    k = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String, nullable=False, unique=True)
    passwhash = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_manager = db.Column(db.Boolean, default=False)


    def __init__(self, pseudo, passw, is_admin=False, is_manager=False):
        self.pseudo = pseudo
        self.passwhash = sha512_crypt.encrypt(passw)
        self.is_admin = is_admin
        self.is_manager = is_manager

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
        ret['IS_MANAGER'] = self.is_manager
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


class Persona(db.Model):
    __tablename__ = 'personas'
    k = db.Column(db.Integer, primary_key=True)


class UserMailServer(db.Model):
    __tablename__ = 'user_mail_servers'
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


class Corporation(db.Model):
    __tablename__ = 'corporations'
    k = db.Column(db.Integer, primary_key=True)


class Grunt(db.Model):
    __tablename__ = 'grunts'
    k = db.Column(db.Integer, primary_key=True)


#
