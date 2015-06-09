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
    is_admin = BooleanField('Give admin rights', default=False)


class AddUser(Form):
    pseudo = TextField('Pseudonnym', validators=[InputRequired()])
    password = PasswordField('New Password', validators=[InputRequired()])
    is_admin = BooleanField('Give admin rights', default=False)


# ------------------------------------------------------------------------------
#
