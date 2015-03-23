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
import csv
import logging
import re
import configparser
# installed
import feedparser
import transmissionrpc
#import requests
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
# custom
from net.shksystem.common.error import FileNotFound
from net.shksystem.common.utils import get_current_timestamp, remove_csv_duplicates

#==========================================================================
# Environment/Static variables
#==========================================================================

logger = logging.getLogger(__name__)
base_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
Base = declarative_base()

#==========================================================================
# Classes/Functions
#==========================================================================

# -- Models
# -------------------------------------------------------------------------

class Feed(Base):
    __tablename__ = 'feeds'
    nudoss = Column(Integer, primary_key=True)
    feed_url = Column(String, nullable=True, unique=True)
    rules = relationship('Rule', backref='rules')
    last_checked = Column(String, nullable=True)

    def __init__(self, feed_url):
        self.feed_url     = feed_url
        self.last_checked = get_current_timestamp()

class Rule(Base):
    __tablename__ = 'rules'
    nudoss = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    regex = Column(String, nullable=False)
    feed = Column(Integer, ForeignKey('feeds.nudoss'))
    __table_args__ = (UniqueConstraint('regex', 'feed',  name='uq_rule'),)

    def __init__(self, name, regex, feed_id):
        self.name = name
        self.regex = regex
        self.feed = feed_id

class DLLed(Base):
    __tablename__ = 'dlleds'
    nudoss = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    def __init__(self, title):
        self.title = title

# -- PROCESSES
# -------------------------------------------------------------------------
def run_feeds():

    conf_dir = os.path.abspath('../etc/{0}'.format(base_name,))

    conf_file = os.path.join(conf_dir, '{0}.ini'.format(base_name,))
    if not os.path.isfile(conf_file):
        logger.error('Configuration ini %s does not exist.', conf_file)
        raise FileNotFound
    config = configparser.ConfigParser()
    config.read(conf_file)

    db_fic = os.path.join(conf_dir, '{0}.db'.format(base_name,))
    engine = create_engine('sqlite:///' + db_fic.replace('\\', '\\\\'))

    feed_fic = os.path.join(conf_dir, 'feeds.csv')
    rule_fic = os.path.join(conf_dir, 'rules.csv')

    logger.debug('Conf fic is  : %s', conf_file)
    logger.debug('DB fic is    : %s', db_fic)
    logger.debug('Feed fic is  : %s', feed_fic)
    logger.debug('Rule fic is  : %s', rule_fic)

    if not os.path.isfile(db_fic):
        logger.info('Database file does not exist. Creating it.')
        if not (all(map(os.path.isfile, [feed_fic, rule_fic]))):
            logger.error('Required data files do not exist. Please create them and run again.')
            raise FileNotFound
        Base.metadata.create_all(engine)
        init_session = sessionmaker(bind=engine)
        session = init_session()
        remove_csv_duplicates(feed_fic)
        with open(feed_fic) as feed_hand:
            for row in csv.reader(feed_hand):
                session.add(Feed(row[0]))
        remove_csv_duplicates(rule_fic)
        with open(rule_fic) as rule_hand:
            for row in csv.reader(rule_hand):
                session.add(Rule(row[0], row[1], int(row[2])))
        session.commit()
    logger.info('Database is ready for business')

    logger.info('Running Rules.')
    init_session = sessionmaker(bind=engine)
    session = init_session()
    dlleds = [x.title for x in session.query(DLLed).all()]
    rc = transmissionrpc.Client(config.get('transmission', 'host'), config.getint('transmission', 'port'))
    for feed in session.query(Feed).all():
        logger.info('Running feed : %s', feed.feed_url)
        rss = feedparser.parse(feed.feed_url)
        for rule in feed.rules:
            logger.info('Running rule : %s', rule.name)
            for entry in rss.entries:
                title = entry['title']
                #logger.debug('Filtering on title : %s', title)
                if re.match(rule.regex, title.lower()) and (title not in dlleds):
                    session.add(DLLed(title))
                    rc.add_torrent(entry['torrent_magneturi'])
                    logger.info('Torrent %s added.', title)

#==========================================================================
#0
