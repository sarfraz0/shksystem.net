# -*- coding: utf-8 -*-

"""
    OBJET            : Flask routes
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 21.04.2015
    LICENSE          : GPL-3
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# standard
import os
import logging
# installed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import Flask, render_template, request
# , redirect, url_for, session, flash
# custom
import net.shksystem.scripts.rssget as rs
import net.shksystem.scripts.dllrange as dl

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# FLASK INIT
# -------------------------------------------------------------------------

app = Flask(__name__)

# DATABASE
# -------------------------------------------------------------------------

FeedSession = sessionmaker(bind=create_engine(os.environ['FEED_URI']))
fdb = FeedSession()
RangeSession = sessionmaker(bind=create_engine(os.environ['RANGE_URI']))
rdb = RangeSession()

# -----------------------------------------------------------------------------
# Classes & Functions
# -----------------------------------------------------------------------------
# NONE
# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@app.route('/', methods=['GET', 'POST'])
def index():
    ret = render_template('index.html', feeds=fdb.query(rs.Rule).all(),
                          ranges=rdb.query(dl.Rule).all())
    if request.method == 'POST':
        pass
    else:
        pass
    return ret

# -----------------------------------------------------------------------------
# End seq
# -----------------------------------------------------------------------------
#
