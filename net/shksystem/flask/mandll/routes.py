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

#standard
import os
import sys
import logging
#installed
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
#custom

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
    logger.info('Index page.')
    if request.method == 'POST':
        pass
    else:
        if 'update_rss' not in session:
            logger.info('No update_rss in session. Setting it to true to grab data.')
            session['update_rss'] = True
        if 'update_range' not in session:
            logger.info('No update_range in session. Setting it to true to grab data.')
            session['update_range'] = True


        if ('ranges' not in session) or session['update_range']:
            logger.info('No data or update needed for ranges. Fetching...')
            ctx = None
            c = None
            try:
                ctx = psycopg2.connect(app.config['RANGE_URL'])
                c = ctx.cursor()
                c.execute('SELECT DISTINCT title, dest FROM rules')
                session['ranges'] = c.fetchall()
                session['update_range'] = False
            except:
                logger.exception('')
            finally:
                if c is not None:
                    c.close()
                if ctx is not None:
                    ctx.close()

        if ('rsss' not in session) or session['update_rss']:
            logger.info('No data or update needed for rss. Fetching...')
            ctx2 = None
            c2 = None
            try:
                ctx2 = psycopg2.connect(app.config['RSS_URL'])
                c2 = ctx2.cursor()
                c2.execute('SELECT DISTINCT r.title, f.url FROM rules AS r INNER JOIN feeds AS f ON r.feed_id = f.id')
                session['rsss'] = c2.fetchall()
                session['update_rss'] = False
            except:
                logger.exception('')
            finally:
                if c2 is not None:
                    c2.close()
                if ctx2 is not None:
                    ctx2.close()

            logger.info('Rendering index.')
            ret = render_template('index.html', rsss=session['rsss'], ranges=session['ranges'])

    return ret

#==========================================================================
# End sequence
#==========================================================================
#0
