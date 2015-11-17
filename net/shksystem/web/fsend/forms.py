# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# installed
from flask_wtf import Form
from wtforms import TextField, PasswordField, BooleanField, SelectField, \
        IntegerField
from wtforms.validators import InputRequired

# Classes and Functions
# -----------------------------------------------------------------------------


class LoginForm(Form):
    pseudo = TextField('Pseudonym', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class RemoveUser(Form):
    pseudo = SelectField('Pseudonym', coerce=int)


class ModifyUser(Form):
    pseudo = SelectField('Pseudonnym', coerce=int)
    password = PasswordField('New Password')
    is_admin = BooleanField('Has admin rights')
    is_manager = BooleanField('Has managing rights')


class AddUser(Form):
    pseudo = TextField('Pseudonnym', validators=[InputRequired()])
    password = PasswordField('New Password', validators=[InputRequired()])
    is_admin = BooleanField('Give admin rights')
    is_manager = BooleanField('Give managing rights')


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


# -----------------------------------------------------------------------------
#
