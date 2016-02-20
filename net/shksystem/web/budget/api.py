#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
import json
# installed
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from tornado import gen, autoreload
from tornado.ioloop import IOLoop
import tornado.web
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

    @run_on_executor
    def create_user(
           self,
           username,
           password,
           email=None
        ):
        ret = {}

        d_status = self.ormdb.query(Status).filter_by(name='pending').first()
        usr = User(username, password, d_status)

        d_role = self.ormdb.query(Role).filter_by(name='user').first()
        usr.roles.append(d_role)

        if email is not None:
            usr.email = email

        try:
            self.ormdb.add(usr)
            self.ormdb.flush()
            ret = {
                    'status_code': ret_code
                  , 'new_usr_id': usr.cid
                  , 'new_usr': usr.to_dict()
                  }
            self.ormdb.commit()
        except exc.IntegrityError as e:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'user already exists'
                  }
        except Exception as e:
            logger.exception('user already exists')
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'Unhandled Exception'
                  }

        return ret

    @run_on_executor
    def update_user(
           self,
           username,
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
        usr = self.ormdb.query(User).filter_by(pseudo=username).first()
        if usr is not None:
            try:
                if password is not None:
                    usr.passwhash = sha512_crypt.encrypt(password)

                if status_name is not None:
                    c_stat = self.ormdb.query(Status) \
                                       .filter_by(name=status_name).first()
                    if c_stat is not None:
                        usr.status = c_stat

                t_roles = []
                if roles_list is not None:
                    for role_name in roles_list:
                        c_role = self.ormdb.query(Role) \
                                           .filter_by(name=role_name).first()
                        if c_role is not None:
                            t_roles.append(c_role)
                    usr.roles = t_roles

                ret = {
                        'status_code': ret_code
                      , 'updated_usr_id': usr.cid
                      , 'updated_usr': usr.to_dict()
                      }
                self.ormdb.commit()
            except Exception as e:
                logger.exception('user could not be updated')
                ret = {
                        'status_code': 400
                      , 'message': 'user could not be updated'
                      }
        else:
            ret = {
                    'status_code': 404
                  , 'message': 'user does not exist'
                  }
        return ret

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = 200
        try:
            username = self.get_argument('pseudo')
            us = self.ormdb.query(User).filter_by(pseudo=username).first()
            if us is not None:
                ret = us.to_dict()
            else:
                ret_code = 404
                ret = {
                        'status_code': ret_code
                      , 'message': 'inexistant user object for given pseudo'
                      }
        except tornado.web.MissingArgumentError as e:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'valid pseudo parameter must be provided'
                  }
        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = 200
        try:
            username = self.get_argument('pseudo')
            email    = self.get_argument('email', default=None)
            password = self.get_argument('password')

            ret = yield self.create_user(username, password, email)
            if 'status_code' in ret:
                ret_code = ret['status_code']

        except tornado.web.MissingArgumentError as e:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'post form is missing required data'
                  }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def put(self):
        ret = {}
        ret_code = 200
        try:
            username        = self.get_argument('pseudo')
            email           = self.get_argument('email',    default=None)
            password        = self.get_argument('password', default=None)
            status_name     = self.get_argument('status',   default=None)
            raw_roles_list  = self.get_argument('roles',    default=None)

            roles_list = None
            if raw_roles_list is not None:
                roles_list= filter(lambda x: x != '', raw_roles_list.split(';'))

            ret = yield self.update_user(
                                username,
                                password,
                                status_name,
                                roles_list,
                                email
                             )
            if 'status_code' in ret:
                ret_code = ret['status_code']

        except tornado.web.MissingArgumentError as e:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'put form is missing required data'
                  }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = 200
        try:
            username = self.get_argument('pseudo')
            us = self.ormdb.query(User).filter_by(pseudo=username).first()
            if us is not None:
                self.ormdb.delete(us)
                self.ormdb.commit()

                ret = { 'status_code': ret_code, 'deleted_usr_id': us.cid }
            else:
                ret_code = 404
                ret = {
                        'status_code': ret_code
                      , 'message': 'cant delete user object for given pseudo'
                      }
        except tornado.web.MissingArgumentError as e:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'pseudo parameter must be provided'
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
