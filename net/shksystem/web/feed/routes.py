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
import logging
import random
# installed
from passlib.hash import sha512_crypt
from flask import Flask, render_template, request, redirect, url_for, \
    flash, jsonify, abort
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
from flask.ext.httpauth import HTTPBasicAuth
import transmissionrpc
# custom
from net.shksystem.common.logic import Switch
# from net.shksystem.common.send_mail import SendMail
from net.shksystem.business.feed import ReleaseFrame
from net.shksystem.web.feed.models import db, User, Feed, Rule, MailServer
from net.shksystem.web.feed.forms import LoginForm, RemoveUser, AddUser, \
    ModifyUser, AddFeed, ModifyFeed, AddRule, ModifyRule, AddMailServer, \
    RemoveMailServer, RemoveRule, RemoveFeed, ModifyMailServer

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

logger = logging.getLogger(__name__)

app = Flask(__name__)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(k):
    return User.query.get(int(k))

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    ret  = False
    user = User.query.filter_by(pseudo=username).first()
    if user is not None:
        if sha512_crypt.verify(password, user.passwhash):
            ret = True
    return ret

# ------------------------------------------------------------------------------
# Classes and Functions
# ------------------------------------------------------------------------------

def get_checkbox(key):
    return (request.form.get(key, 'n') == 'y')


@app.errorhandler(401)
def unauthorized(error):
    return render_template('401.html'), 401

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
        user   = User.query.filter_by(pseudo=pseudo).first()
        if user is not None:
            logger.info('User exists.')
            if sha512_crypt.verify(passwd, user.passwhash):
                login_user(user)
                flash(
                    'Login sucess, welcome %s' % (current_user.pseudo,),
                    'success'
                )
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
    if current_user.is_admin:
        ret = render_template('admin.html')
    else:
        ret = redirect(url_for('index'))
    return ret

@app.route('/admin/manage_users/<mode>', methods=['GET', 'POST'])
@login_required
def manage_users(mode):
    action_list = ['REMOVE', 'MODIFY', 'ADD']
    if current_user.is_admin:

        choices     = [(a.k, a.pseudo) for a in User.query.all()]
        remove_form = RemoveUser()
        add_form    = AddUser()
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
                        mod = User.query.get(int(request.form['pseudo']))
                        if 'password' in request.form:
                            mod.passwhash = sha512_crypt.encrypt(
                                request.form['password']
                            )
                        mod.is_admin = get_checkbox('is_admin')
                        db.session.commit()
                        flash('User modified!', 'success')
                        break
                if case('ADD'):
                    if add_form.validate_on_submit():
                        db.session.add(
                            User(
                                request.form['pseudo'],
                                request.form['password'],
                                get_checkbox('is_admin')
                            )
                        )
                        db.session.commit()
                        flash('User added!', 'success')
                        break
        else:
            if mode in action_list:
                ret = render_template(
                    'users.html',
                    mode=mode,
                    add_form=add_form,
                    modify_form=modify_form,
                    remove_form=remove_form
                )
            else:
                ret = redirect(url_for('admin'))
    else:
        ret = redirect(url_for('index'))

    return ret

