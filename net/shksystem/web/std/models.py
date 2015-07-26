# -*- coding: utf-8 -*-

""""
    OBJET            : Flask SQLAlchemy models
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 16.06.1015
    LICENSE          : GPL-3
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# standard
import os
# installed
import keyring
from passlib.hash import sha512_crypt
from flask.ext.sqlalchemy import SQLAlchemy
# custom

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


class MailServer(db.Model):
    __tablename__ = 'mail_servers'
    k = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.String, nullable=False)
    port = db.Column(db.Integer, default=587)
    username = db.Column(db.String, nullable=False)
    sender = db.Column(db.String, nullable=False)

    def __init__(self, server, username, password, sender):
        self.server = server
        self.username = username
        self.sender = sender
        keyring.set_password(server, username, password)

# ------------------------------------------------------------------------------
#
