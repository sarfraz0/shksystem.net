# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import logging
import json
import multiprocessing
import uuid
# installed
from sqlalchemy.exc
from tornado import autoreload
import tornado.web
import tornado.gen
from tornado.ioloop import IOLoop
import redis
# custom
import net.shksystem.common.constants as constants
import net.shksystem.common.api as api
from net.shksystem.db.logit import Category, SubCategory, Action, Flogger

## Globals
# =============================================================================

logger = logging.getLogger()

STATIC_CACHID=str(uuid.uuid4()).upper().replace('-', "")[0:6]

## Functions and Classes
# =============================================================================


class Application(api.Application):
    def __init__(self, database_url):
        handlers = [
                     (r'/api/v1/categories', CategoryHandler)
                   #, (r'/api/v1/subcategories', SubCategorHandler)
                   #, (r'/api/v1/floggers', FloggerHandler)
                   #, (r'/api/v1/actions', ActionHandler)
                   ]
        super(Application, self).__init__(database_url, handlers)


class CategoryHandler(api.BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        ret = []
        ret_code = constants.HTTP_OK

        categories = self.ormdb.query(Category).all()
        for c in categories:
            ret.append(c.name)

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = constants.HTTP_OK

        try:
            name = get_argument('name')
            cat = self.ormdb.query(Category).filter_by(name=name).first()
            if cat is not None:
                self.ormdb.delete(cat)
                self.ormdb.commit()
            else:
                ret_code = constants.HTTP_NOT_FOUND
                ret = { 'error': 'category does not exist' }

        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'missing category name parameter in request' }

        self.respond(ret, ret_code)

    def post(self):
        ret = {}
        ret_code = constants.HTTP_OK

        try:
            name = get_argument('name')
            self.ormdb.add(Category(name))
            self.ormdb.commit()

        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'missing requiered parameters' }
        except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.InvalidRequestError) as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'category already exist' }

        self.respond(ret, ret_code)


#