@app.route('/admin/manage_mail_servers/<mode>', methods=['GET', 'POST'])
@login_required
def manage_mail_servers(mode):
    action_list = ['REMOVE', 'ADD', 'MODIFY']
    if current_user.is_admin:

        add_form    = AddMailServer()
        remove_form = RemoveMailServer()
        modify_form = ModifyMailServer()
        choices = []
        for a in MailServer.query.all():
            choices.append((a.k, '%s - %s' % (a.username, a.hostname)))
        for form in [remove_form, modify_form]:
            form.server.choices = choices

        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    if remove_form.validate_on_submit():
                        db.session.delete(
                            MailServer.query.get(int(request.form['server']))
                        )
                        db.session.commit()
                        break
                if case('ADD'):
                    if add_form.validate_on_submit():
                        hostname   = request.form['hostname']
                        username = request.form['username']
                        if MailServer.query \
                                .filter_by(hostname=hostname) \
                                .filter_by(username=username).first() is None:
                            new = MailServer(
                                hostname,
                                username,
                                request.form['password'],
                                request.form['sender']
                            )
                            new.port = int(request.form['port'])
                            db.session.add(new)
                            db.session.commit()
                    break
                if case('MODIFY'):
                    if modify_form.validate_on_submit():
                        mod = MailServer.query.get(int(request.form['server']))
                        if 'hostname' in mod:
                            mod.hostname = request.form['hostname']
                        if 'username' in mod:
                            mod.username = request.form['username']
                        if 'port' in mod:
                            mod.port = int(request.form['port'])
                        if 'password' in mod:
                            mod.password = sha512_crypt.encrypt
                            (
                                request.form['password']
                            )
                        if 'sender' in request.form:
                            mod.sender = request.form['sender']
                        db.session.commit()
                        flash('Server modified!', 'success')
                        break
        else:
            if mode in action_list:
               ret = render_template(
                    'mail_servers.html',
                    mode=mode,
                    add_form=add_form,
                    remove_form=remove_form,
                    modify_form=modify_form
                )
            else:
                ret = redirect(url_for('admin'))
    else:
        ret = redirect(url_for('index'))
    return ret


### API
# -----------------------------------------------------------------------------

@app.route('/api/run/feed/<feed_name>', methods=['GET'])
@auth.login_required
def run_feed(feed_name):
    added = []
    logger.info('Processing feed %s', feed_name)
    feed = Feed.query \
            .filter_by(name=feed_name) \
            .filter_by(user_k=user_k).first()
    if (feed is not None) and feed.is_active:
        logger.info('Relative data found. Creating release frame...')
        f = ReleaseFrame()
        d = f.get(
            feed.kickass_url,
            feed.strike_url,
            feed.regex,
            feed.has_episodes,
            feed.has_seasons
        )
        logger.info('Feed retrieved.')
        mlj = random.choice(MailServer.query.all()).to_dict()
        mlj['SUBJECT'] = 'New download in progress...'
        logger.info('Mailing info retrieved.')
        for rule in feed.rules:
            if rule.is_active:
                logger.info('Rule %s is active. Processing...', rule.name)
                ex = f.get_rule(d, rule.name, mlj)
                added.extend(ex)
    return jsonify({'status': 'success', 'data': {'added': added}})

@app.route('/api/run/feeds', methods=['GET'])
@auth.login_required
def run_feeds():
    added = []
    feeds = Feed.query.all()
    for feed in feeds:
        if (feed is not None) and feed.is_active:
            logger.info('Processing feed %s', feed.name)
            logger.info('Relative data found. Creating release frame...')
            f = ReleaseFrame()
            d = f.get(
                feed.kickass_url,
                feed.strike_url,
                feed.regex,
                feed.has_episodes,
                feed.has_seasons
            )
            logger.info('Feed retrieved.')
            mlj = random.choice(MailServer.query.all()).to_dict()
            mlj['SUBJECT'] = 'New download in progress...'
            logger.info('Mailing info retrieved.')
            for rule in feed.rules:
                if rule.is_active:
                    logger.info('Rule %s is active. Processing...', rule.name)
                    ex = f.get_rule(d, rule.name, mlj)
                    added.extend(ex)
    return jsonify({'status': 'success', 'data': {'added': added}})

@app.route('/api/ajax/get_torrents/<hst>/<int:prt>', methods=['GET'])
@login_required
def get_torrents(hst, prt):
    ret = []
    try:
        tc = transmissionrpc.Client(hst, int(prt))
        for tor in tc.get_torrents():
            tmp = {}
            tmp['status']   = tor.status
            tmp['name']     = tor.name
            tmp['progress'] = tor.progress
            ret.append(tmp)
    except:
        logger.exception('Could not fetch torrents list from transmission.')
        abort(500)

    return jsonify({'torrents': ret})

@app.route('/api/ajax/get_rule/<int:rule_k>', methods=['GET'])
@login_required
def get_rule(rule_k):
    ret = {}
    r = Rule.query.filter_by(k=int(rule_k)).first()
    if (r is not None) and (r.feed.user.k == current_user.k):
        ret = r.to_dict()
    else:
        abort(404)
    return jsonify(ret)

