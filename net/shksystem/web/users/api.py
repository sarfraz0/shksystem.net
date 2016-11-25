# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
import json
from datetime import datetime as dt
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
#import keyring
import multiprocessing
# custom
from net.shksystem.common.constants import *
from net.shksystem.common.api import BaseApplication, BaseHandler
from net.shksystem.common.exceptions import SHKException
from net.shksystem.db.users import Base, User, Status, Role
from net.shksystem.operations.users import UtilsCache

## Globals
# =============================================================================

logger = logging.getLogger()
MAX_WORKERS=multiprocessing.cpu_count()

## Functions and Classes
# =============================================================================


class Application(BaseApplication):

    def __init__(self, database_url):
        handlers = [
                     (r'/api/v2/roles(?:/(\w+))?', RoleHandler)
                   , (r'/api/v2/statuses(?:/(\w+))?', StatusHandler)
                   , (r'/api/v2/users/auth', UserAuthHandler)
                   , (r'/api/v2/users(?:/(\w+))?', UserHandler)
                   ]
        super(Application, self).__init__(database_url, handlers)
        self.cache = UtilsCache(self.redis_id)


class RoleHandler(BaseHandler):

    @tornado.gen.coroutine
    def get(self, identifier=None):
        ret = []
        ret_code = HTTP_OK

        try:
            if identifier is None:
                roles = self.ormdb.query(Role).all()
                for r in roles:
                    ret.append(r.to_dict())
            else:
                # else we query on specific entity
                role = self.ormdb.query(Role).filter_by(name=identifier) \
                                             .first()
                if role is None:
                    raise SHKException(
                              HTTP_NOT_FOUND,
                              ENTITY_NOT_FOUND_MSG
                          )
                else:
                    ret = role.to_dict()

        except SHKException as e:
            ret_code = e.http_code
            ret = { ERROR_KEY: e.message }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def post(self, identifier=None):
        ret = {}
        ret_code = HTTP_OK
        try:
            role_name = self.get_argument(NAME_KEY)
            role = Role(role_name)

            ret = role.to_dict()
            self.ormdb.add(role)
            self.ormdb.commit()

        except exc.IntegrityError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: ENTITY_EXISTS_MSG }
        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: MISSING_ARGS_MSG }
        except Exception as e:
            logger.exception(UNHANDLED_EXC_MSG)
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: UNHANDLED_EXC_MSG }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self, identifier=None):
        ret = {}
        ret_code = HTTP_OK
        try:
            if identifier is None:
                raise SHKException(
                          HTTP_BAD_REQUEST,
                          MISSING_ARGS_MSG
                      )
            else:
                rl = self.ormdb.query(Role).filter_by(name=identifier).first()
                if rl is not None:
                    self.ormdb.delete(rl)
                    self.ormdb.commit()

                    ret = { RESSOURCE_KEY: rl.cid }
                else:
                    ret_code = HTTP_NOT_FOUND
                    ret = { ERROR_KEY: ENTITY_NOT_FOUND_MSG }

        except SHKException as e:
            ret_code = e.http_code
            ret = { ERROR_KEY: e.message }

        self.respond(ret, ret_code)


