#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
import json
# installed
import requests

## Globals
# =============================================================================

logger = logging.getLogger()

## Functions and Classes
# =============================================================================


class Client(object):

    def __init__(self, http_api_url):
        self.http_api_url = http_api_url
        self.username = None

    def __warn_username(self):


    def set_username(self):
        pass

    def get_email(self):
        pass

    def get_status(self):
        pass

    def get_roles(self):
        pass

    def get_mail_servers(self):
        pass


#
