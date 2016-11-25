# -*- coding: utf-8 -*-

""" common exceptions """

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
# installed
# custom

# Classes and Functions
# =============================================================================


class SHKException(Exception):

    def __init__(self, http_code, message):
        super(SHKException, self).__init__()
        self.message = message
        self.http_code = http_code

#
