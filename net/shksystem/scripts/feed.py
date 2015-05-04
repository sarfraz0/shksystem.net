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
# installed
from celery import Celery
import pandas as pa
import requests
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
# celery -A net.shksystem.scripts.feed worker --loglevel=info
queue = Celery('tasks', broker='amqp://' + os.environ['CELERY_BROKER_HOST'])

# -----------------------------------------------------------------------------
# Classes & Functions
# -----------------------------------------------------------------------------

# MODELS
# -------------------------------------------------------------------------


class DLLed(Base):
    __tablename__ = 'dlleds'
    nudoss = Column(Integer, primary_key=True)
    magnet_uri = Column(String, nullable=False)
    dayofdown = Column(String, nullable=False)

# PROCESSES
# -------------------------------------------------------------------------


class GenericGet(object):
    """ This class implements the frame getters for popular sites"""

    def __init__(self, release_regex):
        self.release_regex = release_regex

    def get_from_strike(self, strike_url):
        r = requests.get(strike_url)
        j = json.loads(r.text)
        d = pa.DataFrame(j)
        d.drop(['download_count', 'file_count', 'imdbid', 'leeches', 'page',
                'rss_feed', 'seeds', 'sub_category', 'torrent_category',
                'torrent_hash', 'uploader_username'], axis=1, inplace=True)
        d.rename(columns={'torrent_title': 'title', 'upload_date': 'published'},
                 inplace=True)
        d = d.reindex(columns=['title', 'published', 'size', 'magnet_uri'])
        d['published'] = d['published'].apply(dateutil.parser.parse)
        d.sort(['published', 'title', 'size'], ascending=False, inplace=True)
        d['name'] = d['title'] \
            .map(lambda x: re.match(self.release_regex, x,
                                    re.IGNORECASE).group(1).strip())
        return d

    def get_from_kickass(self, kickass_url):
        rss = feedparser.parse(kickass_url)
        d = pa.DataFrame(rss['entries'])
        d.drop(['author', 'author_detail', 'authors', 'guidislink', 'id',
                'link', 'links', 'published_parsed', 'tags', 'title_detail',
                'torrent_filename', 'torrent_infohash', 'torrent_peers',
                'torrent_seeds', 'torrent_verified'], axis=1, inplace=True)
        d.rename(columns={'torrent_magneturi': 'magnet_uri',
                          'torrent_contentlength': 'size'}, inplace=True)
        d = d.reindex(columns=['title', 'published', 'size', 'magnet_uri'])
        d.sort(['published', 'title', 'size'], ascending=False, inplace=True)
        d['name'] = d['title'] \
            .map(lambda x: re.match(self.release_regex, x,
                                    re.IGNORECASE).group(1).strip())
        return d


class GetDimension(GenericGet):
    """ This class role is to get new DIMENSION releases to transmission"""

    def __init__(self):
        self.rule_sheet = 'USATV'
        dimension_regex = '^([a-zA-Z0-9\s-]+)S(\d{1,2})E(\d{1,2})(E\d{1,2})?\s(720p|1080p)\sHDTV\sX264(\sDTS)?-DIMENSION.*$'
        super(self.__class__, self).__init__(dimension_regex)

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
            retry = True
        if retry:
            try:
                ret = self.get_from_kickass()
            except:
                pass
        return ret

class GetDimension(GenericGet):
    """ This class role is to get new DIMENSION releases to transmission"""

    def __init__(self):
        self.rule_sheet = 'USATV'
        dimension_regex = '^([a-zA-Z0-9\s-]+)S(\d{1,2})E(\d{1,2})(E\d{1,2})?\s(720p|1080p)\sHDTV\sX264(\sDTS)?-DIMENSION.*$'
        super(self.__class__, self).__init__(dimension_regex)

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
            retry = True
        if retry:
            try:
                ret = self.get_from_kickass()
            except:
                pass
        return ret


