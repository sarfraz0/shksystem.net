# -*- coding: utf-8 -*-

""""
    OBJET            : Flask routes
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 02.06.2015
    LICENSE          : GPL-3
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# standard
import logging
# installed
from flask import Flask, render_template, request, redirect, url_for, session, \
    flash
from flaskext.csrf import csrf
# custom

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# FLASK INIT
app = Flask(__name__)

# FLASK CSRF
csrf(app)

# FLASK ALCHEMY
#db.init_app(app)

# ------------------------------------------------------------------------------
# Classes and Functions
# ------------------------------------------------------------------------------
# NONE
# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------


@app.route('/', methods=['GET'])
def index():
    ret = render_template('index.html', release_names=['test1', 'test2'])
    return ret

# ------------------------------------------------------------------------------
#
