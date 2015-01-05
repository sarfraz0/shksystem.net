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

# -- LIVRAISON MODELS
# -------------------------------------------------------------------------
class Environment(db.Model):
    __tablename__ = "environments"
    nudoss        = db.Column(db.Integer, primary_key=True)
    envName       = db.Column(db.String)
    applName      = db.Column(db.String, nullable=False)
    hostname      = db.Column(db.String, nullable=False)
    envGroup      = db.Column(db.String, nullable=False)
    component     = db.Column(db.String, nullable=False)
    userName      = db.Column(db.String, nullable=False)
    userGroup     = db.Column(db.String, nullable=False)

    def __init__(self, envName, applName, hostname, envGroup, component, userName, userGroup):
        self.envName   = envName
        self.applName  = applName
        self.hostname  = hostname
        self.envGroup  = envGroup
        self.component = component
        self.userName  = userName
        self.userGroup = userGroup

class UserConf(db.Model):
    __tablename__ = "usersconf"
    # nudoss here is equal to the user nudoss
    # because one to one relationship
    # avoid having to write bothersome ORM
    nudoss        = db.Column(db.Integer, primary_key=True)
    javaUtilsUrl  = db.Column(db.String, nullable=False)
    svnUser       = db.Column(db.String, nullable=False)
    svnPasswd     = db.Column(db.String, nullable=False)
    hopUser       = db.Column(db.String, nullable=False)
    hopPasswd     = db.Column(db.String, nullable=False)

    def __init__(self, curUserID, javaUtilsUrl, svnUser, svnPasswd, hopUser, hopPasswd):
        self.nudoss       = curUserID
        self.javaUtilsUrl = javaUtilsUrl
        self.svnUser      = svnUser
        self.svnPasswd    = svnPasswd
        self.hopUser      = hopUser
        self.hopPasswd    = hopPasswd

#==========================================================================
#0
