# -*- coding: utf-8 -*-

""""
    OBJET            : MyTutorials data models
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 03.06.1015
    LICENSE          : GPL-3
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# standard
import uuid
import random
# installed
import keyring
from passlib.hash import sha512_crypt
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy
# custom
from net.shksystem.common.utils import get_current_timestamp
from net.shksystem.common.send_mail import SendMail

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
    _no = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String, nullable=False, unique=True)
    _passwhash = db.Column(db.String, nullable=False)
    _admin = db.Column(db.Boolean, nullable=False)
    _active = db.Column(db.Boolean, nullable=False)
    _token = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    name = db.Column(db.String)
    lastname = db.Column(db.String)
    birthday = db.Column(db.String)
    last_connected = db.Column(db.Integer, nullable=False)
    num_connected = db.Column(db.Integer, default=1)

    def __init__(self, pseudo, passw, email, admin=False, active=False):
        self.pseudo = pseudo
        self._passwhash = sha512_crypt.encrypt(passw)
        self.email = email
        self._admin = admin
        self._active = active
        self._token = str(uuid.uuid4())
        self.last_connected = get_current_timestamp()

    def is_active(self):
        return self._active

    def is_admin(self):
        return self._admin

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self._no)

    def verify_password(self, test_hash):
        return sha512_crypt.verify(test_hash, self._passwhash)

    def refresh_token(self):
        self._token = str(uuid.uuid4())

    def send_token(self):
        m = random.choice((MailSpool.query.all()))
        html = render_template('user_registration_mail.html', token=self._token)
        mailer = SendMail(m.server, m.port, m.username)
        mailer.send_mail(m.sender, 'Account validation token', html,
                         [self.email], htmlbody=True)

    def set_optionnals(self, post_dict):
        if 'name' in post_dict:
            self.name = post_dict['name']
        if 'lastname' in post_dict:
            self.lastname = post_dict['lastname']
        if 'birthday' in post_dict:
            self.birthday = post_dict['birthday']

    def update_connection_infos(self):
        self.last_connected = get_current_timestamp()
        self.num_connected += 1


class MailSpool(db.Model):
    __tablename__ = 'mail_spool'
    nudoss = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.String, nullable=False)
    port = db.Column(db.Integer, default=587)
    username = db.Column(db.String, nullable=False)
    sender = db.Column(db.String, nullable=False)

    def __init__(self, server, username, passwd, sender):
        self.server = server
        self.username = username
        self.sender = sender
        keyring.set_password(server, username, passwd)


# ------------------------------------------------------------------------------
#
