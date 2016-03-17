# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
import random
# anaconda
from flask import Flask, render_template, request, session, redirect, url_for, \
    flash, jsonify, abort
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
# installed
from passlib.hash import sha512_crypt
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
# custom
from shk.common.logic import Switch
from shk.db.budget import Base, User, MailServer, Status
from shk.web.budget.frt.forms import LoginForm, RemoveUser, AddUser, \
        ModifyUser, AddMailServer, RemoveMailServer, ModifyMailServer

## Globals
# =============================================================================

logger     = logging.getLogger(__name__)
app        = Flask(__name__)
db_session = scoped_session(sessionmaker(
                               autocommit=False,
                               autoflush=False,
                               bind=create_engine(
                                       os.environ['BUDGET_DATABASE_URI'],
                                       convert_unicode=True
                                    )
                            ))

Base.query = db_session.query_property()
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(cid):
    return db_session.query(User).get(int(cid))

## Functions and Classes
# =============================================================================

def get_checkbox(key):
    return (request.form.get(key, 'n') == 'y')

@app.errorhandler(401)
def unauthorized(error):
    return render_template('401.html'), 401

# Default routes
#########################################

@app.route('/', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    ret = render_template('login.html', login_form=login_form)
    if request.method == 'POST' and login_form.validate_on_submit():
        logger.info('User authentification.')
        pseudo = request.form['pseudo']
        passwd = request.form['password']
        user   = db_session.query(User).filter_by(pseudo=pseudo).first()
        if user is not None:
            logger.info('User exists.')
            if sha512_crypt.verify(passwd, user.passwhash):
                login_user(user)
                session['is_admin']   = any([x.is_admin() for x in user.roles])
                session['is_manager'] = any([x.is_manager() for x in user.roles])
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
    session['is_admin']   = False
    session['is_manager'] = False
    ret = redirect(url_for('login'))
    return ret

@app.route('/admin', methods=['GET'])
@login_required
def admin():
    if session['is_admin']:
        ret = render_template('admin.html')
    else:
        ret = redirect(url_for('index'))
    return ret

@app.route('/admin/manage_users/<mode>', methods=['GET', 'POST'])
@login_required
def manage_users(mode):
    action_list = ['REMOVE', 'MODIFY', 'ADD']
    if session['is_admin']:

        pseudo_choices = [(a.cid, a.pseudo) for a in db_session.query(User).all()]
        status_choices = [(a.cid, a.name) for a in db_session.query(Status).all()]
        remove_form    = RemoveUser()
        add_form       = AddUser()
        modify_form    = ModifyUser()
        for form in [remove_form, modify_form]:
            form.pseudo.choices = pseudo_choices
        for form in [add_form, modify_form]:
            form.status.choices = status_choices

        if request.method == 'POST':
            ret = redirect(url_for('admin'))

            for case in Switch(mode):
                if case('REMOVE'):
                    if remove_form.validate_on_submit():
                        pseudo = int(request.form['pseudo'])
                        db_session.delete(db_session.query(User).get(pseudo))
                        db_session.commit()
                        flash('User deleted!', 'success')
                        break
                if case('MODIFY'):
                    if modify_form.validate_on_submit():
                        mod = db_session.query(User).get(int(request.form['pseudo']))
                        if 'email' in request.form:
                            mod.email = request.form['email']
                        if 'password' in request.form:
                            mod.passwhash = sha512_crypt.encrypt(
                                               request.form['password'])
                        mod.status_cid = request.form['status']
                        db_session.commit()
                        flash('User modified!', 'success')
                        break
                if case('ADD'):
                    if add_form.validate_on_submit():
                        new_user = User(
                                      request.form['pseudo'],
                                      request.form['password'],
                                      request.form['status']
                                   )
                        if 'email' in request.form:
                            new_user.email = request.form['email']
                        db_session.add(new_user)
                        db_session.commit()
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
    if session['is_admin']:

        add_form    = AddMailServer()
        remove_form = RemoveMailServer()
        modify_form = ModifyMailServer()
        choices     = []
        for a in db_session.query(MailServer).all():
            choices.append((a.cid, '%s - %s' % (a.username, a.hostname)))
        for form in [remove_form, modify_form]:
            form.server.choices = choices

        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    if remove_form.validate_on_submit():
                        server = request.form['server']
                        db_session.delete(db_session.query(MailServer).get(int(server)))
                        db_session.session.commit()
                        break
                if case('ADD'):
                    if add_form.validate_on_submit():
                        hostname = request.form['hostname']
                        username = request.form['username']
                        if db_session.query(MailServer) \
                                .filter_by(hostname=hostname) \
                                .filter_by(username=username).first() is None:
                            new = MailServer(
                                     hostname,
                                     username,
                                     request.form['password'],
                                     request.form['sender']
                                  )
                            new.port = int(request.form['port'])
                            db_session.add(new)
                            db_session.commit()
                    break
                if case('MODIFY'):
                    if modify_form.validate_on_submit():
                        server = request.form['server']
                        mod = db_session.query(MailServer).get(int(server))
                        if 'hostname' in request.form:
                            mod.hostname = request.form['hostname']
                        if 'username' in request.form:
                            mod.username = request.form['username']
                        if 'port' in request.form:
                            mod.port = int(request.form['port'])
                        if 'password' in request.form:
                            mod.password = sha512_crypt.encrypt(
                                              request.form['password'])
                        if 'sender' in request.form:
                            mod.sender = request.form['sender']
                        db_session.commit()
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

# API
#########################################

@app.route('/api/ajax/get_mail_server/<int:mail_server_cid>', methods=['GET'])
@login_required
def get_mail_server(mail_server_cid):
    ret = {}
    if session['is_admin']:
        r = db_session.query(User).filter_by(cid=int(mail_server_cid)).first()
        if r is not None:
            ret = r.to_dict()
    else:
        abort(401)
    return jsonify(ret)

@app.route('/api/ajax/get_user/<int:user_cid>', methods=['GET'])
@login_required
def get_user(user_cid):
    ret = {}
    logger.info('User logged')
    if session['is_admin']:
        logger.info('And a admin. Boring')
        r = db_session.query(User).filter_by(cid=int(user_cid)).first()
        if r is not None:
            ret = r.to_dict()
    else:
        logger.info('at last we show the boobs.')
        abort(401)
    return jsonify(ret)

# Custom routes
#########################################

#
