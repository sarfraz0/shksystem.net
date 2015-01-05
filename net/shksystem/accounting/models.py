# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Flask data manipulation
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 25.11.2014
#@(#) LICENSE          : GPL-3
#@(#)----------------------------------------------------------------------

#==========================================================================
#
# DEPENDENCIES
# NONE
#
# WARNINGS
# NONE
#
#==========================================================================

#==========================================================================
# Imports
#==========================================================================

from passlib.hash         import sha512_crypt
from flask.ext.sqlalchemy import SQLAlchemy

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
    isAdmin       = db.Column(db.Boolean, nullable=False)

    def __init__(self, pseudo, passw, isAdmin):
        self.pseudo     = pseudo
        self.passwhash  = sha512_crypt.encrypt(passw)
        self.isAdmin    = isAdmin

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.nudoss)

# -- ACCOUNTING MODELS
# -------------------------------------------------------------------------
class Debt(db.Model):
    __tablename__ = "debts"
    nudoss        = db.Column(db.Integer, primary_key=True)
    value         = db.Column(db.Float, nullable=False)
    paid          = db.Column(db.Boolean, default=False)
    # debtor and creditor equal nudoss of an User
    debtor        = db.Column(db.Integer, nullable=False)
    creditor      = db.Column(db.Integer, nullable=False)

    def __init__(self, val, deb, cre, pad=False):
        self.value    = val
        self.paid     = pad
        self.debtor   = deb
        self.creditor = cre

#==========================================================================
#0
