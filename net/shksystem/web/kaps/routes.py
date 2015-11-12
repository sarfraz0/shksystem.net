# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import logging
# installed
from typing import Tuple, Dict, Any
from passlib.hash import sha512_crypt
from flask import Flask, render_template, request, redirect, url_for, \
    flash, jsonify, abort
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
from flask.ext.httpauth import HTTPBasicAuth
# custom
from net.shksystem.common.logic import Switch
from net.shksystem.web.kaps.models import db, User, MailServer
from net.shksystem.web.kaps.forms import LoginForm, RemoveUser, AddUser, \
    ModifyUser, AddMailServer, RemoveMailServer, ModifyMailServer

# Globals
# =============================================================================

logger = logging.getLogger(__name__)

app = Flask(__name__)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(k: int) -> Any:
    return User.query.get(int(k))

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username: str, password: str) -> bool:
    ret  = False
    user = User.query.filter_by(pseudo=username).first()
    if user is not None:
        if sha512_crypt.verify(password, user.passwhash):
            ret = True
    return ret

# Classes and Functions
# =============================================================================

def get_checkbox(key: str) -> bool:
    return (request.form.get(key, 'n') == 'y')

@app.errorhandler(401)
def unauthorized(error: int) -> Tuple[str, int]:
    return render_template('401.html'), 401

# Routes
# =============================================================================

### Default

@app.route('/', methods=['GET', 'POST'])
def login() -> Tuple[str, int]:
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
def manage_users(mode: str) -> Tuple[str, int]:
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
                        mod.is_manager = get_checkbox('is_manager')
                        db.session.commit()
                        flash('User modified!', 'success')
                        break
                if case('ADD'):
                    if add_form.validate_on_submit():
                        db.session.add(
                            User(
                                request.form['pseudo'],
                                request.form['password'],
                                get_checkbox('is_admin'),
                                get_checkbox('is_manager')
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
def manage_mail_servers(mode: str) -> Tuple[str, int]:
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

@app.route('/api/ajax/get_mail_server/<int:mail_server_k>', methods=['GET'])
@login_required
def get_mail_server(mail_server_k: int) -> str:
    ret = {} # type: Dict[str, Any]
    if current_user.is_admin:
        r = MailServer.query.filter_by(k=mail_server_k).first()
        if r is not None:
            ret = r.to_dict()
    else:
        abort(401)
    return jsonify(ret)

@app.route('/api/ajax/get_user/<int:user_k>', methods=['GET'])
@login_required
def get_user(user_k: int) -> str:
    ret = {} # type: Dict[str, Any]
    logger.info('User logged')
    if current_user.is_admin:
        logger.info('And a admin. Boring')
        r = User.query.filter_by(k=user_k).first()
        if r is not None:
            ret = r.to_dict()
    else:
        logger.info('at last we show the boobs.')
        abort(401)
    return jsonify(ret)

### Custom

# -----------------------------------------------------------------------------
#
