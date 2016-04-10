# -*- coding: utf-8 -*-

""" Basic sugar for tornado around Application and RequestHandler """

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import logging
import json
# installed
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import tornado.web
import redis
# custom

## Globals
# =============================================================================

logger = logging.getLogger()

## Classes and Functions
# =============================================================================


class Application(tornado.web.Application):

    def __init__(self, database_url, handlers):
        tornado.web.Application.__init__(self, handlers)

        self.ormdb = scoped_session(
                        sessionmaker(
                           autocommit=False,
                           autoflush=False,
                           bind=create_engine(
                                   database_url,
                                   convert_unicode=True
                                )))
        Base.query = self.ormdb.query_property()
        self.redis = redis.Redis()


class BaseHandler(tornado.web.RequestHandler):

    @property
    def ormdb(self):
        return self.application.ormdb

    @property
    def redis(self):
        return self.application.redis

    def respond(self, data, code=constants.HTTP_OK, data_dump=True):
        self.set_header('Content-Type', 'application/json')
        self.set_status(int(code))
        data_write = data if not data_dump else json.dumps(data, indent=4)
        self.write(data_write)
        self.finish()


#
