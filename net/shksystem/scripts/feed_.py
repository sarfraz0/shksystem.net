# -*- coding: utf-8 -*-

"""
    OBJET            : Automatic torrents flux crawling
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
import json
import dateutil
import shutil
# installed
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from celery import Celery
import numpy
import pandas as pa
import requests
import feedparser
import transmissionrpc as tr
# custom
from net.shksystem.common.utils import get_current_timestamp, format_to_regex
from net.shksystem.common.send_mail import SendMail

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)

Base = declarative_base()
queue = Celery('tasks', broker='amqp://')
# celery -A net.shksystem.scripts.feed worker --loglevel=info

# -----------------------------------------------------------------------------
# Classes & Functions
# -----------------------------------------------------------------------------


class DLLed(Base):
    """ Trace of already downloaded goods """
    __tablename__ = 'dlleds'

    nudoss = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    magnet_uri = Column(String, nullable=False)
    hashed_name = Column(String, nullable=False)
    dayofdown = Column(String, nullable=False)

    def __init__(self, name, hashed_name, magnet_uri):
        self.name = name
        self.hashed_name = hashed_name
        self.magnet_uri = magnet_uri
        self.dayofdown = get_current_timestamp()

    def  create_hash(conc_list, sep=''):
        pass


class GenericGet(object):
    """ This class implements the frame getters for popular sites """

    def __init__(self, release_regex):
        self.release_regex = release_regex

    def _reord(self, d):
        d = d.reindex(columns=['title', 'published', 'size', 'magnet_uri'])
        d.sort(['published', 'title', 'size'], ascending=False, inplace=True)
        d['name'] = d['title'] \
            .map(lambda x: re.match(self.release_regex, x, re.IGNORECASE) \
                 .group(1).strip() if re.match(self.release_regex,
                                               x, re.IGNORECASE) else numpy.nan)
        d.dropna(inplace=True)
        return d

    def get_from_strike(self, strike_url):
        r = requests.get(strike_url)
        j = json.loads(r.text)
        d = pa.DataFrame(j['torrents'])
        d.rename(columns={'torrent_title': 'title', 'upload_date': 'published'},
                 inplace=True)
        d = self._reord(d)
        return d

    def get_from_kickass(self, kickass_url):
        rss = feedparser.parse(kickass_url)
        d = pa.DataFrame(rss['entries'])
        d.rename(columns={'torrent_magneturi': 'magnet_uri',
                          'torrent_contentlength': 'size'}, inplace=True)
        d = self._reord(d)
        return d


class GetDimension(GenericGet):
    """ This class role is to get new DIMENSION releases to transmission"""

    def __init__(self):
        self.rule_sheet = 'TV'
        self.dimension_regex = '^([a-zA-Z0-9\s-]+)S(\d{1,2})E(\d{1,2})(E\d{1,2})?\s(720p|1080p)\sHDTV\sX264-DIMENSION.*$'
        super(self.__class__, self).__init__(self.dimension_regex)

    def _remove_duplicates(self, df):
        df['season'] = df['title'] \
            .map(lambda x: int(re.match(self.dimension_regex, x,
                                        re.IGNORECASE).group(2)))
        df['episode'] = df['title'] \
            .map(lambda x: int(re.match(self.dimension_regex, x,
                                        re.IGNORECASE).group(3)))
        df.drop_duplicates(['name', 'season', 'episode'], inplace=True)
        return df

    def get_from_strike(self, strike_url='https://getstrike.net/api/v2/torrents/search/?phrase=DIMENSION&category=TV'):
        ret = super(self.__class__, self).get_from_strike(strike_url)
        ret = self._remove_duplicates(ret)
        return ret

    def get_from_kickass(self, kickass_url='https://kickass.to/usearch/DIMENSION%20category%3Atv/?rss=1'):
        ret = super(self.__class__, self).get_from_kickass(kickass_url)
        ret = self._remove_duplicates(ret)
        return ret

    def get(self):
        ret = None
        retry = False
        try:
            ret = self.get_from_strike()
        except:
            logger.exception('Cannot get DIMENSION feed from Strike API.')
            retry = True
        if retry:
            try:
                ret = self.get_from_kickass()
            except:
                logger.exception('Cannot get DIMENSION feed from kickass RSS.')
        return ret


class GetHorribleSubs(GenericGet):
    """ This class role is to get new HorribleSubs releases to transmission"""

    def __init__(self):
        self.rule_sheet = 'Animes'
        horrible_regex = '^.HorribleSubs.\s([a-zA-Z0-9\s\'!-]+)\s-\s(\d{1,2}).*1080p.*$'
        super(self.__class__, self).__init__(horrible_regex)

    def get_from_strike(self, strike_url='https://getstrike.net/api/v2/torrents/search/?phrase=HorribleSubs%201080p&category=Anime'):
        ret = super(self.__class__, self).get_from_strike(strike_url)
        return rethttps://getstrike.net/api/v2/torrents/search/?phrase=HorribleSubs%201080p&category=Anime

    def get_from_kickass(self, kickass_url='http://kickass.to/usearch/HorribleSubs%201080p/?rss=1'):
        ret = super(self.__class__, self).get_from_kickass(kickass_url)
        return ret

    def get(self):
        ret = None
        retry = False
        try:
            ret = self.get_from_strike()
        except:
            logger.exception('Cannot get HorribleSubs feed from Strike API.')
            retry = True
        if retry:
            try:
                ret = self.get_from_kickass()
            except:
                logger.exception('Cannot get DIMENSION feed from kickass RSS.')
        return ret


@queue.task
def run_frame(cnf, group):

    # Connecting to database
    logger.info('Connecting to database...')
    Session = sessionmaker(bind=create_engine(cnf['DB_URI']))
    s = Session()
    logger.info('Running frame...')

    # Reading Excel rules
    rules = pa.read_excel(cnf['RULES_XLS'], sheetname=group.rule_sheet)
    logger.info('Excel rules loaded')
    feeds = group.get()
    feeds['lower_name'] = feeds['name'].map(lambda x: x.strip().lower())
    logger.info('Done querying news feeds')

    # Connecting to transmission and mail server
    ml = SendMail(cnf['EMAIL']['HOST'], cnf['EMAIL']['PORT'],
                  cnf['EMAIL']['USER'])
    rc = tr.Client(cnf['TRANSMISSION']['HOST'], cnf['TRANSMISSION']['PORT'])
    logger.info('Connection to transmission open')

    # Parsing rules
    logger.info('Iterating on rules')
    uris = [x.magnet_uri for x in s.query(DLLed).all()]
    for index, rule_row in rules.iterrows():
        name = rule_row['Name']
        logger.info('Treating rule for %s', name)
        concerned_feeds = feeds[feeds['lower_name'] == name.strip().lower()]
        logger.info('Filtering on name')
        if len(concerned_feeds) > 0:
            logger.info('Filter returned elements to process')
            for index, feed_row in concerned_feeds.iterrows():
                magnet_uri = feed_row['magnet_uri']
                if magnet_uri not in uris:
                    logger.info('First time encountering element. Processing..')
                    try:
                        rc.add_torrent(magnet_uri)
                    except tr.error.TransmissionError:
                        break
                    s.add(DLLed(feed_row['name'], magnet_uri))
                    logger.info('Torrent %s added.', feed_row['title'])
                    subj = 'New video.'
                    msg = 'The file {0} will soon be available.' \
                              .format(
                        feed_row['title'], ) + ' Download in progress...'
                    ml.send_mail(cnf['EMAIL']['FROM'],
                                 subj, msg, cnf['EMAIL']['TO'])
    s.commit()


def get_torrents(cnf):
    logger.info('Getting DIMENSION feed')
    dim = GetDimension()
    run_frame.delay(cnf, dim)
    logger.info('Getting HorribleSubs feed')
    hor = GetHorribleSubs()
    run_frame.delay(cnf, hor)


@queue.task
def dllrange(cnf, rules):
    for source in cnf['SOURCES']:
        logger.info('Processing source : %s.', source)
        for rindex, rule in rules.iterrows():
            logger.info('Treating rule named : %s', rule['Name'])
            dest = os.path.join(rule['Destination'], rule['Name'])
            if not os.path.isdir(dest):
                try:
                    os.mkdir(dest)
                except OSError:
                    logger.warn('Rule destination {0} is not accessible.'
                                .format(dest, ) + ' Skipping.')
                    continue
            for filename in os.listdir(source):
                if re.match(format_to_regex(rule['Name']),
                            filename.strip().lower()):
                    logger.info('Filename %s matches rule.', filename)
                    dest_path = os.path.join(dest, filename)
                    try:
                        os.unlink(dest_path)
                    except:
                        pass
                    logger.info('Moving file.')
                    shutil.move(os.path.join(source, filename), dest_path)


def dllranges(cnf):
    xl = pa.ExcelFile(cnf['RULES_XLS'])
    for current_sheet in xl.sheet_names:
        dllrange.delay(cnf, xl.parse(current_sheet))

# -----------------------------------------------------------------------------
#
