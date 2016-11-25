# -*- coding: utf-8 -*-

""" Basic sugar for tornado around Application and RequestHandler """

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import logging
import json
from base64 import b64encode
from uuid import uuid4
# installed
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import tornado.web
import redis
# custom
import net.shksystem.common.constants as const

## Globals
# =============================================================================

logger = logging.getLogger()

## Classes and Functions
# =============================================================================


class BaseApplication(tornado.web.Application):

    def __init__(self, database_url, handlers):
        settings = {
                     "cookie_secret": b64encode(uuid4().bytes + uuid4().bytes)
                   }
        super().__init__(handlers, settings)

        self.ormdb = scoped_session(
                        sessionmaker(
                           autocommit=False,
                           autoflush=False,
                           bind=create_engine(
                                   database_url,
                                   convert_unicode=True
                                )))
        #Base.query = self.ormdb.query_property()
        self.redis = redis.Redis()
        self.redis_id = str(uuid4().hex).upper()[0:6]

class BaseHandler(tornado.web.RequestHandler):

    @property
    def ormdb(self):
        return self.application.ormdb

    @property
    def redis(self):
        return self.application.redis

    def respond(self, data, code=const.HTTP_OK, data_dump=True):
        self.set_header(const.HTTP_CONTENT_TYPE, const.HTTP_APPLICATION_JSON)
        self.set_status(int(code))
        data_write = data if not data_dump else json.dumps(data, indent=4)
        self.write(data_write)
        self.finish()

    def redis_uqit(self, constant_key, varname):
        return '{0}_{1}_{2}'.format(
                                 self.application.redis_id,
                                 constant_key,
                                 varname
                             )

#
