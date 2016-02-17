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
from passlib.hash import sha512_crypt
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
                     (r'/api/v1/roles', RoleHandler)
                   , (r'/api/v1/statuses', StatusHandler)
                   , (r'/api/v1/users', UserHandler)
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

    @property
    def ormdb(self):
        return self.application.ormdb

    def respond(self, data, code=200):
        self.set_header('Content-Type', 'application/json')
        self.set_status(code)
        self.write(json.dumps(data, indent=4))
        self.finish()


class RoleHandler(BaseHandler):

    def get(self):
        ret = {}
        ret_code = 200
        roles = self.ormdb.query(Role).all()
        for r in roles:
            ret[r.cid] = r.name
        self.respond(ret, ret_code)


class StatusHandler(BaseHandler):

    def get(self):
        ret = {}
        ret_code = 200
        roles = self.ormdb.query(Status).all()
        for r in roles:
            ret[r.cid] = r.name
        self.respond(ret, ret_code)


class UserHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def initialize(self):
        self.d_status = self.ormdb.query(Status) \
                                  .filter_by(name='pending').first()
        self.d_role = self.ormdb.query(Role) \
                                .filter_by(name='user').first()

    @run_on_executor
    def get_user_by_name(self, name):
        return self.ormdb.query(User).filter_by(pseudo=name).first()

    @run_on_executor
    def create_user(
           self,
           pseudo,
           password,
           status,
           roles=None,
           email=None
        ):
        ret = {}
        usr = User(pseudo, password, status)
        if roles is not None:
            for role in roles:
                usr.roles.append(role)
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
            ret = {
                    'status_code': 400
                  , 'message': 'user already exist'
                  }
        return ret

    @run_on_executor
    def update_user(
           self,
           pseudo,
           password=None,
           status_name=None,
           roles_list=None,
           email=None
        ):
        """
            update_user :: Self
                        -> String
                        -> Maybe String
                        -> Maybe String
                        -> Maybe [String]
                        -> Maybe String
                        -> IO Map String String
            ===================================
            This function updates an user object in database
        """
        ret = {}

        if usercid.isdigit():
            usr = self.ormdb.query(User).get(int(usercid))
            if usr is not None:
                try:
                    if password is not None:
                        usr.passwhash = sha512_crypt.encrypt(password)
                    if statuscid is not None:
                        usr.status = self.ormdb.query(Status).get(statuscid)
                    if roles_cid_list is not None:
                        for role_cid in roles_cid_list:
                            current_role = self.ormdb.query(Role).get(role_cid)
                            if current_role not in usr.roles:
                                usr.roles.append(current_role)

                    ret = {
                            'updated_usr_id': usr.cid
                          , 'updated_usr': usr.to_dict()
                          }
                    self.ormdb.commit()
                except Exception as e:
                    ret = {
                            'status_code': 400
                          , 'message': 'user could not be updated'
                          }
            else:
                ret = {
                        'status_code': 404
                      , 'message': 'user does not exist'
                      }
        else:
            ret = {
                    'status_code': 404
                  , 'message': 'userid must be valid'
                  }

        return ret

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = 200
        try:
            pseudo = self.get_argument('pseudo')
            us = yield self.get_user_by_name(pseudo)
            if us is not None:
                ret = us.to_dict()
            else:
                ret = {
                        'status_code': 404
                      , 'message': 'cant get user object from given pseudo'
                      }
        except tornado.web.MissingArgumentError as e:
            ret = {
                    'status_code': 400
                  , 'message': 'parameter pseudo must be provided'
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

            d_status = self.d_status
            d_roles = [self.d_role]
            ret = yield self.create_user(pseudo, password, d_status, d_roles, email)
            if 'status_code' in ret:
                ret_code = ret['status_code']

        except tornado.web.MissingArgumentError as e:
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
            pseudo          = self.get_argument('pseudo')
            email           = self.get_argument('email',    default=None)
            password        = self.get_argument('password', default=None)
            status_name     = self.get_argument('status',   default=None)
            raw_roles_list  = self.get_argument('roles',    default=None)

            roles_list = None
            if raw_roles_list is not None:
                roles_list= filter(lambda x: x != '', raw_roles_list.split(';'))

            ret = yield self.update_user(
                                pseudo,
                                password,
                                status_name,
                                roles_list,
                                email
                             )
            if 'status_code' in ret:
                ret_code = ret['status_code']

        except tornado.web.MissingArgumentError as e:
            ret = {
                    'status_code': 400
                  , 'message': 'put form is missing required data'
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
                us = self.ormdb.query(User).get(cast_usercid)
                if us is not None:
                    self.ormdb.delete(us)
                    self.ormdb.commit()
                else:
                    ret = {
                            'status_code': 404
                          , 'message': 'cant delete user object from given userid'
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
    if debug:
        autoreload.start(ioloop)
    ioloop.start()

#
