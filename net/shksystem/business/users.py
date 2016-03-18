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


class UserApi(object):

    def __init__(self, user_api_url, validation_cert):
        self._url = user_api_url
        self._user_endpoint = user_api_url + '/api/v1/users'
        self._role_endpoint = user_api_url + '/api/v1/roles'
        self._cert = validation_cert

    def _get_request(self, endpoint, req_dict):
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

    def _post_request(self, endpoint, req_dict):
        ret = False
        try:
            r = requests.post(endpoint, params=req_dict, verify=self._cert)
            if r.status_code == HTTP_OK:
                ret = True
        except requests.ConnectionError as c:
            logger.exception('Could not connect to User API')
        return ret

    def get_user(self, pseudo):
        ret = None
        rd = self._get_request(self._user_endpoint, {'pseudo': pseudo})
        if rd is not None:
            ret = User(pseudo, rd['status'], rd['roles'], rd['email'])
        return ret

    def create_user(self, user, password):
        params = { 'pseudo': user.pseudo
                 , 'password': password
                 , 'status': user.status
                 , 'roles': ';'.join(user.roles)
                 , 'email': user.email }
        return self._post_request(self._user_endpoint, params)

    def get_roles(self):
        return self._get_request(self._role_endpoint, {})

    def create_role(self, name):
        return self._post_request(self._role_endpoint, {'name': name})

    def delete_role(self, name):
        ret = False
        roles = self.get_roles()
        if name in roles:
            par = {'name', name}
            requests.delete(self._role_endpoint, params=par, verify=self._cert)
            ret = True
        return ret

    def append_role(self, pseudo, role):
        ret = False
        user = self.get_user(pseudo)
        if user is not None:
            if not role in user.roles:
                user.roles.append(role)
                par = { 'pseudo': pseudo, 'roles': ';'.join(user.roles) }
                requests.put(self._user_endpoint, params=par, verify=self._cert)
                ret = True
        return ret

#
