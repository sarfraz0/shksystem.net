#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
import json
#from pprint import pprint
# installed
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from tornado import gen, autoreload
from tornado.ioloop import IOLoop
import tornado.web
#import psycopg2
#import momoko
import keyring
# custom
from net.shksystem.db.budget import Base, User, Status, Role

## Globals
# =============================================================================

logger = logging.getLogger()

MAX_WORKERS=4

## Functions and Classes
# =============================================================================


class Application(tornado.web.Application):

    def __init__(self, database_url):
        handlers = [
                     (r"/api/v1/users?", UserHandler)
                   ]
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


class BaseHandler(tornado.web.RequestHandler):

    #@property
    #def momodb(self):
    #    return self.application.momodb

    @property
    def ormdb(self):
        return self.application.ormdb

    def respond(self, data, code=200):
        self.set_header('Content-Type', 'application/json')
        self.set_status(code)
        self.write(json.dumps(data, indent=4))
        self.finish()


class UserHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def initialize(self):
        self.p_id = self.ormdb.query(Status) \
                              .filter_by(name='pending').first().cid
        self.d_role = self.ormdb.query(Role) \
                                .filter_by(name='user').first()

    @run_on_executor
    def get_user_by_cid(self, usercid):
        return self.ormdb.query(User).get(usercid)

    @run_on_executor
    def create_user(
           self,
           pseudo,
           password,
           init_status_cid,
           email=None
        ):
        ret = {}
        usr = User(pseudo, password, init_status_cid)
        if email is not None:
            usr.email = email
        try:
            self.ormdb.add(usr)
            self.ormdb.flush()
            ret = {
                    'new_usr_id': usr.cid
                  , 'new_usr': usr.to_dict()
                  }
            self.ormdb.commit()
        except Exception as e:
            # ret_code = 400
            #err_msg = 'user already exist'
            #logger.debug(err_msg)
            #logger.debug(repr(e))
            #ret = {
            #        'status_code': ret_code
            #      , 'message': err_msg
            #      }
            ret = {
                    'status_code': 400
                  , 'message': 'user already exist'
                  }
        return ret

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = 200
        try:
            usercid = self.get_argument('userid')
            if usercid.isdigit():
                cast_usercid = int(usercid)
                us = yield self.get_user_by_cid(cast_usercid)
                if us is not None:
                    ret = us.to_dict()
                else:
                    #ret_code = 404
                    #err_msg = 'cant get user object from given userid'
                    #logger.debug(err_msg)
                    #ret = {
                    #        'status_code': ret_code
                    #      , 'message': err_msg
                    #      }
                    ret = {
                            'status_code': 404
                          , 'message': 'cant get user object from given userid'
                          }

                #req1 = """SELECT pseudo, email
                #          FROM users
                #          WHERE cid={0}
                #       """.format(cast_usercid,)

                #req2 = """SELECT hostname, port, username, sender
                #          FROM mail_servers
                #          WHERE user_cid={0}
                #       """.format(cast_usercid,)

                #req3 = """SELECT name
                #          FROM roles r
                #          WHERE NOT EXISTS
                #                   (SELECT * FROM users u
                #                    WHERE cid={0}
                #                    AND NOT EXISTS
                #                           (SELECT *
                #                            FROM roles_users ru
                #                            WHERE ru.role_cid = r.cid
                #                            AND ru.user_cid = u.cid))
                #       """.format(cast_usercid,)
                #req4 = """SELECT name
                #          FROM statuses
                #          WHERE cid=(SELECT status_cid
                #                     FROM users
                #                     WHERE cid={0})
                #       """.format(cast_userid,)

                #try:
                #    f1 = self.momodb.execute(req1)
                #    f2 = self.momodb.execute(req2)
                #    f3 = self.momodb.execute(req3)
                #    f4 = self.momodb.execute(req4)
                #    yield [f1, f2, f3, f4]

                #    c1 = f1.result()
                #    c2 = f2.result()
                #    c3 = f3.result()
                #    c4 = f4.result()
                #except (psycopg2.Warning, psycopg2.Error):
                #    ret_code = 404
                #    ret = {
                #            'status_code': ret_code
                #          , 'message': 'cant get user object from given userid'
                #          }
                #else:
                #    try:
                #        user = c1.fetchone()
                #        ret['pseudo'] = user[0]
                #        ret['email']  = user[1]
                #        wrap = lambda x: {'hostname' : x[0]
                #                         , 'port'    : x[1]
                #                         , 'username': x[2]
                #                         , 'sender'  : x[3] }
                #        ret['mail_servers'] = [wrap(x) for x in c2.fetchall()]
                #        ret['roles'] = [x[0] for x in c3.fetchall()]
                #        ret['status'] = c4.fetchone()[0]
                #    except TypeError:
                #        ret_code = 404
                #        ret = {
                #                'status_code': ret_code
                #              , 'message': 'inexistant user for given userid'
                #              }
                #        ret_code = 404
            else:
                #ret_code = 404
                #err_msg = 'userid parameter must be a positive integer'
                #logger.debug(err_msg)
                #ret = {
                #        'status_code': ret_code
                #      , 'message': 'err_msg'
                #      }
                ret = {
                        'status_code': 400
                      , 'message': 'userid parameter must be a positive integer'
                      }

        except tornado.web.MissingArgumentError as e:
            #ret_code = 404
            #err_msg = 'parameter userid must be provided'
            #logger.debug(err_msg)
            #logger.debug(repr(e))
            #ret = {
            #        'status_code': ret_code
            #      , 'message': err_msg
            #      }
            ret = {
                    'status_code': 400
                  , 'message': 'parameter userid must be provided'
                  }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = 200
        try:
            pseudo = self.get_argument('pseudo')
            email = self.get_argument('email', default=None)
            password = self.get_argument('password')

            ret = yield self.create_user(pseudo, password, self.p_id, email)
            if 'status_code' in ret:
                ret_code = ret['status_code']

        except tornado.web.MissingArgumentError as e:
            #ret_code = 400
            #err_msg = 'post form is missing required data'
            #logger.debug(err_msg)
            #logger.debug(repr(e))
            #ret = {
            #        'status_code': ret_code
            #      , 'message': err_msg
            #      }
            ret = {
                    'status_code': 400
                  , 'message': 'post form is missing required data'
                  }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def put(self):
        ret = {}
        ret_code = 200
        try:
            usercid = self.get_argument('userid')
            email = self.get_argument('email', default=None)
            password = self.get_argument('password')

            ret = yield self.update_user(usercid, password, self.p_id, email)
            if 'status_code' in ret:
                ret_code = ret['status_code']

        except tornado.web.MissingArgumentError as e:
            ret = {
                    'status_code': 400
                  , 'message': 'post form is missing required data'
                  }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = 200
        try:
            usercid = self.get_argument('userid')
            if usercid.isdigit():
                cast_usercid = int(usercid)
                us = yield self.get_user_by_cid(cast_usercid)
                if us is not None:
                    self.ormdb.delete(us)
                    self.ormdb.commit()
                else:
                    ret = {
                            'status_code': 404
                          , 'message': 'cant get user object from given userid'
                          }
            else:
                ret = {
                        'status_code': 400
                      , 'message': 'userid parameter must be a positive integer'
                      }
        except tornado.web.MissingArgumentError as e:
            ret = {
                    'status_code': 400
                  , 'message': 'parameter userid must be provided'
                  }

        self.respond(ret, ret_code)

def run_api(database_url, port=8180, debug=False):
    app = Application(database_url)
    app.listen(port)
    ioloop = IOLoop.instance()
    #app.momodb = momoko.Pool(
    #                       os.environ['BUDGET_DATABASE_URI'],
    #                       size=1,
    #                       ioloop=ioloop
    #                    )
    #future = app.momodb.connect()
    #ioloop.add_future(future, lambda f: ioloop.stop())
    #ioloop.start()
    #future.result()  # raises exception on connection error
    if debug:
        autoreload.start(ioloop)
    ioloop.start()

#
