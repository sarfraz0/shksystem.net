
# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Flask routes
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 25.12.2014
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

# Standard
import os
import sys
import logging
# Environment defined
from flask import Flask, render_template, request, redirect, url_for, session, flash
# User defined

#==========================================================================
# Environment/Parameters/Static variables
#==========================================================================

logger = logging.getLogger(__name__)

# -- FLASK INIT
# -------------------------------------------------------------------------
app = Flask(__name__)

#==========================================================================
# Classes/Functions
#==========================================================================
# NONE
#==========================================================================
# Routes
#==========================================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    list_range = []
    ctx = None
    c = None
    try:
        ctx = psycopg2.connect(app.config['RANGE_URL'])
        c = ctx.cursor()
        c.execute('')
        list_range = c.fetchall()
    except:
        logger.exception('')
    finally:
        if c is not None:
            c.close()
        if ctx is not None:
            ctx.close()

    list_rss = []
    ctx2 = None
    c2 = None
    try:
        ctx2 = psycopg2.connect(app.config['RSS_URL'])
        c2 = ctx.cursor()
        c2.execute('')
        list_rss = c2.fetchall()
    except:
        logger.exception('')
    finally:
        if c2 is not None:
            c2.close()
        if ctx2 is not None:
            ctx2.close()

    ret = render_template('index.html', rsss=list_rss, ranges=list_range)
    return ret

#==========================================================================
# End sequence
#==========================================================================
#0
