# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Livraison Center processes
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 30.11.2014
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
import time
from subprocess                  import call
import tempfile
import shutil
import logging
import pysvn
from pprint                      import pprint
from net.shksystem.common.puppet import deployFic
from models                      import Environment, UserConf

#==========================================================================
# Environment/Static variables
#==========================================================================

logger = logging.getLogger(__name__)

#==========================================================================
# Classes/Functions
#==========================================================================

class CheckoutFailure(Exception):
    pass
class CompileFailure(Exception):
    pass

def compileProj(pname, surl):
    logger.info('Setting up workplace')
    current = os.getcwd()
    temp    = tempfile.mkdtemp()

    checkoutDir = os.path.join(temp, pname)
    os.mkdir(checkoutDir)
    os.chdir(checkoutDir)

    logger.info('SVN checkout')
    try:
        client = pysvn.Client()
        client.checkout('{0}/{1}'.format(surl, pname), './')
        client = None # Otherwise cannot remove temp dir
    except:
        logger.error('Could not finish SVN checkout')
        raise CheckoutFailure

    logger.info('Compiling {0}'.format(pname,))
    code = call(['mvn', 'clean', 'package', '-o', '-Dmaven.test.skip'], shell=True)
    if code != 0:
        logger.error('Compile error on {0}'.format(pname,))
        raise CompileFailure

    os.chdir(current)
    return temp

def deployLiv(envs, userConf):
    pname = 'Livraison'
    temp  = ''
    try:
        temp = compileProj(pname, userConf.javaUtilsUrl)
    except:
        pass

    if temp != '':
        try:
            for inv in envs:
                deployFic(os.path.join(temp, pname, 'target', '{0}.jar'.format(pname,))
                          , '/appl/liv000/{0}/{1}/java'.format(inv.envName, pname)
                          , inv.hostname
                          , inv.userName
                          , inv.userGroup
                          , 0660
                          , userConf.hopUser
                          , userConf.hopPasswd)
        except:
            logger.error('Deployment wrongly halted')

        shutil.rmtree(temp)
        logger.info('{0} deployment is a success'.format(pname,))
    else:
        logger.info('{0} deployment is a failure'.format(pname,))

def deployUtil(envs, userConf):
    pname = 'utilitaires'
    temp  = ''
    try:
        temp = compileProj(pname, userConf.javaUtilsUrl)
    except:
        pass

    if temp != '':
        try:
            for inv in envs:
                deployFic(os.path.join(temp, pname,'target', '{0}.jar'.format(pname,))
                          , '/appl/com000/java/lib'
                          , inv.hostname
                          , inv.userName
                          , inv.userGroup
                          , 0660
                          , userConf.hopUser
                          , userConf.hopPasswd)
        except:
            logger.error('Deployment wrongly halted')

        shutil.rmtree(temp)
        logger.info('{0} deployment is a success'.format(pname,))
    else:
        logger.info('{0} deployment is a failure'.format(pname,))

#==========================================================================
#0
