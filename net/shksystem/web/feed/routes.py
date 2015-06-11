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
# installed
from passlib.hash import sha512_crypt
from flask import Flask, render_template, request, redirect, url_for, \
    session, flash
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
# custom
from net.shksystem.common.logic import Switch
from net.shksystem.web.feed.models import db, User, Feed, Rule, DLLed
from net.shksystem.web.feed.forms import LoginForm, RemoveUser, AddUser, \
    ModifyUser

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

    choices = [(a.k, a.name) for a in Feed.query.all()]
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


                    if 'password' in request.form:
                        fuser_obj.passwhash = sha512_crypt \
                                .encrypt(request.form['password'])
                    user_obj.is_admin = (('is_admin' in request.form) and \
                            (request.form['is_admin'] == 'y'))
                    db.session.commit()
                    flash('Feed modified!', 'success')
                    break
            if case('ADD'):
                if add_form.validate_on_submit():
                    isadm = (('is_admin' in request.form) and \
                            (request.form['is_admin'] == 'y'))
                    new_feed = Feed(request.form['name'],
                                    request.form['regex'],
                                    request.form['strike_url'],
                                    request.form['kickass_url'],
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


















# -----------------------------------------------------------------------------

# ------------------------------------------------------------------------------
#
