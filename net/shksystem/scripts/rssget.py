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
import requests
from sqlalchemy                     import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative     import declarative_base
from sqlalchemy.orm                 import sessionmaker
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
    __tablename__ = 'rules'
    nudoss        = Column(Integer, primary_key=True)
    is_active     = Column(Boolean, default=False)
    name          = Column(String, nullable=False)
    dest          = Column(String, nullable=False)
    regex         = Column(String, nullable=False)
    feed          = Column(Integer, ForeignKey('feeds.nudoss'))
    dlleds        = relationship('DLLed', backref='dlleds')

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
        with open(dest_fic) as f1:
            for w1 in csv.reader(f1):
                s.add(Recipient(w1[0]))
        with open(serv_fic) as f2:
            for w2 in csv.reader(f2):
                s.add(Server(w2[0], int(w2[1]), w2[2], w2[3], w2[4]))
        s.commit()
    else:
        if not (all(map(os.path.isfile, [feed_fic, rule_fic]))):
            logger.info('Required data files do not exist. Database does not need updates.')
        else:
            Session = sessionmaker(bind=engine)
            s       = Session()
            logger.info('Reading configuration files and updating database if needed.')
            with open(feed_fic) as f1:
                data      = list(csv.reader(f1))
                row_count = len(data)
                db_count  = s.query(Feed.nudoss).count()
                logger.debug('1001102 - 2 - Feeds relative informations =')
                logger.debug('Number of rows in csv file : ' + row_count)
                logger.debug('Number of queryed feeds    : ' + db_count)
                if  row_count == db_count:
                    logger.info('Nothing to update for feeds')
                else:
                    for row in data:
                        if
            with open(dest_fic) as f1:
                for w1 in csv.reader(f1):
                    s.add(Recipient(w1[0]))
            with open(serv_fic) as f2:
                for w2 in csv.reader(f2):
                    s.add(Server(w2[0], int(w2[1]), w2[2], w2[3], w2[4]))
            s.commit()

    logger.info('Database is ready for business')

    logger.info('Running recipients.')
    Session1 = sessionmaker(bind=engine)
    s1       = Session1()
    serv     = s1.query(Server).first()

    logger.info('Sending emails')
    sm      = SendMail(serv.hostname, serv.port, serv.username)
    recs    = [x.mail for x in s1.query(Recipient).all()]
    subject = '[DISPO] {0}'.format(get_current_timestamp(),)
    sender  = serv.sender
    send    = False
    for case in Switch(imperium):
        if case('arrivee'):
            msg  = 'Ready for business.'
            send = True
            break
        if case('depart'):
            msg  = 'Bonne soirée'
            send = True
            break
        if case('depart_pause'):
            msg  = 'Go pause, a toute.'
            send = True
            break
        if case('fin_pause'):
            msg  = 'Re.'
            send = True
            break
    if send:
        for rec in recs:
            sm.send_mail(sender, subject, msg, [rec], [])
    else:
        logger.info('Nothing to be done.')
    logger.debug('100102 - END')

#==========================================================================
#0
