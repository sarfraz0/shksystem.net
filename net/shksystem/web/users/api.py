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
#import keyring
import multiprocessing
# custom
import net.shksystem.common.constants as constants
import net.shksystem.common.api as api
from net.shksystem.db.users import Base, User, Status, Role

## Globals
# =============================================================================

logger = logging.getLogger()

MAX_WORKERS=multiprocessing.get_cpu_count()
STATIC_CACHID=str(uuid.uuid4()).upper().replace('-', "")[0:6]

## Functions and Classes
# =============================================================================


class Application(api.Application):

    def __init__(self, database_url):
        handlers = [
                     (r'/api/v1/roles', RoleHandler)
                   , (r'/api/v1/statuses', StatusHandler)
                   , (r'/api/v1/users', UserHandler)
                   ]
        super(Application, self).__init__(database_url, handlers)


class RoleHandler(api.BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        ret = []
        ret_code = constants.HTTP_OK
        roles = self.ormdb.query(Role).all()
        for r in roles:
            ret.append(r.name)
        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = constants.HTTP_OK
        try:
            role_name = self.get_argument('name')
            role = Role(role_name)

            ret = role.to_dict()
            self.ormdb.add(role)
            self.ormdb.commit()

        except exc.IntegrityError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'role already exists' }
        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'post form is missing required data' }
        except Exception as e:
            logger.exception('Unhandled Exception')
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'Unhandled Exception' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = constants.HTTP_OK
        try:
            role_name = self.get_argument('name')
            rl = self.ormdb.query(Role).filter_by(name=role_name).first()
            if rl is not None:
                self.ormdb.delete(rl)
                self.ormdb.commit()

                ret = { 'deleted ID': rl.cid }
            else:
                ret_code = constants.HTTP_NOT_FOUND
                ret = { 'error': 'cant delete user object for given name' }

        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'name parameter must be provided' }

        self.respond(ret, ret_code)


class StatusHandler(api.BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        ret = []
        ret_code = constants.HTTP_OK
        statuses = self.ormdb.query(Status).all()
        for s in statuses:
            ret.append(s.name)
        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = constants.HTTP_OK
        try:
            status_name = self.get_argument('name')
            status = Role(status_name)

            ret = status.to_dict()
            self.ormdb.add(status)
            self.ormdb.commit()

        except exc.IntegrityError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'status already exists' }
        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'post form is missing required data' }
        except Exception as e:
            logger.exception('Unhandled Exception')
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'Unhandled Exception' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = constants.HTTP_OK
        try:
            status_name = self.get_argument('name')
            st = self.ormdb.query(Status).filter_by(name=status_name).first()
            if st is not None:
                self.ormdb.delete(st)
                self.ormdb.commit()

                ret = { 'deleted ID': st.cid }
            else:
                ret_code = constants.HTTP_NOT_FOUND
                ret = { 'error': 'cant delete user object for given name' }

        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'name parameter must be provided' }

        self.respond(ret, ret_code)


class UserHandler(api.BaseHandler):

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
        ret_code = constants.HTTP_OK

        d_status = self.ormdb.query(Status).filter_by(name='pending').first()
        usr = User(username, password, d_status)

        d_role = self.ormdb.query(Role).filter_by(name='user').first()
        usr.roles.append(d_role)

        if email is not None:
            usr.email = email

        try:
            self.ormdb.add(usr)
            self.ormdb.flush()
            ret = usr.to_dict()
            self.ormdb.commit()

        except (exc.IntegrityError, exc.InvalidRequestError) as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'user already exists' }
        except Exception as e:
            logger.exception('Unhandled Exception')
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'Unhandled Exception' }

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
        ret_code = constants.HTTP_OK

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
                ret_code = constants.HTTP_BAD_REQUEST
                ret = { 'error': 'user could not be updated' }
        else:
            ret_code = constants.HTTP_NOT_FOUND
            ret = { 'error': 'user does not exist' }

        return (ret, ret_code)

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = constants.HTTP_OK
        dp=True
        try:
            username = self.get_argument('pseudo')

            redis_id = 'users_{0}_{1}'.format(username, STATIC_CACHID)
            red_res = self.redis.get(redis_id)
            if red_res is not None:
                ret = red_res
                dp=False
            else:
                us = self.ormdb.query(User).filter_by(pseudo=username).first()
                if us is not None:
                    ret = us.to_dict()
                    self.redis.set(redis_id, json.dumps(ret, indent=4))
                    self.redis.expire(redis_id, constants.REDIS_CACHE_TIMEOUT)
                else:
                    ret_code = constants.HTTP_NOT_FOUND
                    ret = { 'error': 'inexistant user object for given pseudo' }

        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'valid pseudo parameter must be provided' }

        self.respond(ret, ret_code, data_dump=dp)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = constants.HTTP_OK
        try:
            username = self.get_argument('pseudo')
            email    = self.get_argument('email', default=None)
            password = self.get_argument('password')

            ret, ret_code = yield self.create_user(username, password, email)

        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'post form is missing required data' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def put(self):
        ret = {}
        ret_code = constants.HTTP_OK
        try:
            i_us = self.get_argument('pseudo')
            i_em = self.get_argument('email', default=None)
            i_pa = self.get_argument('password', default=None)
            i_st = self.get_argument('status', default=None)
            i_rw = self.get_argument('roles', default=None)

            p_rl = None
            if i_rw is not None:
                p_rl = filter(lambda x: x != '', i_rw.split(';'))

            ret, ret_code = yield self.update_user(i_us, i_pa, i_st, p_rl, i_em)

            if ret_code == constants.HTTP_OK:
                redis_id = 'users_{0}_{1}'.format(i_us, STATIC_CACHID)
                self.redis.set(redis_id, json.dumps(ret, indent=4))
                self.redis.expire(redis_id, constants.REDIS_CACHE_TIMEOUT)

        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
            ret = { 'error': 'put form is missing required data' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = constants.HTTP_OK
        try:
            username = self.get_argument('pseudo')
            us = self.ormdb.query(User).filter_by(pseudo=username).first()
            if us is not None:
                self.ormdb.delete(us)
                self.ormdb.commit()

                ret = { 'deleted ID': us.cid }
            else:
                ret_code = constants.HTTP_NOT_FOUND
                ret = { 'error': 'cant delete user object for given pseudo' }

        except tornado.web.MissingArgumentError as e:
            ret_code = constants.HTTP_BAD_REQUEST
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
