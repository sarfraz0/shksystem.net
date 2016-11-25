# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import logging
import json
from typing import Dict, List, Tuple
# installed
import requests
# custom
from net.shksystem.common.constants import *

# Globals
# =============================================================================

logger = logging.getLogger(__name__)

# Classes and Functions
# =============================================================================

class User(object):

    def __init__(self, pseudo: str, status: str
            , roles: List[str], namespaces: List[str]
            , email: str =None) -> 'User':

        self.pseudo = pseudo
        self.status = status.lower().strip()
        self.roles = [x.strip().lower() for x in roles]
        self.namespaces = [x.strip().lower() for x in namespaces]
        self.email = email

    def is_active(self):
        return (self.status == ACTIVE_KEY)

    def is_admin(self) -> bool:
        return (ADMIN_KEY in self.roles)

    def is_manager(self) -> bool:
        return (MANAGER_KEY in self.roles)

    def is_authenticated(self) -> bool:
        return True

    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        return self.pseudo


class GetRequest(object):

    def __init__(self, user_url: str, role_url: str
            , status_url: str) -> 'GetRequest':

        self._user_endpoint = user_url
        self._role_endpoint = role_url
        self._status_endpoint = status_url

    def _request(self, endpoint: str, identifier: str =None) -> Dict:
        ret = None
        try:
            final_url = endpoint if identifier is None \
                                 else '{0}/{1}'.format(endpoint, identifier)
            r = requests.get(final_url)
            if r.status_code == int(HTTP_OK):
                d = json.loads(r.text)
                if not ERROR_KEY in d:
                    ret = d
        except requests.ConnectionError as c:
            logger.exception(REMOTE_TIMEOUT_MSG)

        return ret

    def user(self, pseudo: str) -> User:
        ret = None
        rd = self._request(self._user_endpoint, pseudo)
        if rd is not None:
            ret = User(
                     pseudo,
                     rd[STATUS_KEY],
                     rd[ROLES_KEY],
                     rd[NAMESPACES_KEY],
                     rd[EMAIL_KEY]
                 )
        return ret

    def roles(self) -> List[Dict]:
        return self._request(self._role_endpoint)

    def role(self, name: str) -> Dict:
        return self._request(self._role_endpoint, name)

    def statuses(self) -> List[Dict]:
        return self._request(self._status_endpoint)

    def status(self, name: str) -> Dict:
        return self._request(self._status_endpoint, name)


class PostRequest(object):

    def __init__(self, user_url: str, role_url: str, status_url: str
            , auth_url: str) -> 'PostRequest':

        self._user_endpoint = user_url
        self._role_endpoint = role_url
        self._status_endpoint = status_url
        self._auth_endpoint = auth_url

    def _request(self, endpoint: str, req_dict: Dict) -> bool:
        ret = False
        try:
            r = requests.post(endpoint, data=req_dict)
            if r.status_code == int(HTTP_OK):
                d = json.loads(r.text)
                if not ERROR_KEY in d:
                    ret = True

        except requests.ConnectionError as c:
            logger.exception(REMOTE_TIMEOUT_MSG)
        return ret

    def user(self, username: str, password: str, email: str =None) -> bool:
        reqbody = { PSEUDO_KEY: username
                  , PASSWORD_KEY: password }
        if email is not None:
            reqbody[EMAIL_KEY] = email
        return self._request(self._user_endpoint, reqbody)

    def role(self, name: str) -> bool:
        return self._request(self._role_endpoint, {NAME_KEY: name})

    def status(self, name: str) -> bool:
        return self._request(self._status_endpoint, {NAME_KEY: name})

    def verify_login(self, pseudo: str, password: str) -> bool:
        ret = False
        reqbody = { PSEUDO_KEY: pseudo
                  , PASSWORD_KEY: password }
        req = requests.post(self._auth_endpoint, reqbody)
        if req.status_code == int(HTTP_OK):
            ret = json.loads(req.text)[RESSOURCE_KEY]
        return ret


class PutRequest(object):

    def __init__(self, user_url: str, role_url: str
            , status_url: str) -> 'PutRequest':

        self._user_endpoint = user_url
        self._role_endpoint = role_url
        self._status_endpoint = status_url

    def _request(self, endpoint: str, req_dict: Dict) -> bool:
        ret = False
        try:
            r = requests.put(endpoint, data=req_dict)
            if r.status_code == int(HTTP_OK):
                d = json.loads(r.text)
                if not ERROR_KEY in d:
                    ret = True

        except requests.ConnectionError as c:
            logger.exception(REMOTE_TIMEOUT_MSG)
        return ret

    def user(self, user: User, password: str =None) -> bool:
        reqbody = { PSEUDO_KEY: user.pseudo
                  , STATUS_KEY: user.status
                  , ROLES_KEY: CSV_SEPARATOR.join(user.roles) }
        if password is not None:
            reqbody[PASSWORD_KEY] = password
        if user.email is not None:
            reqbody[EMAIL_KEY] = user.email

        return self._request(self._user_endpoint, reqbody)


class DeleteRequest(object):

    def __init__(self, user_url: str, role_url: str
            , status_url: str) -> 'DeleteRequest':

        self._user_endpoint = user_url
        self._role_endpoint = role_url
        self._status_endpoint = status_url

    def _request(self, endpoint: str, identifier: str =None) -> bool:
        ret = False
        try:
            final_url = endpoint if identifier is None \
                                 else '{0}/{1}'.format(endpoint, identifier)
            r = requests.delete(final_url)
            if r.status_code == int(HTTP_OK):
                d = json.loads(r.text)
                if not ERROR_KEY in d:
                    ret = True

        except requests.ConnectionError as c:
            logger.exception(REMOTE_TIMEOUT_MSG)
        return ret

    def user(self, pseudo: str) -> bool:
        return self._request(self._user_endpoint, pseudo)

    def role(self, name: str) -> bool:
        return self._request(self._role_endpoint, name)

    def status(self, name: str) -> bool:
        return self._request(self._status_endpoint, name)


class UserAPI(object):

    def __init__(self, api_url: str
            , auth_tuple: Tuple[str, str] =None) -> 'UserAPI':
        self._url = api_url
        self._user_endpoint = '/'.join([api_url, USERS_KEY])
        self._role_endpoint = '/'.join([api_url, ROLES_KEY])
        self._status_endpoint = '/'.join([api_url, STATUSES_KEY])
        self._auth_endpoint = '/'.join([api_url, USERS_KEY, AUTH_KEY])
        self.auth_dict = auth_tuple

        self.get = GetRequest(self._user_endpoint, self._role_endpoint
                , self._status_endpoint)
        self.post = PostRequest(self._user_endpoint, self._role_endpoint
                , self._status_endpoint, self._auth_endpoint)
        self.put = PutRequest(self._user_endpoint, self._role_endpoint
                , self._status_endpoint)
        self.delete = DeleteRequest(self._user_endpoint, self._role_endpoint
                , self._status_endpoint)

#