class GetYIFY(GenericGet):
    """ This class role is to get new YIFY releases to transmission"""

    def __init__(self):
        self.rule_sheet = 'USAMovies'
        yify_regex = ''
        super(self.__class__, self).__init__(yify_regex)

    def get_from_yify(self, yify_url=''):
        pass

    def get_from_strike(self, strike_url=''):
        ret = super(self.__class__, self).get_from_strike(strike_url)
        return ret

    def get_from_kickass(self, kickass_url=''):
        ret = super(self.__class__, self).get_from_strike(kickass_url)
        return ret

    def get(self):
        ret = None
        retry = False
        try:
            ret = self.get_from_yify()
        except:
            retry = True
        if retry:
            try:
                ret = self.get_from_strike()
                retry = False
            except:
                retry = True
        if retry:
            try:
                ret = self.get_from_kickass()
            except:
                pass
        return ret

class GetFRENCH(GenericGet):
    """ This class role is to get new FRENCH tagged releases to transmission"""

    def __init__(self):
        self.rule_sheet = 'USATV'
        dimension_regex = '^([a-zA-Z0-9\s-]+)S(\d{1,2})E(\d{1,2})(E\d{1,2})?\s(720p|1080p)\sHDTV\sX264(\sDTS)?-DIMENSION.*$'
        super(self.__class__, self).__init__(dimension_regex)

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
            retry = True
        if retry:
            try:
                ret = self.get_from_kickass()
            except:
                pass
        return ret

@queue.task
def run_frame(cnf, group):
    logger.info('Running frame...')
    Session = sessionmaker(bind=create_engine(cnf['DB_URI']))
    db = Session()
    logger.info('Database initialized.')
    rules = pa.read_excel(cnf['RULES_XLS'], sheetname=group.rule_sheet)
    logger.info('Excel rules loaded')
    feeds = group.get()
    feeds['name'] = feeds['name'].map(lambda x: x.strip().lower())
    logger.info('Done querying news feeds')
    ml = SendMail(cnf['EMAIL']['HOST'], cnf['EMAIL']['PORT'],
                  cnf['EMAIL']['USER'])
    rc = tr.Client(cnf['TRANSMISSION']['HOST'], cnf['TRANSMISSION']['PORT'])
    logger.info('Connection to transmission open')
    logger.info('Iterating on rules')
    for index, name in rules['Name'].iteritems():
        logger.info('Treating rule for %s', name)
        concerned_feeds = feeds[feeds['name'] == name.strip().lower()]
        logger.info('Filtering on name')
        if len(concerned_feeds) > 0:
            logger.info('Filter returned elements to process')
            for index, row in concerned_feeds.iterrows():
                if db.query(DLLed).filter_by(magnet_uri=row['magnet_uri']) \
                                  .count() < 1:
                    logger.info('First time encountering element. Processing..')
                    try:
                        rc.add_torrent(row['magnet_uri'])
                    except tr.error.TransmissionError:
                        break
                    db.add(DLLed(magnet_uri=row['magnet_uri'],
                                 dayofdown=utils.get_current_timestamp()))
                    logger.info('Torrent %s added.', row['title'])
                    subj = 'New video.'
                    msg = 'The file {0} will soon be available.' \
                        .format(row['title'],) + ' Download in progress...'
                    ml.send_mail(cnf['EMAIL']['FROM'],
                                 subj, msg, cnf['EMAIL']['TO'])
    db.commit()


def get_torrents(cnf):
    logger.info('Getting DIMENSION feed')
    dim = GetDimension()
    run_frame.delay(cnf, dim)
    logger.info('Getting HorribleSubs feed')
    hor = GetHorribleSubs()
    run_frame.delay(cnf, hor)
    logger.info('Getting YIFY feed')
    yif = GetYIFY()
    run_frame.delay(cnf, yif)

@queue.task
def dllrange(cnf):
    pass

# -----------------------------------------------------------------------------
#
