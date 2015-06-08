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
from flask import Flask, render_template, request, redirect, url_for, session, \
    flash
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
# custom
from net.shksystem.common.logic import Switch
from net.shksystem.web.feed.models import db, User, Feed, Rule, DLLed
from net.shksystem.web.feed.forms import LoginForm

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
        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    db.session.delete(User.query.get(int(request.form['pseudo'])))
                    db.session.commit()
                    break
                if case('MODIFY'):
                    user_obj = User.query.get(int(request.form['pseudo']))
                    user_obj.password = sha512_crypt.encrypt(request.form['password'])
                    user_obj.is_admin = ('is_admin' in request.form)
                    db.session.commit()
                    break
                if case('ADD'):
                    isadm = ('is_admin' in request.form)
                    new_user = User(request.form['pseudo'], request.form['password'], isadm)
                    db.session.add(new_user)
                    db.session.commit()
                    break
        else:
            if mode in action_list:
                ret = render_template('users.html', mode=mode, users=User.query.all())
            else:
                ret = redirect(url_for('admin'))
    else:
        ret = redirect(url_for('index'))
    return ret


### Feed
# -----------------------------------------------------------------------------

## Feed views

@app.route('/view/feed/add', methods=['GET', 'POST'])
def add_feed_form():
    pass

@app.route('/view/feed/delete', methods=['GET', 'POST'])
def delete_feed_form():
    pass

## Feed API

@app.route('/api/feed', methods=['GET'])
def get_feeds():
    """ Process all feed to get new torrents and returns torrents added """
    pass

@app.route('/api/feed/<feed_name>', methods=['GET'])
def get_feed(feed_name):
    """ Process given feed to get new torrents and returns torrents added"""
    pass

@app.route('/api/feed', methods=['POST'])
def add_feed():
    """ Add a new feed """
    pass

@app.route('/api/feed/<feed_name>', methods=['DELETE'])
def delete_feed(feed_name):
    """ Delete given feed """
    pass

# -----------------------------------------------------------------------------

### Rule
# -----------------------------------------------------------------------------

## Rule views

@app.route('/view/rule/add', methods=['GET', 'POST'])
def add_rule_form():
    pass

@app.route('/view/rule/delete', methods=['GET', 'POST'])
def delete_rule_form():
    pass

## Rule API

@app.route('/api/rule', methods=['GET'])
def get_rules():
    """ Process all rule to get new torrents and returns torrents added """
    pass

@app.route('/api/rule/<rule_name>', methods=['GET'])
def get_rule(rule_name):
    """ Process given rule to get new torrents and returns torrents added"""
    pass

@app.route('/api/rule', methods=['POST'])
def add_rule():
    """ Add a new rule """
    pass

@app.route('/api/rule/<rule_name>', methods=['DELETE'])
def delete_rule(rule_name):
    """ Delete given rule """
    pass

# -----------------------------------------------------------------------------

# ------------------------------------------------------------------------------
#
