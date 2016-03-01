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
from concurrent.futures import ThreadPoolExecutor
from tornado import autoreload
import tornado.web
import tornado.gen
from tornado.ioloop import IOLoop
import redis
from passlib.hash import sha512_crypt
import keyring
# custom
from net.shksystem.db.users import Base, User, Status, Role, MailServer

## Globals
# =============================================================================

logger = logging.getLogger()

MAX_WORKERS=4
REDIS_CACHE_TIMEOUT=2700
STATIC_CACHID='C6CH4d'

HTTP_OK='200'
HTTP_BAD_REQUEST='400'
HTTP_NOT_FOUND='404'

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

        self.redis = redis.Redis()


class BaseHandler(tornado.web.RequestHandler):

    @property
    def ormdb(self):
        return self.application.ormdb

    @property
    def redis(self):
        return self.application.redis

    def respond(self, data, code=HTTP_OK, data_dump=True):
        self.set_header('Content-Type', 'application/json')
        self.set_status(int(code))
        data_write = data if not data_dump else json.dumps(data, indent=4)
        self.write(data_write)
        self.finish()


class MailServerHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @tornado.concurrent.run_on_executor
    def create_server(self, host, prt, usern, passwd, sendr, owner_name=None):
        """
            create_server :: Self
                          -> String               -- ^ smtp hostname
                          -> Int                  -- ^ smtp port
                          -> String               -- ^ smtp username
                          -> String               -- ^ smtp password
                          -> String               -- ^ identity email
                          -> Maybe String         -- ^ owner name
                          -> IO Map String String -- ^ request info
            ========================================================
            This method creates a new mail_server given proper infos
        """
        ret = {}

        owner=None
        if owner_name is not None:
            owner = self.ormdb.query(User).filter_by(pseudo=owner_name).first()

        serv = MailServer(host, prt, usern, passwd, sendr, owner)

        try:
            self.ormdb.add(serv)
            self.ormdb.flush()
            ret = { 'status_code': HTTP_OK
                  , 'message': serv.to_dict() }
            self.ormdb.commit()

        except exc.IntegrityError as e:
            ret = { 'status_code': HTTP_BAD_REQUEST
                  , 'error': 'mail_server already exists' }
        except Exception as e:
            logger.exception('Unhandled Exception')
            ret = { 'status_code': HTTP_BAD_REQUEST
                  , 'error': 'Unhandled Exception' }

        return ret

    @tornado.concurrent.run_on_executor
    def update_server(self, host, usern, prt=None, passwd=None, sendr=None,
                      owner_name=None):
        """
            update_server :: Self
                          -> String               -- ^ hostname of server
                          -> String               -- ^ username of server
                          -> Maybe Int            -- ^ new port
                          -> Maybe String         -- ^ new password
                          -> Maybe String         -- ^ new identity
                          -> Maybe String         -- ^ mail_server's owner
                          -> IO Map String String -- ^ request info
            ======================================================
            This function updates a mail_server object in database
        """
        ret = {}
        srv = self.ormdb.query(MailServer) \
                        .filter_by(hostname=host, username=usern).first()
        if srv is not None:
            try:
                if passwd is not None:
                    keyring.set_password(srv.hostname, srv.username, passwd)

                if prt is not None:
                    serv.port = prt

                if sendr is not None:
                    serv.sender = sendr

                final_ret = { 'status_code': HTTP_OK
                            , 'message': srv.to_dict() }

                if owner_name is not None:
                    usr = self.ormdb.query(User) \
                                    .filter_by(pseudo=owner_name).first()
                    if usr is None:
                        ret = { 'status_code': HTTP_NOT_FOUND
                              , 'error': 'owner does not exist' }
                    else:
                        srv.owner = usr
                        ret = final_ret
                else:
                    ret = final_ret

                self.ormdb.commit()

            except Exception as e:
                logger.exception('user could not be updated')
                ret = { 'status_code': HTTP_BAD_REQUEST
                      , 'error': 'user could not be updated' }
        else:
            ret = { 'status_code': HTTP_BAD_REQUEST
                  , 'error': 'mail_server does not exist' }

        return ret

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = HTTP_OK
        dp=True
        try:
            host = self.get_argument('hostname')
            usern = self.get_argument('username')

            uniq_redis_id = 'mail_servers_{0}{1}_{2}' \
                               .format(host, usern, STATIC_CACHID)
            red_res = self.redis.get(uniq_redis_id)
            if red_res is not None:
                ret = red_res
                dp=False
            else:
                us = self.ormdb.query(MailServer) \
                               .filter_by(hostname=host, username=usern).first()
                if us is not None:
                    ret = us.to_dict()
                    self.redis.set(uniq_redis_id, json.dumps(ret, indent=4))
                    self.redis.expire(uniq_redis_id, REDIS_CACHE_TIMEOUT)
                else:
                    ret_code = HTTP_NOT_FOUND
                    ret = { 'error': 'inexistant object for hostname/username pair' }

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'hostname and username must be provided' }

        self.respond(ret, ret_code, data_dump=dp)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = HTTP_OK
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

            res = yield self.create_server(host, prt2, usern, passwd, sendr,
                                           owner_name)
            ret_code = res.pop('status_code')
            ret = res if 'error' in res else res['message']

        except tornado.web.MissingArgumentError:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'post form is missing required data' }
        except ValueError:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'port must be 25, 465 or 587' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def put(self):
        ret = {}
        ret_code = HTTP_OK
        try:
            host       = self.get_argument('hostname')
            usern      = self.get_argument('username')
            prt        = self.get_argument('port', default=None)
            passwd     = self.get_argument('password', default=None)
            sendr      = self.get_argument('mail_sender', default=None)
            owner_name = self.get_argument('pseudo', default=None)

            prt2=None
            if prt is not None:
                prt2 = int(prt)
                if not (prt2 in [25, 465, 587]):
                    raise ValueError

            res = yield self.update_server(host, usern, prt2, passwd, sendr,
                                           owner_name)
            ret_code = res.pop('status_code')
            if 'error' in res:
                ret = res
            else:
                ret = res['message']
                uniq_redis_id = 'mail_servers_{0}{1}_{2}' \
                                   .format(host, usern, STATIC_CACHID)
                self.redis.set(uniq_redis_id, json.dumps(ret, indent=4))
                self.redis.expire(uniq_redis_id, REDIS_CACHE_TIMEOUT)


        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'put form is missing required data' }
        except ValueError:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'port must be 25, 465 or 587' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = HTTP_OK
        try:
            username = self.get_argument('pseudo')
            us = self.ormdb.query(User).filter_by(pseudo=username).first()
            if us is not None:
                self.ormdb.delete(us)
                self.ormdb.commit()

                ret = { 'deleted_usr_id': us.cid }
            else:
                ret_code = HTTP_NOT_FOUND
                ret = { 'error': 'cant delete user object for given pseudo' }

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'pseudo parameter must be provided' }

        self.respond(ret, ret_code)


