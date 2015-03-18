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
# installed
import keyring
import configparser
import feedparser
#import requests
from sqlalchemy                     import create_engine, Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative     import declarative_base
from sqlalchemy.orm                 import sessionmaker, relationship
# custom
from net.shksystem.common.error     import FileNotFound
from net.shksystem.common.utils     import get_current_timestamp
from net.shksystem.common.send_mail import SendMail
from net.shksystem.common.logic     import Switch

#==========================================================================
# Environment/Static variables
#==========================================================================

logger    = logging.getLogger(__name__)
base_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
Base      = declarative_base()

#==========================================================================
# Classes/Functions
#==========================================================================

# -- Models
# -------------------------------------------------------------------------

class Rule(Base):
    __tablename__  = 'rules'
    nudoss         = Column(Integer, primary_key=True)
    is_active      = Column(Boolean, default=False)
    name           = Column(String, nullable=False)
    dest           = Column(String, nullable=False)
    regex          = Column(String, nullable=False)
    feed           = Column(Integer, ForeignKey('feeds.nudoss'))
    dlleds         = relationship('DLLed', backref='dlleds')
    __table_args__ = (UniqueConstraint('dest', 'regex', 'feed',  name='uq_rule'),)

    def __init__(self, name, dest, regex, feed_id):
        self.name  = name
        self.dest  = dest
        self.regex = regex
        self.feed  = feed_id

class Feed(Base):
    __tablename__  = 'feeds'
    nudoss         = Column(Integer, primary_key=True)
    feed_url       = Column(String, nullable=True, unique=True)
    rules          = relationship('Rule', backref='rules')
    last_checked   = Column(String, nullable=True)

    def __init__(self, feed_url):
        self.feed_url     = feed_url
        self.last_checked = get_current_timestamp()

class DLLed(Base):
    __tablename__  = 'dlleds'
    nudoss         = Column(Integer, primary_key=True)
    filename       = Column(String, nullable=False)
    rule           = Column(Integer, ForeignKey('rules.nudoss'))

    def __init__(self, filename, rule_id):
        self.filename = filename
        self.rule     = rule_id

# -- PROCESSES
# -------------------------------------------------------------------------
def run_feeds():
    logger.debug('100102 - BEGIN')

    conf_dir  = os.path.abspath('../etc/{0}'.format(base_name,))
    feed_fic  = os.path.join(conf_dir, 'feeds.csv')
    rule_fic  = os.path.join(conf_dir, 'rules.csv')
    db_fic    = os.path.join(conf_dir, '{0}.db'.format(base_name,))
    logger.debug('100102 - 1 - Setting up configuration files =')
    logger.debug('Configuration directory : ' + conf_dir)
    logger.debug('Feed list csv           : ' + feed_fic)
    logger.debug('Rule list csv           : ' + db_fic)
    logger.debug('SQLite database path    : ' + db_fic)
    engine    = create_engine('sqlite:///' + db_fic.replace('\\', '\\\\'))

    logger.info('#### Processing all feeds. ####')

    logger.info('Checking data.')
    if not os.path.isfile(db_fic):
        logger.info('Database file does not exist. Creating it.')
        if not (all(map(os.path.isfile, [feed_fic, rule_fic]))):
            logger.error('Required data files do not exist. Please create them and run again.')
            raise FileNotFound
        Base.metadata.create_all(engine)
        logger.info('Creating session to feed database.')
        Session = sessionmaker(bind=engine)
        s       = Session()
        logger.info('Reading configuration files and inserting into database.')
        with open(feed_fic) as f1:
            for w1 in csv.reader(f1):
                s.add(Feed(w1[0]))
        with open(rule_fic) as f2:
            for w2 in csv.reader(f2):
                s.add(Rule(w2[0], w2[1], w2[2], int(w2[3])))
        s.commit()
    else:
        if not (all(map(os.path.isfile, [feed_fic, rule_fic]))):
            logger.info('Required data files do not exist. Database does not need updates.')
        else:
            Session = sessionmaker(bind=engine)
            s       = Session()
            logger.info('Reading configuration files and updating database if needed.')
            with open(feed_fic) as f1:
                data      = [i for i in csv.reader(f1)]
                row_count = len(data)
                db_count  = s.query(Feed.nudoss).count()
                logger.debug('1001102 - 2 - Feeds relative informations =')
                logger.debug('Number of rows in csv file : ' + str(row_count))
                logger.debug('Number of queryed feeds    : ' + str(db_count))
                if  row_count == db_count:
                    logger.info('Nothing to update.')
                else:
                    for row in data:
                        if s.query(Feed).filter_by(feed_url=row[0]).first() is None:
                            s.add(Feed(row[0]))
            with open(rule_fic) as f2:
                data      = [i for i in csv.reader(f2)]
                row_count = len(data)
                db_count  = s.query(Rule.nudoss).count()
                logger.debug('1001102 - 3 - Rules relative informations =')
                logger.debug('Number of rows in csv file : ' + str(row_count))
                logger.debug('Number of queryed feeds    : ' + str(db_count))
                if  row_count == db_count:
                    logger.info('Nothing to update.')
                else:
                    for row in data:
                        if s.query(Rule).filter( (Rule.dest == row[1]) & (Rule.regex == row[2]) & (Rule.feed == int(row[3])) ).first() is None:
                            s.add(Rule(row[0], row[1], row[2], int(row[3])))
            s.commit()
    logger.info('Database is ready for business')

    logger.info('Running Rules.')
    Session  = sessionmaker(bind=engine)
    s        = Session()

    logger.debug('100102 - END')

#==========================================================================
#0
