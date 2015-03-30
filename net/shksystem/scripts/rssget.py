# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Automatic torrent RSS flux crawling
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 15.03.2015
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
import logging
import re
import configparser
# installed
from pymongo import MongoClient
import feedparser
import transmissionrpc
# custom
from net.shksystem.common.error import FileNotFound
import  net.shksystem.common.utils as utils

#==========================================================================
# Environment/Static variables
#==========================================================================

logger = logging.getLogger(__name__)
base_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
Base = declarative_base()

#==========================================================================
# Classes/Functions
#==========================================================================

# -- PROCESSES
# -------------------------------------------------------------------------

def run_feeds():

    conf_dir = os.path.abspath('../etc'.format(base_name,))
    conf_file = os.path.join(conf_dir, '{0}.ini'.format(base_name,))
    if not (all(map(os.path.isfile, [conf_file]))):
        logger.error('Please check if file %s exists.', conf_file)
        raise FileNotFound
    config = configparser.ConfigParser()
    config.read(conf_file)

    db_host = config.get('database', 'host')
    db_port = config.getint('database', 'port')
    db_name = config.get('database', 'db_name')
    tr_host = config.get('transmission', 'host')
    tr_port = config.getint('transmission', 'port')

    client = MongoClient(db_host, db_port)
    db = client[db_name]

    feeds = db[base_name + '_feeds']
    dlleds = db[base_name + '_dlleds']
    rules = db[base_name + '_rules']

    logger.info('Total of downloads : %d', dlleds.count())
    logger.info('Number of rules    : %d', rules.count())
    logger.info('Number of feeds    : %d', feeds.count())

    rc = transmissionrpc.Client(tr_host, tr_port)
    for feed in feeds.find().distinct('url'):
        rss = feedparser.parse(feed)
        logger.info('Current feed : %s', feed)
        for rule in rules.find():
            logger.info('Running rule : %s', rule['name'])
            for entry in rss.entries:
                title = entry['title'].strip().lower()
                if re.match(rule['regex'], title) and (title not in dlleds.find().distinct('title')):
                    dlleds.insert({'title': title, 'date': utils.get_current_timestamp()})
                    rc.add_torrent(entry['torrent_magneturi'])
                    logger.info('Torrent %s added.', title)

#==========================================================================
#0