class RoleHandler(BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = HTTP_OK
        roles = self.ormdb.query(Role).all()
        for r in roles:
            ret[r.cid] = r.name
        self.respond(ret, ret_code)


class StatusHandler(BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = HTTP_OK
        roles = self.ormdb.query(Status).all()
        for r in roles:
            ret[r.cid] = r.name
        self.respond(ret, ret_code)


class UserHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @tornado.concurrent.run_on_executor
    def create_user(self, username, password, email=None):
        """
            create_user :: Self
                        -> String               -- ^ new user's name
                        -> String               -- ^ the password
                        -> Maybe String         -- ^ the email
                        -> IO Map String String -- ^ request info
            ===========================
            This method creates an user
        """
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
            ret = { 'status_code': HTTP_OK
                  , 'message': usr.to_dict() }
            self.ormdb.commit()

        except exc.IntegrityError as e:
            ret = { 'status_code': HTTP_BAD_REQUEST
                  , 'error': 'user already exists' }
        except Exception as e:
            logger.exception('Unhandled Exception')
            ret = { 'status_code': HTTP_BAD_REQUEST
                  , 'error': 'Unhandled Exception' }

        return ret

    @tornado.concurrent.run_on_executor
    def update_user(self, username, password=None, status_name=None,
                    roles_list=None, email=None):
        """
            update_user :: Self
                        -> String                -- ^ users's pseudo
                        -> Maybe String          -- ^ new password
                        -> Maybe String          -- ^ account status name
                        -> Maybe [String]        -- ^ list of roles names
                        -> Maybe String          -- ^ new email
                        -> IO Map String String  -- ^ request info
            ================================================
            This function updates an user object in database
        """
        ret = {}
        usr = self.ormdb.query(User).filter_by(pseudo=username).first()
        if usr is not None:
            try:
                if password is not None:
                    usr.passwhash = sha512_crypt.encrypt(password)

                if status_name is not None:
                    c_stat = self.ormdb.query(Status)\
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

                ret = { 'status_code': HTTP_OK
                      , 'message': usr.to_dict() }
                self.ormdb.commit()

            except Exception as e:
                logger.exception('user could not be updated')
                ret = { 'status_code': HTTP_BAD_REQUEST
                      , 'error': 'user could not be updated' }
        else:
            ret = { 'status_code': HTTP_NOT_FOUND
                  , 'error': 'user does not exist' }

        return ret

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = HTTP_OK
        dp=True
        try:
            username = self.get_argument('pseudo')

            uniq_redis_id = 'users_{0}_{1}'.format(username, STATIC_CACHID)
            red_res = self.redis.get(uniq_redis_id)
            if red_res is not None:
                ret = red_res
                dp=False
            else:
                us = self.ormdb.query(User).filter_by(pseudo=username).first()
                if us is not None:
                    ret = us.to_dict()
                    self.redis.set(uniq_redis_id, json.dumps(ret, indent=4))
                    self.redis.expire(uniq_redis_id, REDIS_CACHE_TIMEOUT)
                else:
                    ret_code = HTTP_NOT_FOUND
                    ret = { 'error': 'inexistant user object for given pseudo' }

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'valid pseudo parameter must be provided' }

        self.respond(ret, ret_code, data_dump=dp)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = HTTP_OK
        try:
            username = self.get_argument('pseudo')
            email    = self.get_argument('email', default=None)
            password = self.get_argument('password')

            res = yield self.create_user(username, password, email)
            ret_code = res.pop('status_code')
            ret = res if 'error' in res else res['message']

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'post form is missing required data' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def put(self):
        ret = {}
        ret_code = HTTP_OK
        try:
            i_us = self.get_argument('pseudo')
            i_em = self.get_argument('email', default=None)
            i_pa = self.get_argument('password', default=None)
            i_st = self.get_argument('status', default=None)
            i_rw = self.get_argument('roles', default=None)

            p_rl = None
            if i_rw is not None:
                p_rl = filter(lambda x: x != '', i_rw.split(';'))

            res = yield self.update_user(i_us, i_pa, i_st, p_rl, i_em)
            ret_code = res.pop('status_code')
            if 'error' in res:
                ret = res
            else:
                ret = res['message']
                uniq_redis_id = 'users_{0}_{1}'.format(i_us, STATIC_CACHID)
                self.redis.set(uniq_redis_id, json.dumps(ret, indent=4))
                self.redis.expire(uniq_redis_id, REDIS_CACHE_TIMEOUT)

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'put form is missing required data' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = HTTP_OK
        try:
            username = self.get_argument('pseudo')
            us = self.ormdb.query(User).filter_by(pseudo=username).first()
            if us is not None:
                self.ormdb.delete(us)
                self.ormdb.commit()

                ret = { 'deleted_usr_id': us.cid }
            else:
                ret_code = HTTP_NOT_FOUND
                ret = { 'error': 'cant delete user object for given pseudo' }

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'pseudo parameter must be provided' }

        self.respond(ret, ret_code)


def run_api(database_url, port=8080, debug=False):
    app = Application(database_url)
    app.listen(port)
    ioloop = IOLoop.instance()
    if debug:
        tornado.autoreload.start(ioloop)
    ioloop.start()

#
