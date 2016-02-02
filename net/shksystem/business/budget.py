# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
import re
import json
# installed
import numpy
import pandas as pa
import requests
import feedparser
import transmissionrpc as tr
import shutil
# custom
from sahoka.common.logic import Switch
from sahoka.common.send_mail import SendMail
from sahoka.common.utils import regexify

# Globals
# =============================================================================

logger = logging.getLogger(__name__)

# Classes and Functions
# =============================================================================


class ReleaseFrame(object):
    """ This class implements getters for popular sites feeds """

    def _remove_leaves(self, d, regex, has_episodes=False, has_seasons=False):
        d = d.reindex(columns=['title', 'published', 'size', 'magnet_uri'])
        d.sort(['published', 'title', 'size'], ascending=False, inplace=True)

        def map_title(regex, group_num, default_ret, title):
            ret = default_ret
            ma = re.match(regex, title)
            if ma and re.compile(regex).groups >= group_num:
                ret = ma.group(group_num).strip()
            return ret

        if has_episodes and has_seasons:
            season_grp = 2
            episode_grp = 3
        elif has_episodes:
            season_grp = 110
            episode_grp = 2
        else:
            season_grp = 110
            episode_grp = 110

        d['name'] = d['title'] \
                .map(lambda x: map_title(regex, 1, numpy.nan, x))
        d.dropna(inplace=True)
        d['episode'] = d['title'] \
                .map(lambda x: int(map_title(regex, episode_grp, 0, x)))
        d['season'] = d['title'] \
                .map(lambda x: int(map_title(regex, season_grp, 0, x)))
        d.drop_duplicates(['name', 'season', 'episode'], inplace=True)

        return d

    def _get_from_kickass(self, kat_uri, regex, has_episodes=False,
                          has_seasons=False):
        rss = feedparser.parse(kat_uri)
        d = pa.DataFrame(rss['entries'])
        d.rename(columns={'torrent_magneturi': 'magnet_uri',
                          'torrent_contentlength': 'size'}, inplace=True)
        d = self._remove_leaves(d, regex, has_episodes, has_seasons)
        return d


    def _get_from_strike(self, strike_uri, regex, has_episodes=False,
                         has_seasons=False):
        r = requests.get(strike_uri)
        j = json.loads(r.text)
        d = pa.DataFrame(j['torrents'])
        d.rename(columns={'torrent_title': 'title', 'upload_date': 'published'},
                 inplace=True)
        d = self._remove_leaves(d, regex, has_episodes, has_seasons)
        return d

    def get(self, backend, uri, regex, has_episodes=False, has_seasons=False):
        ret = None
        for case in Switch(backend):
            if case('kickass'):
                try:
                    ret = self._get_from_kickass(kickass_url, regex,
                                                 has_episodes, has_seasons)
                except:
                    logger.exception('Cannot fetch feed from kickass backend.')
                break
            if case('strike'):
                try:
                    ret = self._get_from_strike(strike_url, regex,
                                                has_episodes, has_seasons)
                except:
                    logger.exception('Cannot fetch feed from strike backend')
                break
            if case():
                logger.error('No valid backend specified.')
        return ret

    def get_rule(self, d, name, mail, tr_host='localhost', tr_port=9091):
        added = []
        f = d[d['name'] == name]
        # Connecting to transmission and mail server
        #ml = SendMail(mail['SERVER'], mail['PORT'], mail['USERNAME'])
        rc = tr.Client(tr_host, tr_port)
        for i, r in f.iterrows():
            rc.add_torrent(r['magnet_uri'])
            added.append(r['title'])
            #ml.send_mail(mail['SENDER'], mail['SUBJECT'], r['title'],
            #             mail['DEST'].split(','))
        return added

    def range_rule(self, cat, name, dl_dir, release_dir):
        r = regexify(name)
        for fic in os.listdir(dl_dir):
            if re.match(r, fic):
                shutil.move(os.path.join(dl_dir, fic),
                            os.path.join(release_dir, cat, name, fic))
#
