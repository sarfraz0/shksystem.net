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
import random
import json
# installed
from pandas import DataFrame
from passlib.hash import sha512_crypt
from flask import Flask, render_template, request, redirect, url_for, \
    session, flash
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
# custom
from net.shksystem.common.logic import Switch
from net.shksystem.common.send_mail import SendMail
from net.shksystem.scripts.feed import ReleaseFrame
from net.shksystem.web.feed.models import db, User, Feed, Rule, DLLed, \
    MailServer
from net.shksystem.web.feed.forms import LoginForm, RemoveUser, AddUser, \
    ModifyUser, AddFeed, ModifyFeed, AddRule, ModifyRule, AddMailServer, \
    RemoveMailServer

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

logger = logging.getLogger(__name__)

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
    logger.info('Processing feed %s', feed_name)
    feed = Feed.query.filter_by(name=feed_name).first()
    logger.info('%s', feed.to_json())
    if (feed is not None) and feed.is_active:
        logger.info('Relative data found. Creating release frame...')
        f = ReleaseFrame()
        d = f.get(feed.kickass_url, feed.strike_url, feed.regex,
                  feed.has_episodes, feed.has_seasons)
        logger.info('Feed retrieved.')
        logger.info('%s', DataFrame.to_string(d))
        ml = random.choice(MailServer.query.all())
        mlj = ml.to_dict()
        mlj['SUBJECT'] = 'New download in progress...'
        logger.info('Mail infos init... Done.')
        logger.info('%s', json.dumps(mlj))
        for rule in feed.rules:
            if rule.is_active:
                logger.info('Rule %s is active. Processing...', rule.name)
                f.get_rule(d, rule.name, mlj)
    return '{\'responseStatus\': 200, \'responseBody\': \'\'}'

@app.route('/api/v1/run/feeds', methods=['GET'])
def run_feeds():
    feeds = Feed.query.all()
    for feed in feeds:
        if (feed is not None) and feed.is_active:
            f = ReleaseFrame()
            d = f.get(feed.kickass_uri, feed.strike_uri, feed.regex,
                      feed.has_episodes, feed.has_seasons)
            ml = random.choice(MailServer.query.all())
            mj = { 'HOST'   : ml.server
                 , 'PORT'   : ml.port
                 , 'USER'   : ml.username
                 , 'FROM'   : ml.sender
                 , 'TO'     : ml.sender
                 , 'SUBJECT': 'New download in progress...' }
            for rule in feed.rules:
                if rule.is_active:
                    f.get_rule(d, rule.name, mj)

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
            if case('ADD'):
                if add_form.validate_on_submit():
                    is_active = (('is_active' in request.form) and \
                            (request.form['is_active'] == 'y'))
                    has_episodes = (('has_episodes' in request.form) and \
                            (request.form['has_episodes'] == 'y'))
                    has_seasons = (('has_seasons' in request.form) and \
                            (request.form['has_seasons'] == 'y'))
                    dest = request.form['dest'] if \
                            'dest' in request.form else ''
                    new_feed = Feed(request.form['name'],
                                    request.form['category'],
                                    request.form['regex'],
                                    request.form['strike_url'],
                                    request.form['kickass_url'],
                                    current_user.k,
                                    is_active, has_episodes, has_seasons,
                                    dest)
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
