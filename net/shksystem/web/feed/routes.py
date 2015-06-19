# -*- coding: utf-8 -*-

""""
    OBJET            : Flask routes
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 05.06.2015
    LICENSE          : GPL-3
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# standard
import os
import logging
# installed
from celery import Celery
from passlib.hash import sha512_crypt
from flask import Flask, render_template, request, redirect, url_for, \
    session, flash
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
# custom
from net.shksystem.common.logic import Switch
from net.shksystem.common.send_mail import SendMail
from net.shksystem.web.feed.models import db, User, Feed, Rule, DLLed, \
    MailServer
from net.shksystem.web.feed.forms import LoginForm, RemoveUser, AddUser, \
    ModifyUser, AddFeed, ModifyFeed, AddRule, ModifyRule, AddMailServer, \
    RemoveMailServer

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

logger = logging.getLogger(__name__)

queue = Celery('tasks', backend=os.environ['CELERY_BACKEND_URI'],
               broker=os.environ['CELERY_BROKER_URI'])
# celery -A net.shksystem.web.feed.logic worker --loglevel=info

app = Flask(__name__)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(k):
    return User.query.get(int(k))

# ------------------------------------------------------------------------------
# Classes and Functions
# ------------------------------------------------------------------------------
# NONE
# ------------------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------------------


class FeedFrame(object):
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
def run_frame(feed_id):
    logger.info('Running frame...')

    cnf = app.config
    feed = Feed.query.filter_by(k=feed_id).first()
    feed_frame = FeedFrame(feed.regex, feed.strike_url, feed.kickass_url,
                           feed.has_episodes, feed.has_seasons)

    # Connecting to transmission and mail server
    ml = SendMail(cnf['EMAIL']['HOST'], cnf['EMAIL']['PORT'],
                  cnf['EMAIL']['USER'])
    rc = tr.Client(cnf['TRANSMISSION']['HOST'], cnf['TRANSMISSION']['PORT'])
    logger.info('Connection to transmission open')

    # Parsing rules
    logger.info('Iterating on rules')
    for rule in feed.rules:
        uris = [x.magnet_uri for x in rule.dlleds]
        name = rule.name
        logger.info('Treating rule for %s', name)
        concerned_feeds = feed_frame[feed_frame['lower_name'] == name.strip().lower()]
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
                    db.session.add(DLLed(feed_row['name'], magnet_uri]))
                    db.session.commit()
                    logger.info('Torrent %s added.', feed_row['title'])
                    subj = 'New video.'
                    msg = 'The file {0} will soon be available.' \
                              .format(
                        feed_row['title'], ) + ' Download in progress...'
                    ml.send_mail(cnf['EMAIL']['FROM'],
                                 subj, msg, cnf['EMAIL']['TO'])
    s.commit(]


def get_torrents():
    for feed_id in [x.k in x for Feed.query.all()]:
        run_frame(feed_id).delay()


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

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

### Default
# -----------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    ret = render_template('login.html', login_form=login_form)
    if request.method == 'POST' and login_form.validate_on_submit():
        logger.info('User authentification.')
        pseudo = request.form['pseudo']
        passwd = request.form['password']
        user = User.query.filter_by(pseudo=pseudo).first()
        if user is not None:
            logger.info('User exists.')
            if sha512_crypt.verify(passwd, user.passwhash):
                login_user(user)
                flash('Login sucess, welcome {0}' \
                        .format(current_user.pseudo,), 'success')
                ret = redirect(url_for('index'))
    return ret

@app.route('/index', methods=['GET'])
@login_required
def index():
    ret = render_template('index.html')
    return ret

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    ret = redirect(url_for('login'))
    return ret

@app.route('/admin', methods=['GET'])
@login_required
def admin():
    ret = render_template('admin.html') if current_user.is_admin else \
            redirect(url_for('index'))
    return ret

@app.route('/admin/manage_users/<mode>', methods=['GET', 'POST'])
@login_required
def manage_users(mode):
    action_list = ['REMOVE', 'MODIFY', 'ADD']
    if current_user.is_admin:

        choices = [(a.k, a.pseudo) for a in User.query.all()]
        remove_form = RemoveUser()
        add_form = AddUser()
        modify_form = ModifyUser()
        for form in [remove_form, modify_form]:
            form.pseudo.choices = choices

        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    if remove_form.validate_on_submit():
                        pseudo = int(request.form['pseudo'])
                        db.session.delete(User.query.get(pseudo))
                        db.session.commit()
                        flash('User deleted!', 'success')
                        break
                if case('MODIFY'):
                    if modify_form.validate_on_submit():
                        user_obj = User.query.get(int(request.form['pseudo']))
                        if 'password' in request.form:
                            user_obj.passwhash = sha512_crypt \
                                    .encrypt(request.form['password'])
                        user_obj.is_admin = (('is_admin' in request.form) and \
                                (request.form['is_admin'] == 'y'))
                        db.session.commit()
                        flash('User modified!', 'success')
                        break
                if case('ADD'):
                    if add_form.validate_on_submit():
                        isadm = (('is_admin' in request.form) and \
                                (request.form['is_admin'] == 'y'))
                        new_user = User(request.form['pseudo'],
                                        request.form['password'], isadm)
                        db.session.add(new_user)
                        db.session.commit()
                        flash('User added!', 'success')
                        break
        else:
            if mode in action_list:
                ret = render_template('users.html', mode=mode,
                                      add_form=add_form,
                                      modify_form=modify_form,
                                      remove_form=remove_form)
            else:
                ret = redirect(url_for('admin'))
    else:
        ret = redirect(url_for('index'))
    return ret

@app.route('/admin/manage_mail_servers/<mode>', methods=['GET', 'POST'])
@login_required
def manage_mail_servers(mode):
    action_list = ['REMOVE', 'ADD']
    if current_user.is_admin:
        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    db.session.delete(MailServer.query.filter_by(k=request.form['mail_server']).first())
                    db.session.commit()
                    break
                if case('ADD'):
                    server = request.form['server']
                    username = request.form['username']
                    port = int(request.form['port'])
                    password = request.form['password']
                    sender = request.form['sender']
                    m = MailServer.query.filter_by(server=server).filter_by(username=username).first()
                    if m is None:
                        new_server = MailServer(server, username, password, sender)
                        new_server.port = port
                        db.session.add(new_server)
                        db.session.commit()
                    break
        else:
            if mode in action_list:
                add_form = AddMailServer()
                remove_form = RemoveMailServer()
                choices = [(a.k, '{0} - {1}'.format(a.username, a.server)) \
                        for a in MailServer.query.all()]
                remove_form.mail_server.choices = choices
                ret = render_template('mail_servers.html', mode=mode,
                                      add_form=add_form,
                                      remove_form=remove_form)
            else:
                ret = redirect(url_for('admin'))
    else:
        ret = redirect(url_for('index'))
    return ret


### API
# -----------------------------------------------------------------------------

@app.route('/api/v1/run/feed/<feed_name>', methods=['GET'])
def run_feed(feed_name):
    pass

@app.route('/api/v1/run/feeds', methods=['GET'])
def run_feeds():
    pass

# -----------------------------------------------------------------------------

### Custom
# -----------------------------------------------------------------------------


@app.route('/custom/data', methods=['GET'])
@login_required
def data():
    ret = render_template('data.html')
    return ret

@app.route('/custom/data/manage_feeds/<mode>', methods=['GET', 'POST'])
@login_required
def manage_feeds(mode):
    action_list = ['MODIFY', 'ADD']

    choices = [(a.k, a.name) for a in Feed.query.filter_by(user_k=current_user.k).all()]
    add_form = AddFeed()
    modify_form = ModifyFeed()
    modify_form.name.choices = choices

    if request.method == 'POST':
        ret = redirect(url_for('data'))
        for case in Switch(mode):
            if case('MODIFY'):
                if modify_form.validate_on_submit():
                    feed_obj = Feed.query.get(int(request.form['name']))
                    if 'regex' in request.form:
                        feed_obj.regex = request.form['regex']
                    if 'strike_url' in request.form:
                        feed_obj.strike_url = request.form['strike_url']
                    if 'kickass_url' in request.form:
                        feed_obj.kickass_url = request.form['kickass_url']
                    feed_obj.is_active = (('is_active' in request.form) and \
                            (request.form['is_active'] == 'y'))
                    feed_obj.has_episodes = (('has_episodes' in request.form) and \
                            (request.form['has_episodes'] == 'y'))
                    feed_obj.has_seasons = (('has_seasons' in request.form) and \
                            (request.form['has_seasons'] == 'y'))

                    db.session.commit()
                    flash('Feed modified!', 'success')
                    break
            if case('ADD'):
                if add_form.validate_on_submit():
                    is_active = (('is_active' in request.form) and \
                            (request.form['is_active'] == 'y'))
                    has_episodes = (('has_episodes' in request.form) and \
                            (request.form['has_episodes'] == 'y'))
                    has_seasons = (('has_seasons' in request.form) and \
                            (request.form['has_seasons'] == 'y'))

                    new_feed = Feed(request.form['name'],
                                    request.form['regex'],
                                    request.form['strike_url'],
                                    request.form['kickass_url'],
                                    current_user.k,
                                    is_active, has_episodes, has_seasons)
                    db.session.add(new_feed)
                    db.session.commit()
                    flash('Feed added!', 'success')
                    break
    else:
        if mode in action_list:
            ret = render_template('feeds.html', mode=mode,
                                    add_form=add_form,
                                    modify_form=modify_form)
        else:
            ret = redirect(url_for('data'))

    return ret

@app.route('/custom/data/manage_rules/<mode>', methods=['GET', 'POST'])
@login_required
def manage_rules(mode):
    action_list = ['MODIFY', 'ADD']

    feeds = Feed.query.filter_by(user_k=current_user.k).all()
    feeds_choices = [(a.k, a.name) for a in feeds]
    rules_choices = [(rule.k, rule.name) for inner_list in [a.rules for a in feeds] for rule in inner_list]
    add_form = AddRule()
    add_form.feed_k.choices = feeds_choices
    modify_form = ModifyRule()
    modify_form.name.choices = rules_choices

    if request.method == 'POST':
        ret = redirect(url_for('data'))
        for case in Switch(mode):
            if case('MODIFY'):
                if modify_form.validate_on_submit():
                    rule_obj = Rule.query.get(int(request.form['name']))
                    rule_obj.is_active = (('is_active' in request.form) and \
                            (request.form['is_active'] == 'y'))
                    db.session.commit()
                    flash('Rule modified!', 'success')
                    break
            if case('ADD'):
                if add_form.validate_on_submit():
                    is_active = (('is_active' in request.form) and \
                            (request.form['is_active'] == 'y'))

                    new_rule = Rule(request.form['name'],
                                    request.form['feed_k'],
                                    is_active)
                    db.session.add(new_rule)
                    db.session.commit()
                    flash('Rule added!', 'success')
                    break
    else:
        if mode in action_list:
            ret = render_template('rules.html', mode=mode,
                                    add_form=add_form,
                                    modify_form=modify_form)
        else:
            ret = redirect(url_for('data'))

    return ret

# -----------------------------------------------------------------------------

# ------------------------------------------------------------------------------
#
