# -*- coding: utf-8 -*-

"""
    OBJET            : Automatic torrent RSS flux crawling
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 15.03.2015
    LICENSE          : GPL-3
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# standard
import os
import logging
import re
# installed
from celery import Celery
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import feedparser
import transmissionrpc as tr
# custom
import net.shksystem.common.utils as utils
from net.shksystem.common.send_mail import SendMail

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)
Base = declarative_base()
# celery -A net.shksystem.scripts.rssget worker --loglevel=info
queue = Celery('tasks', broker='amqp://' + os.environ['CELERY_BROKER_HOST'])

# -----------------------------------------------------------------------------
# Classes & Functions
# -----------------------------------------------------------------------------

# MODELS
# -------------------------------------------------------------------------


class Rule(Base):
    __tablename__ = 'rules'
    nudoss = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    regex = Column(String, nullable=False)
    dlleds = relationship('DLLed', backref='rule')


class DLLed(Base):
    __tablename__ = 'dlleds'
    nudoss = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    dayofdown = Column(String, nullable=False)
    rule_id = Column(Integer, ForeignKey('rules.nudoss'), nullable=False)

# PROCESSES
# -------------------------------------------------------------------------


def get_tv_dimension():
    pass

@queue.task
def run_feed(cnf, rules, fson):



@queue.task
def run_feed(feed_id, cnf):
    Session = sessionmaker(bind=create_engine(cnf['DB_URI']))
    db = Session()

    ml = SendMail(cnf['EMAIL']['HOST'],
                  cnf['EMAIL']['PORT'], cnf['EMAIL']['USER'])
    rc = tr.Client(cnf['TRANSMISSION']['HOST'], cnf['TRANSMISSION']['PORT'])

    feed = db.query(Feed).filter_by(nudoss=feed_id).one()
    rss = feedparser.parse(feed.url)
    logger.info('Current feed : %s', feed.url)
    for rule in feed.rules:
        logger.info('Running rule : %s', rule.title)
        already_got = [x.filename for x in rule.dlleds]
        for entry in rss.entries:
            title = entry['title'].strip().lower()
            if re.match(rule.regex, title) and (title not in already_got):
                try:
                    rc.add_torrent(entry['torrent_magneturi'])
                except tr.error.TransmissionError:
                    break
                db.add(DLLed(filename=title,
                             dayofdown=utils.get_current_timestamp(),
                             rule_id=rule.nudoss))
                logger.info('Torrent %s added.', title)
                subj = 'New video.'
                msg = 'The file {0} will soon be available.'.format(title,) + \
                    ' Download in progress...'
                ml.send_mail(cnf['EMAIL']['FROM'],
                             subj, msg, cnf['EMAIL']['TO'])
    db.commit()


def run_feeds(cnf):
    Session = sessionmaker(bind=create_engine(cnf['DB_URI']))
    db = Session()

    cnt_dlleds = db.query(DLLed).count()
    logger.info('Total of downloads : %d', cnt_dlleds)
    cnt_rules = db.query(Rule).count()
    logger.info('Number of rules    : %d', cnt_rules)
    cnt_feeds = db.query(Feed).count()
    logger.info('Number of feeds    : %d', cnt_feeds)

    for fid in [x.nudoss for x in db.query(Feed).all()]:
        run_feed.delay(fid, cnf)

# -----------------------------------------------------------------------------
#
