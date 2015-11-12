# -*- coding: utf-8 -*-

"""
    DESCRIPTION   : Base configuration for flask wsgi script
    AUTHOR        : Sarfraz Kapasi
    CREATION DATE : 10.08.2015
    LICENSE       : GPL-3
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# standard
import os
import logging
import json
# installed
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
# custom
from net.shksystem.common.utils import init_logger

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
# NONE
# -----------------------------------------------------------------------------
# Classes and Functions
# -----------------------------------------------------------------------------


class WSGI(object):

    def __init__(self, app, db):
        cnf = {}
        with open(os.path.abspath('../etc/config.json')) as f:
            cnf = json.load(f)

        # FLASK CONFIG
        app.config['APP_NAME'] = cnf['APP_NAME']
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['SECRET_KEY'] = cnf['SECRET']
        app.config['SQLALCHEMY_DATABASE_URI'] = cnf['DATABASE_URI']

        self.app = app
        self.db = db

        self.logpath = cnf['LOGFILE']

    def run(self):
        logger = init_logger(self.logpath, logging.INFO)
        # FLASK ALCHEMY MIGRATION
        migrate = Migrate(self.app, self.db)
        manager = Manager(self.app)
        manager.add_command('db', MigrateCommand)
        self.app.config['DEBUG'] = True
        manager.run()


# -----------------------------------------------------------------------------
#
