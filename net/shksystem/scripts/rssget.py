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
import time
import logging
import re
import configparser
# installed
from celery import Celery
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
import keyring
import feedparser
from transmissionrpc import Client as TrCli
# custom
import net.shksystem.common.utils as utils
from net.shksystem.common.send_mail import SendMail

#==========================================================================
# Environment/Static variables
#==========================================================================

logger = logging.getLogger(__name__)
Base = declarative_base()
queue = Celery('tasks', backend='amqp://', broker='amqp://')

#==========================================================================
# Classes/Functions
#==========================================================================

# -- MODELS
# -------------------------------------------------------------------------

class Feed(Base):
    __tablename__ = 'feeds'
    nudoss = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    rules = relationship('Rule', backref='feed')

class Rule(Base):
    __tablename__ = 'rules'
    nudoss = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    regex = Column(String, nullable=False)
    feed_id = Column(Integer, ForeignKey('feeds.nudoss'), nullable=False)
    dlleds = relationship('DLLed', backref='rule')

class DLLed(Base):
    __tablename__ = 'dlleds'
    nudoss = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    dayofdown = Column(String, nullable=False)
    rule_id = Column(Integer, ForeignKey('rules.nudoss'), nullable=False)

# -- PROCESSES
# -------------------------------------------------------------------------

@queue.task
def run_feed(feed_id, cnf):
    Session = sessionmaker(bind=create_engine(cnf['DB_URI']))
    db = Session()
    rc = transmissionrpc.Client(cnf['TRANSMISSION']['HOST'], cnf['TRANSMISSION']['PORT'])
    c.execute('SELECT url FROM feeds WHERE id={0}'.format(feed_id,))
    feed = db.query(Feed).filter(feed_id=feed_id).fetchone()
    rss = feedparser.parse(feed.url)
    logger.info('Current feed : %s', feed.url)
    for rule in feed.rules:
        logger.info('Running rule : %s', rule.title)
        already_got = [x[0] for x in c.fetchall()]
        for entry in rss.entries:
            title = entry['title'].strip().lower()
            if re.match(rule[2], title) and (title not in already_got):
                try:
                    rc.add_torrent(entry['torrent_magneturi'])
                    c.execute('INSERT INTO dlleds(filename, dayofdown, rule_id) VALUES (\'{0}\', \'{1}\', {2})'
                              .format(title, utils.get_current_timestamp(), rule[0]))
                except transmissionrpc.error.TransmissionError:
                    logger.exception('Unable to add new torrent.')
                    break
                except psycopg2.ProgrammingError:
                    logger.exception('Unable to persist download filename.')
                    break
                logger.info('Torrent %s added.', title)
                subject = 'New video.'
                msg = 'The file {0} will soon be available. Download in progress...'.format(title,)
                to = msg_to.split(',')
                mail.send_mail(msg_from, subject, msg, to)
    dbcon.commit()

def run_feeds(cnf):
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
    msg_host = config.get('email', 'host')
    msg_port = config.getint('email', 'port')
    msg_user = config.get('email', 'user')
    msg_from = config.get('email', 'from')
    msg_to = config.get('email', 'to')
    tr_host = config.get('transmission', 'host')
    tr_port = config.getint('transmission', 'port')

    ctx = None
    c = None
    try:
        if db_use_pwd:
            passwd = keyring.get_password(db_host, db_user)
            ctx = psycopg2.connect(database=db_name, user=db_user, password=passwd, host=db_host, port=db_port, sslmode=db_ssl)
            db_url = 'psycopg2+postgresql://{0}:{1}@{2}:{3}/{4}{5}'.format(db_user, passwd, db_host, db_port, db_name, db_ssl)
        else:
            ctx = psycopg2.connect(database=db_name, user=db_user, host=db_host, port=db_port, sslmode=db_ssl)

        c = ctx.cursor()

        c.execute('SELECT COUNT(id) FROM dlleds')
        cnt_dlleds = c.fetchone()[0]
        c.execute('SELECT COUNT(title) FROM rules')
        cnt_rules = c.fetchone()[0]
        c.execute('SELECT COUNT(url) FROM feeds')
        cnt_feeds = c.fetchone()[0]

        logger.info('Total of downloads : %d', cnt_dlleds)
        logger.info('Number of rules    : %d', cnt_rules)
        logger.info('Number of feeds    : %d', cnt_feeds)

        mail = SendMail(msg_host, msg_port, msg_user)
        c.execute('SELECT DISTINCT feed_id FROM rules')
        all_tasks = []
        for feed_id in [x[0] for x in c.fetchall()]:
            task = run_feed.delay(feed_id, ctx, tr_host, tr_port, mail)
            all_tasks.append(task)
        print('Processing tasks...')
        while not all([x.ready() for x in all_tasks]):
            time.sleep(2)
            print('...')

    except:
        logger.exception('')
    finally:
        if c is not None:
            c.close()
        if ctx is not None:
            ctx.close()

#==========================================================================
#0
