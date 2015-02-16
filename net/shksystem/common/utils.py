# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Process helpers
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 03.01.2015
#@(#) LICENSE          : GPL-3
#@(#)----------------------------------------------------------------------

#==========================================================================
#
# WARNINGS
# NONE
#
#==========================================================================

#==========================================================================
# Imports
#==========================================================================

import os
import sys
import binascii
import random
import datetime
import logging, logging.handlers
from subprocess import call
from .error     import *

#==========================================================================
# Environment/Static variables
#==========================================================================
# NONE
#==========================================================================
# Classes/Functions
#==========================================================================

logger = logging.getLogger(__name__)

## This function add console and file handlers to a Logger object
# initLogger :: FilePath
#            -> String
#            -> Logger
#            -> IO ()
def init_logger(loggo, log_path, log_level):
    # setting formatter
    formater = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s", "%d-%m %H:%M")
    # configuring rotation
    hd = logging.handlers.RotatingFileHandler(log_path, maxBytes=5000000, backupCount=5)
    hd.setFormatter(formater)
    # adding console output
    ch = logging.StreamHandler()
    ch.setFormatter(formater)
    # configuring logger
    loggo.setLevel(log_level)
    loggo.addHandler(hd)
    loggo.addHandler(ch)

## This function calls pdflatex on LaTEX source file
#    and performs basic cleanup afterwards
# compileTex :: FilePath
#            -> IO ()
def compile_tex(tex_source_file):
    if not os.path.isfile(tex_source_file):
        logger.warn('Input file does not exist'.format(tex_source_file,))
        raise FileNotFound
    tex_file_name = os.path.splitext(tex_source_file)[0]
    exts          = ['aux', 'log']

    logger.info('Calling pdflatex on {0}.'.format(tex_source_file,))
    code = call(['pdflatex', '-interaction=nonstopmode', tex_source_file, '>', os.devnull])
    if code != 0:
        logger.warn('Compilation failure.')
        raise CommandFailure

    for ext in exts:
        final_file = '{0}{1}{2}'.format(tex_file_name, os.extsep, ext)
        if os.path.isfile(final_file):
            logger.info('Deleting {0}.'.format(final_file,))
            os.unlink(final_file)

    logger.info('Compilation success.')

## This function gets current date and time with the following format:
#    dd/mm/yy:HH:MM
# get_current_timestamp :: IO String
def get_current_timestamp():
    ret = datetime.datetime.now().isoformat()
    return ret

## This function generate random n lenght token
# gen_random_token :: IO String
def gen_random_token(n):
    ret = binascii.hexlify(os.urandom(n))
    return ret

## This function returns the nth element of a list
# get_random_elem :: [a]
#                 -> IO a
def get_random_elem(lst):
    ret = random.choice(lst)
    return ret

#==========================================================================
#0