@app.route('/api/ajax/get_feed/<int:feed_k>', methods=['GET'])
@login_required
def get_feed(feed_k):
    ret = {}
    r = Feed.query.filter_by(k=int(feed_k)).first()
    if (r is not None) and (r.user.k == current_user.k):
        ret = r.to_dict()
    else:
        abort(404)
    return jsonify(ret)

@app.route('/api/ajax/get_mail_server/<int:mail_server_k>', methods=['GET'])
@login_required
def get_mail_server(mail_server_k):
    ret = {}
    if current_user.is_admin:
        r = MailServer.query.filter_by(k=int(mail_server_k)).first()
        if r is not None:
            ret = r.to_dict()
    else:
        abort(401)
    return jsonify(ret)

@app.route('/api/ajax/get_user/<int:user_k>', methods=['GET'])
@login_required
def get_user(user_k):
    ret = {}
    logger.info('User logged')
    if current_user.is_admin:
        logger.info('And a admin. Boring')
        r = User.query.filter_by(k=int(user_k)).first()
        if r is not None:
            ret = r.to_dict()
    else:
        logger.info('at last we show the boobs.')
        abort(401)
    return jsonify(ret)

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
    action_list = ['MODIFY', 'ADD', 'REMOVE']

    choices = []
    for a in Feed.query.filter_by(user_k=current_user.k).all():
        choices.append((a.k, a.name))
    add_form    = AddFeed()
    modify_form = ModifyFeed()
    remove_form = RemoveFeed()
    for form in [modify_form, remove_form]:
        form.name.choices = choices

    if request.method == 'POST':
        ret = redirect(url_for('data'))
        for case in Switch(mode):
            if case('MODIFY'):
                if modify_form.validate_on_submit():
                    feed_obj = Feed.query.get(int(request.form['name']))
                    if 'category' in request.form:
                        feed_obj.category = request.form['category']
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
                    feed_obj.dest = request.form['dest'] if \
                            'dest' in request.form else ''
                    db.session.commit()
                    flash('Feed modified!', 'success')
                    break
            if case('REMOVE'):
                db.session.delete
                (
                    Feed.query.filter_by(k=int(request.form['name'])).first()
                )
                db.session.commit()
                flash('Feed deleted!', 'success')
                break
            if case('ADD'):
                if add_form.validate_on_submit():
                    db.session.add(
                        Feed(
                            request.form['name'],
                            request.form['category'],
                            request.form['regex'],
                            request.form['strike_url'],
                            request.form['kickass_url'],
                            current_user.k,
                            get_checkbox('is_active'),
                            get_checkbox('has_episodes'),
                            get_checkbox('has_seasons'),
                            request.form.get('dest', '')
                        )
                    )
                    db.session.commit()
                    flash('Feed added!', 'success')
                    break
    else:
        if mode in action_list:
            ret = render_template(
                'feeds.html',
                mode=mode,
                add_form=add_form,
                modify_form=modify_form,
                remove_form=remove_form
            )
        else:
            ret = redirect(url_for('data'))

    return ret

@app.route('/custom/data/manage_rules/<mode>', methods=['GET', 'POST'])
@login_required
def manage_rules(mode):
    action_list = ['MODIFY', 'ADD', 'REMOVE']

    feeds = Feed.query.filter_by(user_k=current_user.k).all()
    feeds_choices = [(a.k, a.name) for a in feeds]
    rules_choices = [(rule.k, rule.name) for inner_list in [a.rules for a in feeds] for rule in inner_list]
    add_form = AddRule()
    add_form.feed_k.choices = feeds_choices
    modify_form = ModifyRule()
    remove_form = RemoveRule()
    for form in [modify_form, remove_form]:
        form.name.choices = rules_choices

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
            if case('REMOVE'):
                db.session.delete(Rule.query.filter_by(k=int(request.form['name'])).first())
                db.session.commit()
                flash('Rule deleted!', 'success')
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
                                    modify_form=modify_form,
                                    remove_form=remove_form)
        else:
            ret = redirect(url_for('data'))

    return ret


# -----------------------------------------------------------------------------
#
