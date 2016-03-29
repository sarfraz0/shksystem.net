# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
import json
# installed
import requests
# custom

# Globals
# =============================================================================

logger = logging.getLogger(__name__)

HTTP_OK = 200

# Classes and Functions
# =============================================================================

class User(object):

    def __init__(self, pseudo, status, roles, email=None):
        self.pseudo = pseudo
        self.status = status.lower().strip()
        self.roles = map(lambda x: x.strip().lower(), roles)
        self.email = email

    def is_active(self):
        return (self.status == 'active')

    def is_admin(self):
        return ('admin' in self.roles)

    def is_manager(self):
        return ('manager' in self.roles)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.pseudo


class GetRequest(object):

    def __init__(self, user_url, role_url, status_url, validation_cert):
        self._user_endpoint = user_url
        self._role_endpoint = role_url
        self._status_endpoint = status_url
        self._cert = validation_cert

    def _request(self, endpoint, req_dict):
        ret = None
        try:
            r = requests.get(endpoint, params=req_dict, verify=self._cert)
            if r.status_code == HTTP_OK:
                d = json.loads(r.text)
                if not 'error' in d:
                    ret = d
        except requests.ConnectionError as c:
            logger.exception('Could not connect to User API')

        return ret

    def user(self, pseudo):
        ret = None
        rd = self._request(self._user_endpoint, {'pseudo': pseudo})
        if rd is not None:
            ret = User(pseudo, rd['status'], rd['roles'], rd['email'])
        return ret

    def roles(self):
        return self._request(self._role_endpoint, {})

    def statuses(self):
        return self._request(self._status_endpoint, {})


class PostRequest(object):

    def __init__(self, user_url, role_url, status_url, validation_cert):
        self._user_endpoint = user_url
        self._role_endpoint = role_url
        self._status_endpoint = status_url
        self._cert = validation_cert

    def _request(self, endpoint, req_dict):
        ret = False
        try:
            r = requests.post(endpoint, data=req_dict, verify=self._cert)
            if r.status_code == HTTP_OK:
                ret = True
        except requests.ConnectionError as c:
            logger.exception('Could not connect to User API')
        return ret

    def user(self, user, password):
        reqbody = { 'pseudo': user.pseudo
                  , 'password': password
                  , 'status': user.status
                  , 'roles': ';'.join(user.roles)
                  , 'email': user.email }
        return self._request(self._user_endpoint, reqbody)

    def role(self, name):
        return self._request(self._role_endpoint, {'name': name})

    def status(self, name):
        return self._request(self._status_endpoint, {'name': name})


class PutRequest(object):

    def __init__(self, user_url, role_url, status_url, validation_cert):
        self._user_endpoint = user_url
        self._role_endpoint = role_url
        self._status_endpoint = status_url
        self._cert = validation_cert

    def _request(self, endpoint, req_dict):
        ret = False
        try:
            r = requests.put(endpoint, data=req_dict, verify=self._cert)
            if r.status_code == HTTP_OK:
                ret = True
        except requests.ConnectionError as c:
            logger.exception('Could not connect to User API')

        return ret

    def user(self, user, password=None):
        reqbody = { 'pseudo': user.pseudo
                  , 'status': user.status
                  , 'roles': ';'.join(user.roles) }
        if password is not None:
            reqbody['password'] = password
        if user.email is not None:
            reqbody['email'] = user.email
        return self._request(self._user_endpoint, reqbody)


class DeleteRequest(object):

    def __init__(self, user_url, role_url, status_url, validation_cert):
        self._user_endpoint = user_url
        self._role_endpoint = role_url
        self._status_endpoint = status_url
        self._cert = validation_cert

    def _request(self, endpoint, req_dict):
        ret = False
        try:
            r = requests.delete(endpoint, params=req_dict, verify=self._cert)
            if r.status_code == HTTP_OK:
                ret = True
        except requests.ConnectionError as c:
            logger.exception('Could not connect to User API')

        return ret

    def user(self, pseudo):
        return self._request(self._user_endpoint, {'pseudo': pseudo})

    def role(self, name):
        return self._request(self._role_endpoint, {'name': name})

    def status(self):
        return self._request(self._status_endpoint, {'name': name})


class UserAPI(object):

    def __init__(self, api_url, validation_cert):
        self._url = api_url
        self._user_endpoint = self._url + '/users'
        self._role_endpoint = self._url + '/roles'
        self._status_endpoint = self._url + '/statuses'
        self._cert = validation_cert

        self.get    = GetRequest(self._user_endpoint, self._role_endpoint,
                                 self._status_endpoint, self._cert)
        self.post   = PostRequest(self._user_endpoint, self._role_endpoint,
                                  self._status_endpoint, self._cert)
        self.put    = PutRequest(self._user_endpoint, self._role_endpoint,
                                 self._status_endpoint, self._cert)
        self.delete = DeleteRequest(self._user_endpoint, self._role_endpoint,
                                    self._status_endpoint, self._cert)

#
