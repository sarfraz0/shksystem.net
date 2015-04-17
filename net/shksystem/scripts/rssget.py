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
import psycopg2
import keyring
import feedparser
import transmissionrpc
# custom
import net.shksystem.common.utils as utils
from net.shksystem.common.send_mail import SendMail

#==========================================================================
# Environment/Static variables
#==========================================================================

logger = logging.getLogger(__name__)

#==========================================================================
# Classes/Functions
#==========================================================================

# -- PROCESSES
# -------------------------------------------------------------------------

def run_feeds(conf_file):
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

        rc = transmissionrpc.Client(tr_host, tr_port)
        mail = SendMail(msg_host, msg_port, msg_user)
        c.execute('SELECT DISTINCT feed_id FROM rules')
        for feed_id in [x[0] for x in c.fetchall()]:
            c.execute('SELECT url FROM feeds WHERE id={0}'.format(feed_id,))
            url = c.fetchone()[0]
            rss = feedparser.parse(url)
            logger.info('Current feed : %s', url)
            c.execute('SELECT * FROM rules WHERE feed_id={0}'.format(feed_id,))
            for rule in c.fetchall():
                logger.info('Running rule : %s', rule[1])
                c.execute('SELECT filename FROM dlleds WHERE rule_id={0}'.format(rule[0]))
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
        ctx.commit()
    except:
        logger.exception('')
    finally:
        if c is not None:
            c.close()
        if ctx is not None:
            ctx.close()

#==========================================================================
#0
