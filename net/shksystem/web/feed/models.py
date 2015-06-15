# -*- coding: utf-8 -*-

""""
    OBJET            : Flask SQLAlchemy models
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 08.06.1015
    LICENSE          : GPL-3
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# standard
import os
# installed
from passlib.hash import sha512_crypt
from flask.ext.sqlalchemy import SQLAlchemy
# custom
from net.shksystem.common.utils import get_current_timestamp

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

db = SQLAlchemy()

# ------------------------------------------------------------------------------
# Classes and Functions
# ------------------------------------------------------------------------------


class User(db.Model):
    """Flask-Login User class"""
    __tablename__ = "users"
    k = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String, nullable=False, unique=True)
    passwhash = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    feeds = db.relationship('Feed', backref='user')

    def __init__(self, pseudo, passw, is_admin):
        self.pseudo = pseudo
        self.passwhash = sha512_crypt.encrypt(passw)
        self.is_admin = is_admin

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.k)


class Feed(db.Model):
    __tablename__ = 'feeds'
    k = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    regex = db.Column(db.String, nullable=False)
    strike_url = db.Column(db.String, nullable=False)
    kickass_url = db.Column(db.String, nullable=False)
    has_episodes = db.Column(db.Boolean, default=False)
    has_seasons = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    rules = db.relationship('Rule', backref='feed')
    user_k = db.Column(db.Integer, db.ForeignKey('users.k'))

    def __init__(self, name, regex, strike_url, kickass_url, user_k,
                 has_episodes=False, has_seasons=False, is_active=True):
        self.name = name
        self.regex = regex
        self.strike_url = strike_url
        self.kickass_url = kickass_url
        self.has_episodes = has_episodes
        self.has_seasons = has_seasons
        self.is_active = is_active
        self.user_k = user_k

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


class Rule(db.Model):
    __tablename__ = 'rules'
    k = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    dlleds = db.relationship('DLLed', backref='rule')
    feed_k = db.Column(db.Integer, db.ForeignKey('feeds.k'))

    def __init__(self, name, feed_k, is_active=True):
        self.name = name
        self.is_active = is_active
        self.feed_k = feed_k

class DLLed(db.Model):
    __tablename__ = 'dlleds'
    k = db.Column(db.Integer, primary_key=True)
    magnet_uri = db.Column(db.String, nullable=False)
    dayofdown = db.Column(db.String, nullable=False)
    in_filesytem = db.Column(db.Boolean, default=False)
    rule_k = db.Column(db.Integer, db.ForeignKey('rules.k'))

    def __init__(self, magnet_uri, filepath):
        self.magnet_uri = magnet_uri
        self.dayofdown = get_current_timestamp()
        self.in_filesystem = os.path.isfile(filepath)



# ------------------------------------------------------------------------------
#
