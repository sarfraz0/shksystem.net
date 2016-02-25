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
import keyring
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
                     (r'/api/v1/roles', RoleHandler)
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


class MailServerHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @run_on_executor
    def create_server(self, host, prt, usern, passwd, sendr, owner_name=None):
        ret = {}
        ret_code = 200

        owner=None
        if owner_name is not None:
            owner = self.ormdb.query(User).filter_by(pseudo=owner_name).first()
        serv = MaiServer(hostname, port, username, password, sender, owner)

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
    def update_server(self, host, usern, prt=None, passwd=None, sendr=None, owner_name=None):
        """
            update_server :: Self -> String -> String -> Maybe Int -> Maybe String -> Maybe String -> Maybe String -> IO Dict
            ================================================
            This function updates a mail_server object in database
        """
        ret = {}
        ret_code = 200
        srv = self.ormdb.query(MailServer).filter_by(hostname=host, username=usern).first()
        if srv is not None:
            try:
                if passwd is not None:
                    keyring.set_password(srv.hostname, srv.username, passwd)

                if prt is not None:
                    serv.port = prt

                if sendr is not None:
                    serv.sender = sendr

                final_ret = {
                              'status_code': ret_code
                            , 'updated_usr_id': usr.cid
                            , 'updated_usr': usr.to_dict()
                            }

                if owner_name is not None:
                    usr = self.ormdb.query(User).filter_by(pseudo=owner_name).first()
                    if usr is None:
                        ret = {
                              }
                    else:
                        srv.owner = usr
                        ret = final_ret
                else:
                    ret = final_ret

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
                  , 'message': 'mail_server does not exist'
                  }
        return ret

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = 200
        try:
            host = self.get_argument('hostname')
            usern = self.get_argument('username')
            us = self.ormdb.query(User).filter_by(hostname=host) \
                                       .filter_by(username=usrn).first()
            if us is not None:
                ret = us.to_dict()
            else:
                ret_code = 404
                ret = {
                        'status_code': ret_code
                      , 'message': 'inexistant mail_server object for given hostname/username pair'
                      }
        except tornado.web.MissingArgumentError as e:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'hostname and username parameters must be provided'
                  }
        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = 200
        try:
            host       = self.get_argument('hostname')
            prt        = self.get_argument('port')
            passwd     = self.get_argument('password')
            usern      = self.get_argument('username')
            sendr      = self.get_argument('mail_sender')
            owner_name = self.get_argument('pseudo', default=None)

            prt2 = int(prt)
            if not (prt2 in [25, 465, 587]):
                raise ValueError

            ret = yield self.create_server(host, usern, prt2, usern, passwd, sendr, owner_name)
            if 'status_code' in ret:
                ret_code = ret['status_code']

        except tornado.web.MissingArgumentError:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'post form is missing required data'
                  }
        except ValueError:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'port must be 25, 465 or 587'
                  }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def put(self):
        ret = {}
        ret_code = 200
        try:
            host       = self.get_argument('hostname')
            usern      = self.get_argument('username')
            prt        = self.get_argument('port', default=None)
            passwd     = self.get_argument('password', default=None)
            sendr      = self.get_argument('mail_sender', default=None)
            owner_name = self.get_argument('pseudo', default=None)

            if prt is not None:
                prt2 = int(prt)
                if not (prt2 in [25, 465, 587]):
                    raise ValueError

            ret = yield self.update_server(host, prt2, usern, passwd, sendr, owner_name)

            if 'status_code' in ret:
                ret_code = ret['status_code']

        except tornado.web.MissingArgumentError as e:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'put form is missing required data'
                  }
        except ValueError:
            ret_code = 400
            ret = {
                    'status_code': ret_code
                  , 'message': 'port must be 25, 465 or 587'
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
