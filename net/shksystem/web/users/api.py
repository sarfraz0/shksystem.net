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
from passlib.hash import sha512_crypt
# custom
from net.shksystem.db.users import Base, User, Status, Role, MailServer

## Globals
# =============================================================================

logger = logging.getLogger()

MAX_WORKERS=4

## Functions and Classes
# =============================================================================


class Application(tornado.web.Application):

    def __init__(self, database_url):
        handlers = [
                     (r'/api/v1/info', InfoHandler)
                   , (r'/api/v1/roles', RoleHandler)
                   , (r'/api/v1/statuses', StatusHandler)
                   , (r'/api/v1/mail_servers', MailServerHandler)
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


class InfoHandler(BaseHandler):

    def get(self):
        ret = {}
        ret_code = 200

        ret['base_api_url'] = '/api/v1'
        e_info = {
            'info':
            {
                'allowed_methods':
                [
                    {
                        'GET':
                        {
                            'arguments': None,
                            'action': 'print this help'
                        }
                    }
                ]
            }
        }
        e_users = {
            'users':
            {
                'allowed_methods':
                {
                    'GET':
                    {
                        'arguments':
                        [
                            {
                                'position': 1,
                                'name': 'pseudo',
                                'nullable': False,
                                'description': 'username corresponding to the unique pseudo for which info must be fetched'
                            }
                        ],
                        'action': 'show user description',
                        'curl_example': 'curl -X GET "https://$host/api/v1/users?pseudo=example"'
                    },
                    'POST':
                    {
                        'arguments':
                        [
                            {
                                'position': 1,
                                'name': 'pseudo',
                                'nullable': False,
                                'description': 'username of new user - must be unique'
                            },
                            {
                                'position': 2,
                                'name': 'password',
                                'nullable': False,
                                'description': 'password of the new user'
                            },
                            {
                                'position': 3,
                                'name': 'email',
                                'nullable': True,
                                'description': 'email of the new user (null if not present)'
                            }
                        ],
                        'action': 'create new user',
                        'curl_example': 'curl -X POST -F "pseudo=example" -F "password=example" -F "email=example@mail.com" "https://$host/api/v1/users"'
                    }
                    'PUT':
                    {
                        'arguments':
                        [
                            {
                                'position': 1,
                                'name': 'pseudo',
                                'nullable': False,
                                'description': 'username corresponding to the unique pseudo which need update'
                            },
                            {
                                'position': 2,
                                'name': 'password',
                                'nullable': True,
                                'description': 'new password of the user'
                            },
                            {
                                'position': 3,
                                'name': 'email',
                                'nullable': True,
                                'description': 'new email of the user'
                            },
                            {
                                'position': 4,
                                'name': 'status',
                                'nullable': True,
                                'description': 'account status of the user - must be taken from the statuses endpoint'
                            },
                            {
                                'position': 5,
                                'name': 'roles',
                                'nullable': True,
                                'description': 'roles of the user - must be a ";" concatenated list of roles taken from the roles endpoint'
                            }
                        ],
                        'action': 'update user given new fields; no change if optionnal field is ommited or invalid',
                        'curl_example': 'curl -X PUT -F "pseudo=example" -F "password=example" -F "email=example@mail.com" "https://$host/api/v1/users"'
                    }
                }
            }
        }
        ret['endpoints'] = [ e_info, e_users ]

        self.respond(ret, ret_code)


class MailServerHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @run_on_executor
    def create_server(
           self,
           hostname,
           port,
           username,
           sender,
           owner=None
        ):
        ret = {}
        ret_code = 200

        g_user=None
        if owner is not None:
            g_user = self.ormdb.query(User).filter_by(pseudo=owner).first()
        serv = MaiServer(hostname, port, username, password, sender, g_user)

        try:
            self.ormdb.add(serv)
            self.ormdb.flush()
            ret = {
                    'status_code': ret_code
                  , 'new_server_id': serv.cid
                  , 'new_server': serv.to_dict()
                  }
            self.ormdb.commit()
        except exc.IntegrityError as e:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'mail_server already exists'
                  }
        except Exception as e:
            logger.exception('Unhandled Exception')
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'Unhandled Exception'
                  }

        return ret

    @run_on_executor
    def update_server(
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
        ret_code = 200
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
        ret_code = 200

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
            logger.exception('Unhandled Exception')
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
        ret_code = 200
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

                if email is not None:
                    usr.email = email

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


def run_api(database_url, port=8080, debug=False):
    app = Application(database_url)
    app.listen(port)
    ioloop = IOLoop.instance()
    if debug:
        autoreload.start(ioloop)
    ioloop.start()

#
