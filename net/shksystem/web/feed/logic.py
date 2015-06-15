# -*- coding14.06.2015-

"""
    OBJET            : Automatic torrents flux crawling
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 14.06.2015
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
import shutil
# installed
from celery import Celery
import numpy
import pandas as pa
import requests
import feedparser
import transmissionrpc as tr
# custom
from net.shksystem.common.send_mail import SendMail

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)

queue = Celery('tasks', broker='amqp://')
# celery -A net.shksystem.web.feed.logic worker --loglevel=info

# -----------------------------------------------------------------------------
# Classes & Functions
# -----------------------------------------------------------------------------


class GetFeed(object):
    """ This class implements the frame getters for popular sites """

    def __init__(self, regex, strike_url, kickass_url, has_episodes=False,
                 has_seasons=False):
        self.regex = regex
        self.strike_url = strike_url
        self.kickass_url = kickass_url
        self.has_episodes = has_episodes
        self.has_seasons = has_seasons

    def _reord(self, d):
        d = d.reindex(columns=['title', 'published', 'size', 'magnet_uri'])
        d.sort(['published', 'title', 'size'], ascending=False, inplace=True)

        def map_title(regex, group_num, default_ret, title):
            ma = re.match(regex, title)
            if ma and re.compile(regex).groups >= group_num:
                ret = ma.group(group_num).strip()
            else:
                ret = default_ret
            return ret

        if self.has_episodes and self.has_seasons:
            season_grp = 2
            episode_grp = 3
        elif self.has_episodes:
            season_grp = 42
            episode_grp = 2
        else:
            season_grp = 42
            episode_grp = 42

        regex = self.regex
        d['name'] = d['title'] \
                .map(lambda x: map_title(self.regex, 1, numpy.nan, x))
        d.dropna(inplace=True)
        d['episode'] = d['title'] \
                .map(lambda x: int(map_title(self.regex, episode_grp, 0, x)))
        d['season'] = d['title'] \
                .map(lambda x: int(map_title(self.regex, season_grp, 0, x)))
        d.drop_duplicates(['name', 'season', 'episode'], inplace=True)

        return d

    def get_from_strike(self):
        r = requests.get(self.strike_url)
        j = json.loads(r.text)
        d = pa.DataFrame(j['torrents'])
        d.rename(columns={'torrent_title': 'title', 'upload_date': 'published'},
                 inplace=True)
        d = self._reord(d)
        return d

    def get_from_kickass(self):
        rss = feedparser.parse(self.kickass_url)
        d = pa.DataFrame(rss['entries'])
        d.rename(columns={'torrent_magneturi': 'magnet_uri',
                          'torrent_contentlength': 'size'}, inplace=True)
        d = self._reord(d)
        return d

    def get(self):
        ret = None
        retry = False
        try:
            ret = self.get_from_strike()
        except:
            logger.exception('Cannot get json from Strike API.')
            retry = True
        if retry:
            try:
                ret = self.get_from_kickass()
            except:
                logger.exception('Cannot get feed from kickass RSS.')
        return ret


@queue.task
def run_frame(cnf, feed):
    logger.info('Running frame...')

    # Reading Excel rules
    rules = pa.read_excel(cnf['RULES_XLS'], sheetname=group.rule_sheet)
    rules = feed.rules
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
