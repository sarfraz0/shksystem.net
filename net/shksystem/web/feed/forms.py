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
from wtforms import TextField, PasswordField, BooleanField, SelectField, \
        IntegerField
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
    is_admin = BooleanField('Has admin rights')


class AddUser(Form):
    pseudo = TextField('Pseudonnym', validators=[InputRequired()])
    password = PasswordField('New Password', validators=[InputRequired()])
    is_admin = BooleanField('Give admin rights')


class AddFeed(Form):
    name = TextField('Name', validators=[InputRequired()])
    category = TextField('Category', validators=[InputRequired()])
    regex = TextField('Regex', validators=[InputRequired()])
    strike_url = TextField('Strike API url', validators=[InputRequired()])
    kickass_url = TextField('Kickass feed url', validators=[InputRequired()])
    is_active = BooleanField('Activate feed', default=True)
    has_episodes = BooleanField('Has episodes')
    has_seasons = BooleanField('Has seasons')
    dest = TextField('Mailing list')


class ModifyFeed(Form):
    name = SelectField('Name', coerce=int)
    category = TextField('Category')
    regex = TextField('Regex')
    strike_url = TextField('Strike API url')
    kickass_url = TextField('Kickass feed url')
    is_active = BooleanField('Active feed')
    has_episodes = BooleanField('Has episodes')
    has_seasons = BooleanField('Has seasons')
    dest = TextField('Mailing list')


class RemoveFeed(Form):
    name = SelectField('Name', coerce=int)


class AddRule(Form):
    name = TextField('Name', validators=[InputRequired()])
    feed_k = SelectField('Related feed', coerce=int)
    is_active = BooleanField('Activate rule', default=True)


class ModifyRule(Form):
    name = SelectField('Name', coerce=int)
    is_active = BooleanField('Active rule')


class RemoveRule(Form):
    name = SelectField('Name', coerce=int)


class AddMailServer(Form):
    hostname = TextField('Hostname', validators=[InputRequired()])
    port = IntegerField('Port')
    username = TextField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    sender = TextField('Sender', validators=[InputRequired()])


class ModifyMailServer(Form):
    server   = SelectField('Server', coerce=int)
    hostname = TextField('Hostname')
    port     = IntegerField('Port')
    username = TextField('Username')
    password = PasswordField('Password')
    sender   = TextField('Sender')


class RemoveMailServer(Form):
    server = SelectField('Server', coerce=int)


# ------------------------------------------------------------------------------
#
