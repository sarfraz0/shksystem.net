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

import os, sys
import logging, logging.handlers
from subprocess import call
from error      import *

#==========================================================================
# Environment/Static variables
#==========================================================================
# NONE
#==========================================================================
# Classes/Functions
#==========================================================================

logger = logging.getLogger(__name__)

class LogH(object):

    def __init__(self):
        pass

    ## This function add console and file handlers to a Logger object
    # initLogger :: FilePath
    #            -> String
    #            -> Logger
    #            -> IO ()
    @staticmethod
    def initLogger(loggo, logPath, logLevel):
        # setting formatter
        formater = logging.Formatter("%(asctime)s %(name)-5s %(levelname)-5s %(message)s", "%d/%m %Hh%M")
        # configuring rotation
        hd = logging.handlers.RotatingFileHandler(logPath, maxBytes=5000000, backupCount=5)
        hd.setFormatter(formater)
        # adding console output
        ch = logging.StreamHandler()
        ch.setFormatter(formater)
        # configuring logger
        loggo.setLevel(logLevel)
        loggo.addHandler(hd)
        loggo.addHandler(ch)

    @staticmethod
    def endMessage(endMsg, endCode):
        return ('({0}) ********** {1} **********'
                .format(str(endCode), endMsg.upper()))

## This function calls pdflatex on LaTEX source file
#    and performs basic cleanup afterwards
# compileTex :: FilePath
#            -> IO Integer
def compileTex(texSourceFile):
    if not os.path.isfile(texSourceFile):
        logger.warn(LogH.endMessage('input file does not exist', 2))
        raise FileNotFound
    texFileName = os.path.splitext(texSourceFile)[0]
    exts        = ['aux', 'log']

    logger.info('Calling pdflatex on {0}.'.format(texSourceFile,))
    code = call(['pdflatex', '-interaction=nonstopmode', texSourceFile, '>', os.devnull])
    if code != 0:
        logger.warn(LogH.endMessage('compilation failure', 3))
        raise CommandFailure

    for ext in exts:
        finalFile = '{0}{1}{2}'.format(texFileName, os.extsep, ext)
        if os.path.isfile(finalFile):
            logger.info('Deleting {0}.'.format(finalFile,))
            os.unlink(finalFile)

    logger.info(LogH.endMessage('compilation success', 0))


#==========================================================================
#0
