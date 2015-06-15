# -*- coding: utf-8 -*-

""""
    OBJET            : Flask WTF forms
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 08.06.2015
    LICENSE          : GPL-3
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# standard
# installed
from flask_wtf import Form
from wtforms import TextField, PasswordField, BooleanField, SelectField
from wtforms.validators import InputRequired
# custom

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------
# NONE
# ------------------------------------------------------------------------------
# Classes and Functions
# ------------------------------------------------------------------------------


class LoginForm(Form):
    pseudo = TextField('Pseudonym', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class RemoveUser(Form):
    pseudo = SelectField('Pseudonym', coerce=int)


class ModifyUser(Form):
    pseudo = SelectField('Pseudonnym', coerce=int)
    password = PasswordField('New Password')
    is_admin = BooleanField('Give/Keep admin rights')


class AddUser(Form):
    pseudo = TextField('Pseudonnym', validators=[InputRequired()])
    password = PasswordField('New Password', validators=[InputRequired()])
    is_admin = BooleanField('Give admin rights')


class AddFeed(Form):
    name = TextField('Name', validators=[InputRequired()])
    regex = TextField('Regex', validators=[InputRequired()])
    strike_url = TextField('Strike API url', validators=[InputRequired()])
    kickass_url = TextField('Kickass feed url', validators=[InputRequired()])
    is_active = BooleanField('Activate feed', default=True)
    has_episodes = BooleanField('Has episodes')
    has_seasons = BooleanField('Has seasons')


class ModifyFeed(Form):
    name = SelectField('Name', coerce=int)
    regex = TextField('New Regex')
    strike_url = TextField('New strike API url')
    kickass_url = TextField('New kickass feed url')
    is_active = BooleanField('Keep feed active')
    has_episodes = BooleanField('Still has episodes')
    has_seasons = BooleanField('Still has seasons')


class AddRule(Form):
    name = TextField('Name', validators=[InputRequired()])
    feed_k = SelectField('Related feed', coerce=int)
    is_active = BooleanField('Activate rule', default=True)


class ModifyRule(Form):
    name = SelectField('Name', coerce=int)
    is_active = BooleanField('Keep rule active')


# ------------------------------------------------------------------------------
#
