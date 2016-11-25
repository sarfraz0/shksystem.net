# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# installed
from flask_wtf import Form
from wtforms import TextField, PasswordField, BooleanField, SelectField, \
        IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Required, Optional, Email

## Globals
# =============================================================================

## Functions and Classes
# =============================================================================


class LoginForm(Form):
    pseudo   = TextField('Pseudonym', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])


class RemoveUser(Form):
    pseudo = SelectField('Pseudonym', coerce=int)


class ModifyUser(Form):
    pseudo   = SelectField('Pseudonnym', coerce=int)
    email    = EmailField('Email', validators=[Email(), Optional()])
    password = PasswordField('New Password')
    status   = SelectField('Status', coerce=int)


class AddUser(Form):
    pseudo   = TextField('Pseudonnym', validators=[Required()])
    email    = EmailField('Email', validators=[Email(), Optional()])
    password = PasswordField('New Password', validators=[Required()])
    status   = SelectField('Status', coerce=int)


class AddMailServer(Form):
    hostname = TextField('Hostname', validators=[Required()])
    port = IntegerField('Port')
    username = TextField('Username', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    sender = TextField('Sender', validators=[Required()])


class ModifyMailServer(Form):
    server   = SelectField('Server', coerce=int)
    hostname = TextField('Hostname')
    port     = IntegerField('Port')
    username = TextField('Username')
    password = PasswordField('Password')
    sender   = TextField('Sender')


class RemoveMailServer(Form):
    server = SelectField('Server', coerce=int)


#
