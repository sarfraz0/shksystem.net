# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Flask data manipulation
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 15.01.2015
#@(#) LICENSE          : GPL-3
#@(#)----------------------------------------------------------------------

#==========================================================================
#
# WARNINGS
# NONE
#
#==========================================================================

#==========================================================================
# Imports
#==========================================================================

import keyring
from passlib.hash                   import sha512_crypt
from flask.ext.sqlalchemy           import SQLAlchemy
from net.shksystem.common.utils     import get_current_timestamp, get_random_elem, gen_random_token
from net.shksystem.common.send_mail import SendMail

#==========================================================================
# Environment/Static variables
#==========================================================================

db = SQLAlchemy()

#==========================================================================
# Classes/Functions
#==========================================================================

# -- FLASK MODELS
# -------------------------------------------------------------------------
class User(db.Model):
    """Flask-Login User class"""
    __tablename__ = "users"
    nudoss        = db.Column(db.Integer, primary_key=True)
    pseudo        = db.Column(db.String, nullable=False, unique=True)
    passwhash     = db.Column(db.String, nullable=False)
    is_admin      = db.Column(db.Boolean, nullable=False)
    persona       = db.relationship('Persona', uselist=False, backref='users')
    temp          = db.relationship('Temp', uselist=False, backref='users')
    up_debts      = db.relationship('Debt', backref='debts')
    down_debts    = db.relationship('Debt', backref='debts')

    def __init__(self, pseudo, passw, is_admin):
        self.pseudo     = pseudo
        self.passwhash  = sha512_crypt.encrypt(passw)
        self.is_admin   = is_admin

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.nudoss)

# -- APP MODELS
# -------------------------------------------------------------------------
class Persona(db.Model):
    __tablename__  = 'personas'
    nudoss         = db.Column(db.Integer, primary_key=True)
    user_attached  = db.Column(db.Integer, db.ForeignKey('users.nudoss'))
    name           = db.Column(db.String)
    lastname       = db.Column(db.String)
    email          = db.Column(db.String, nullable=False)
    valid          = db.Column(db.Boolean, default=False)
    birthday       = db.Column(db.String)
    last_connected = db.Column(db.String, nullable=False)
    num_connected  = db.Column(db.Integer, default=1)

    def __init__(self, user_nudoss, user_mail):
        self.user_attached  = user_nudoss
        self.email          = user_mail
        self.last_connected = get_current_timestamp()

    def set_optionnals(self, post_dict):
        if 'name' in post_dict:
            self.name     = post_dict['name']
        if 'lastname' in post_dict:
            self.lastname = post_dict['lastname']
        if 'birthday' in post_dict:
            self.birthday = post_dict['birthday']

    def update_connection_infos(self):
        self.last_connected = get_current_timestamp()
        self.num_connected += 1

    def gen_validation_request(self):
        token  = gen_random_token(24)
        minfos = get_random_elem(MailSpool.query.all())
        mailer = SendMail(minfos.mail_server, minfos.mail_port, minfos.mail_username)
        # mailer.send_mail()
        return token


class Temp(db.Model):
    __tablename__    = 'temp'
    nudoss           = db.Column(db.Integer, primary_key=True)
    user_attached    = db.Column(db.Integer, db.ForeignKey('users.nudoss'))
    validation_token = db.Column(db.String)

    def __init__(self, user_nudoss):
        self.user_attached = user_nudoss

class MailSpool(db.Model):
    __tablename__ = 'mail_spool'
    nudoss        = db.Column(db.Integer, primary_key=True)
    mail_server   = db.Column(db.String, nullable=False)
    mail_port     = db.Column(db.Integer, default=587)
    mail_username = db.Column(db.String, nullable=False)
    full_sender   = db.Column(db.String, nullable=False)

    def __init__(self, mail_server, mail_username, mail_passwd, full_sender):
        self.mail_server   = mail_server
        self.mail_username = mail_username
        self.full_sender   = full_sender
        keyring.set_password(mail_server, mail_username, mail_passwd)

class Debt(db.Model):
    __tablename__ = 'debts'
    nudoss        = db.Column(db.Integer, primary_key=True)
    value         = db.Column(db.Float, nullable=False)
    paid          = db.Column(db.Float, nullable=False)
    debtor        = db.Column(db.Integer, db.ForeignKey('users.nudoss'))
    creditor      = db.Column(db.Integer, db.ForeignKey('users.nudoss'))

    def __init__(self, value, debtor, creditor, paid):
        self.value    = value
        self.paid     = paid
        self.debtor   = debtor
        self.creditor = creditor

#==========================================================================
#0
