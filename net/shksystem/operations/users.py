# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import logging
import json
# installed
import redis
# custom
import net.shksystem.common.constants as cst
import net.shksystem.constants.users as ucst

## Globals
# =============================================================================

logger = logging.getLogger()

## Functions and Classes
# =============================================================================

class UtilsCache(object):

    def __init__(self, redis_id: str) -> 'UtilsCache':
        self.redis_id = redis_id
        self.cache_manager = redis.Redis()

    def redis_uqit(self, constant_key: str, varname: str) -> str:
        return '{0}_{1}_{2}'.format(self.redis_id, constant_key, varname)

    def set_user(self, usrobj: 'User') -> None:
        uqid = self.redis_uqit(ucst.USER_KEY, usrobj.pseudo)
        self.cache_manager.set(uqid, json.dumps(usrobj.to_dict()))
        self.cache_manager.expire(uqid, cst.CACHE_TIMEOUT)

    def get_user(self, pseudo: str) -> 'User':
        ret = None
        uqid = self.redis_uqit(ucst.USER_KEY, pseudo)
        red_res = self.cache_manager.get(uqid)
        if red_res is not None:
            ret = json.loads(str(red_res, cst.UTF8))
        return ret

#
