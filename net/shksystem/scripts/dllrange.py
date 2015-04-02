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
from pymongo import MongoClient
# custom
import net.shksystem.common.utils as utils

#==========================================================================
# Environment/Static variables
#==========================================================================

logger    = logging.getLogger(__name__)
base_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

#==========================================================================
# Classes/Functions
#==========================================================================

def run_rules():
    conf_dir = os.path.abspath('../etc'.format(base_name,))
    conf_file = os.path.join(conf_dir, '{0}.ini'.format(base_name,))
    if not (all(map(os.path.isfile, [conf_file]))):
        logger.error('Please check if file %s exists.', conf_file)
        raise OSError
    config = configparser.ConfigParser()
    config.read(conf_file)

    db_host = config.get('database', 'host')
    db_port = config.getint('database', 'port')
    db_name = config.get('database', 'db_name')

    client = MongoClient(db_host, db_port)
    db = client[db_name]

    sources = db[base_name + '_sources']
    rules = db[base_name + '_rules']

    for source in sources.find().distinct('path'):
        logger.info('Processing source : {0}.'.format(source,))

        logger.info('There is %d rules to process', rules.count())
        for rule in rules.find():
            logger.info('Treating rule named : {0}'.format(rule['name'],))
            dest = os.path.join(rule['cat'], rule['name'])
            if not os.path.isdir(dest):
                try:
                    os.mkdir(dest)
                except OSError as e:
                    logger.warn('Rule destination %s is not accessible. Skipping.', dest)
                    continue

            for filename in os.listdir(source):
                if re.match(rule['regex'], filename.strip().lower()):
                    logger.info('Filename {0} matches rule.'.format(filename,))
                    dest_path = os.path.join(dest, filename)
                    source_path = os.path.join(source, filename)
                    try:
                        os.unlink(dest_path)
                    except:
                        pass
                    logger.info('Moving file.')
                    shutil.move(source_path, dest_path)

#==========================================================================
#0
