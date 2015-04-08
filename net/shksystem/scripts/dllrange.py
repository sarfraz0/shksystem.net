# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Automatic rules based folder cleanup
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 15.02.2015
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

# standard
import os
import sys
import shutil
import re
import logging
import configparser
# installed
import psycopg2
import keyring
# custom
import net.shksystem.common.utils as utils

#==========================================================================
# Environment/Static variables
#==========================================================================

logger = logging.getLogger(__name__)

#==========================================================================
# Classes/Functions
#==========================================================================

def run_rules(conf_file):
    if not (all(map(os.path.isfile, [conf_file]))):
        logger.error('Please check if file %s exists.', conf_file)
        raise OSError

    config = configparser.ConfigParser()
    config.read(conf_file)

    db_host = config.get('database', 'host')
    db_port = config.getint('database', 'port')
    db_name = config.get('database', 'name')
    db_user = config.get('database', 'user')
    db_use_pwd = config.getboolean('database', 'use_pwd')
    db_ssl = config.get('database', 'ssl')
    source = config.get('script', 'source')

    ctx = None
    c = None
    try:
        if db_use_pwd:
            passwd = keyring.get_password(db_host, db_user)
            ctx = psycopg2.connect(database=db_name, user=db_user, password=passwd, host=db_host, port=db_port, sslmode=db_ssl)
        else:
            ctx = psycopg2.connect(database=db_name, user=db_user, host=db_host, port=db_port, sslmode=db_ssl)

        c = ctx.cursor()

        logger.info('Processing source : %s.', source)
        c.execute('SELECT COUNT(*) FROM rules')
        logger.info('There is %d rules to process', c.fetchone()[0])
        c.execute('SELECT * FROM rules')
        for rule in c.fetchall():
            logger.info('Treating rule named : %s', rule[1])
            dest = os.path.join(rule[3], rule[1])
            if not os.path.isdir(dest):
                try:
                    os.mkdir(dest)
                except OSError as e:
                    logger.warn('Rule destination %s is not accessible. Skipping.', dest)
                    continue

            for filename in os.listdir(source):
                if re.match(rule[2], filename.strip().lower()):
                    logger.info('Filename %s matches rule.', filename)
                    dest_path = os.path.join(dest, filename)
                    source_path = os.path.join(source, filename)
                    try:
                        os.unlink(dest_path)
                    except:
                        pass
                    logger.info('Moving file.')
                    shutil.move(source_path, dest_path)
    except:
        logger.exception('')
    finally:
        if c is not None:
            c.close()
        if ctx is not None:
            ctx.close()

#==========================================================================
#0