class StatusHandler(BaseHandler):

    @tornado.gen.coroutine
    def get(self, identifier=None):
        ret = []
        ret_code = HTTP_OK

        if identifier is None:
            statuses = self.ormdb.query(Status).all()
            for s in statuses:
                ret.append(s.name)
        else:
            try:
                status = self.ormdb.query(Status).filter_by(name=identifier) \
                                                 .first()
                if status is None:
                    raise SHKException(
                              HTTP_NOT_FOUND,
                              ENTITY_NOT_FOUND_MSG
                          )
                else:
                    ret = status.to_dict()

            except SHKException as e:
                ret_code = e.http_code
                ret = {ERROR_KEY: e.message}

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def post(self, identifier=None):
        ret = {}
        ret_code = HTTP_OK
        try:
            status_name = self.get_argument(NAME_KEY)
            status = Status(status_name)

            ret = status.to_dict()
            self.ormdb.add(status)
            self.ormdb.commit()

        except exc.IntegrityError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: ENTITY_EXISTS_MSG }
        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: MISSING_ARGS_MSG }
        except Exception as e:
            logger.exception(UNHANDLED_EXC_MSG)
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: UNHANDLED_EXC_MSG }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self, identifier=None):
        ret = {}
        ret_code = HTTP_OK
        try:
            if identifier is None:
                raise SHKException(
                          HTTP_BAD_REQUEST,
                          MISSING_ARGS_MSG
                      )
            else:
                st = self.ormdb.query(Status).filter_by(name=identifier).first()
                if st is not None:
                    self.ormdb.delete(st)
                    self.ormdb.commit()
                    ret = { RESSOURCE_KEY: st.cid }
                else:
                    ret_code = HTTP_NOT_FOUND
                    ret = { ERROR_KEY: ENTITY_NOT_FOUND_MSG }

        except SHKException as e:
            ret_code = e.http_code
            ret = { ERROR_KEY: e.message }

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
        ret_code = HTTP_OK

        d_status = self.ormdb.query(Status).filter_by(name=PENDING_KEY) \
                                           .first()
        usr = User(username, password, d_status)

        d_role = self.ormdb.query(Role).filter_by(name=USER_KEY).first()
        usr.roles.append(d_role)

        if email is not None:
            usr.email = email

        try:
            self.ormdb.add(usr)
            self.ormdb.flush()
            ret = usr.to_dict()
            self.ormdb.commit()

        except (exc.IntegrityError, exc.InvalidRequestError) as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: ENTITY_EXISTS_MSG }
        except Exception as e:
            logger.exception(UNHANDLED_EXC_MSG)
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: UNHANDLED_EXC_MSG }

        return (ret, ret_code)

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
        ret_code = HTTP_OK

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

                ret = usr.to_dict()
                self.ormdb.commit()

            except Exception as e:
                logger.exception('user could not be updated')
                ret_code = HTTP_BAD_REQUEST
                ret = { ERROR_KEY: 'user could not be updated' }
        else:
            ret_code = HTTP_NOT_FOUND
            ret = { ERROR_KEY: 'user does not exist' }

        return (ret, ret_code)

    @tornado.gen.coroutine
    def get(self, identifier=None):
        ret = {}
        ret_code = HTTP_OK
        dp=True
        try:
            if identifier is None:
                raise SHKException(
                          HTTP_BAD_REQUEST,
                          MISSING_ARGS_MSG
                      )
            else:
                uqid = self.redis_uqit(USER_KEY, identifier)
                red_res = self.redis.get(uqid)
                if red_res is not None:
                    ret = red_res
                    dp=False
                else:
                    us = self.ormdb.query(User).filter_by(pseudo=identifier) \
                                               .first()
                    if us is not None:
                        ret = us.to_dict()
                        self.redis.set(uqid, json.dumps(ret, indent=4))
                        self.redis.expire(uqid, CACHE_TIMEOUT)
                    else:
                        ret_code = HTTP_NOT_FOUND
                        ret = { ERROR_KEY: ENTITY_NOT_FOUND_MSG }

        except SHKException as e:
            ret_code = e.http_code
            ret = { ERROR_KEY: e.message }

        self.respond(ret, ret_code, data_dump=dp)

    @tornado.gen.coroutine
    def post(self, identifier=None):
        ret = {}
        ret_code = HTTP_OK
        try:
            username = self.get_argument(PSEUDO_KEY)
            email    = self.get_argument(EMAIL_KEY, default=None)
            password = self.get_argument(PASSWORD_KEY)

            ret, ret_code = yield self.create_user(username, password, email)

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: MISSING_ARGS_MSG }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def put(self, identifier=None):
        ret = {}
        ret_code = HTTP_OK
        try:
            if identifier is not None:
                ret_code = HTTP_NOT_FOUND
                ret = { ERROR_KEY: URL_NOT_FOUND_MSG }
            else:
                i_us = self.get_argument(PSEUDO_KEY)
                i_em = self.get_argument(EMAIL_KEY, default=None)
                i_pa = self.get_argument(PASSWORD_KEY, default=None)
                i_st = self.get_argument(STATUS_KEY, default=None)
                i_rw = self.get_argument(ROLES_KEY, default=None)

                rl = None
                if i_rw is not None:
                    rl = filter(lambda x: x != '', i_rw.split(CSV_SEPARATOR))

                ret, ret_code = yield self.update_user(i_us, i_pa, i_st, rl
                        , i_em)

                if ret_code == HTTP_OK:
                    uqid = self.redis_uqit(USER_KEY, i_us)
                    self.redis.set(uqid, json.dumps(ret, indent=4))
                    self.redis.expire(uqid, CACHE_TIMEOUT)

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { ERROR_KEY: MISSING_ARGS_MSG }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self, identifier=None):
        ret = {}
        ret_code = HTTP_OK
        try:
            if identifier is None:
                raise SHKException(
                          HTTP_BAD_REQUEST,
                          MISSING_ARGS_MSG
                      )
            else:
                us = self.ormdb.query(User).filter_by(pseudo=identifier) \
                        .first()
            if us is not None:
                self.ormdb.delete(us)
                self.ormdb.commit()

                ret = { RESSOURCE_KEY: us.cid }
            else:
                ret_code = HTTP_NOT_FOUND
                ret = { ERROR_KEY: ENTITY_OP_FAIL_MSG }

        except SHKException as e:
            ret_code = e.http_code
            ret = { ERROR_KEY: e.message }

        self.respond(ret, ret_code)


class UserAuthHandler(BaseHandler):

    def post(self):
        ret = {}
        ret_code = HTTP_OK

        try:
            pseudo = self.get_argument(PSEUDO_KEY)
            password = self.get_argument(PASSWORD_KEY)

            cached_usr = self.application.cache.get_user(pseudo)
            is_auth = False
            if cached_usr is not None:
                if sha512_crypt.verify(password, cached_usr[PASSWHASH_KEY]):
                    is_auth = True
            else:
                us = self.ormdb.query(User).filter_by(pseudo=pseudo).first()
                if us is not None:
                    self.application.cache.set_user(us)
                    if sha512_crypt.verify(password, us.passwhash):
                        is_auth = True
                else:
                    ret_code = HTTP_NOT_FOUND
                    ret = { ERROR_KEY: ENTITY_NOT_FOUND_MSG }

            ret = {RESSOURCE_KEY: is_auth}

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = {ERROR_KEY: MISSING_ARGS_MSG}

        self.respond(ret, ret_code)


def run_api(database_url, port=8080, debug=False):
    app = Application(database_url)
    app.listen(port)
    ioloop = IOLoop.instance()
    if debug:
        tornado.autoreload.start(ioloop)
    ioloop.start()


