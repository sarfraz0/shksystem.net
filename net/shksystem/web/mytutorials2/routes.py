# -*- coding: utf-8 -*-

""""
    OBJET            : Flask routes
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 03.06.2015
    LICENSE          : GPL-3
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

# standard
import logging
# installed
from net.shksystem.common.logic import Switch
from flask import Flask, render_template, request, redirect, url_for, session, \
    flash
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
from flaskext.csrf import csrf
# custom
from net.shksystem.web.accounting.models import db, User, MailSpool

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# FLASK INIT
# -------------------------------------------------------------------------
app = Flask(__name__)

# FLASK CSRF
# -------------------------------------------------------------------------
csrf(app)

# FLASK ALCHEMY
# -------------------------------------------------------------------------
db.init_app(app)

# -- FLASK-LOGIN
# -------------------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(nudoss):
    return User.query.get(int(nudoss))

# ------------------------------------------------------------------------------
# Classes and Functions
# ------------------------------------------------------------------------------
# NONE
# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

login_manager.login_view = 'login'


@app.route('/', methods=['GET', 'POST'])
def login():
    ret = render_template('login.html')
    if request.method == 'POST':
        logger.info('User authentification.')
        pseudo = request.form['pseudo']
        passw = request.form['password']
        user = User.query.filter_by(pseudo=pseudo).first()
        if user is not None:
            logger.info('User exists.')
            if user.is_active():
                logger.info('And is valid.')
                if user.verify_password(passw):
                    login_user(user)
                    user.update_connection_infos()
                    flash('Login sucess, welcome {0}' \
                          .format(current_user.pseudo,), 'success')
                    ret = redirect(url_for('index'))
            else:
                logger.info('But is not valid')
                ret = redirect(url_for('validate', mode='VALID',
                                       pseudo=user.pseudo))
    return ret

@app.route('/register', methods=['POST'])
def register():
    ret = redirect(url_for('login'))
    logger.info('Registering new user.')

    pseudo = request.form['pseudo']
    passw1 = request.form['passw1']
    passw2 = request.form['passw2']
    email  = request.form['email']

    user = User.query.filter_by(pseudo=pseudo).first()
    if user is None:
        logger.info('User does not exist, creating it.')
        if passw1 == passw2:
            logger.debug('Creating new user...')
            newusr = User(pseudo, passw1, email)
            newusr.set_optionnals(request.form)
            newusr.send_token()
            db.session.add(newusr)
            db.session.commit()
            ret = redirect(url_for('validate', mode='VALID',
                           pseudo=newuser.pseudo))
        else:
            msg = 'Passwords do not match.'
            logger.info(msg)
            flash(msg, 'error')
    elif not user.is_active():
        logger.info('User does exists but needs validation.')
        ret = redirect(url_for('validate', mode='VALID', pseudo=user.pseudo))
    else:
        msg = 'User already exist.'
        logger.info(msg)
        flash(msg, 'error')

    return ret

@app.route('/register/validate/<mode>/<pseudo>', methods=['GET', 'POST'])
def validate(mode, pseudo):
    ret = render_template('validate.html', mode=mode, pseudo=pseudo)
    logger.info('Action %s for id %s.', mode, pseudo)
    user = User.query.filter_by(pseudo=pseudo).first()
    if request.method == 'POST':
        for case in Switch(mode):
            if case('VALID'):
                logger.info('Validating user %s.', user.pseudo)
                stored_token = session['NEW_TOKEN'] if 'NEW_TOKEN' in session else user._token
                submited_token = request.form['token_entry']
                if stored_token == submited_token:
                    logger.info('Token matches.')
                    user._active = True
                    user.update_connection_infos()
                    db.session.commit()
                    login_user(user)
                    ret = redirect(url_for('index'))
            if case('REGEN'):
                logger.info('Regeneration of token for user %s.', user.pseudo)
                user.refresh_token()
                user.send_token()
                session['NEW_TOKEN'] = user.token
                db.session.commit()
                redirect(url_for('validate', mode='VALID', pseudo_id=pseudo_id))
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
    if current_user.is_admin():
        ret = render_template('admin.html')
    else:
        ret = redirect(url_for('index'))
    return ret

@app.route('/admin/manage_users/<mode>', methods=['GET', 'POST'])
@login_required
def manage_users(mode):
    action_list = ['REMOVE', 'MODIFY', 'ADD']
    if current_user.is_admin():
        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    db.session.delete(User.query.get(int(request.form['pseudo'])))
                    db.session.commit()
                    break
                if case('MODIFY'):
                    user_obj = User.query.get(int(request.form['pseudo']))
                    user_obj.passw = sha512_crypt.encrypt(request.form['password'])
                    user_obj.admin = ('is_admin' in request.form)
                    db.session.commit()
                    break
                if case('ADD'):
                    isadm = ('is_admin' in request.form)
                    newusr = User(request.form['pseudo'], request.form['password'], isadm)
                    db.session.add(newusr)
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


@app.route('/admin/manage_mail_spool/<mode>', methods=['GET', 'POST'])
@login_required
def manage_mail_spool(mode):
    action_list = ['REMOVE', 'MODIFY', 'ADD']
    if current_user.is_admin:
        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    db.session.delete(MailSpool.query.filter_by(nudoss=request.form['mail_spool']).first())
                    db.session.commit()
                    break
                if case('MODIFY'):
                    spool_obj = MailSpool.query.filter_by(nudoss=request.form['mail_spool']).first()
                    spool_obj.mail_server = request.form['mail_server']
                    spool_obj.mail_port = int(request.form['mail_port'])
                    spool_obj.mail_username = request.form['mail_username']
                    spool_obj.mail_password = request.form['mail_password']
                    spool_obj.full_sender = request.form['full_sender']
                    db.session.commit()
                    break
                if case('ADD'):
                    mserv = request.form['mail_server']
                    muser = request.form['mail_username']
                    mport = int(request.form['mail_port'])
                    mpassword = request.form['mail_password']
                    mfull_sender = request.form['full_sender']
                    m = MailSpool.query.filter_by(mail_server=mserv).filter_by(mail_username=muser).first()
                    if m is None:
                        new_spool           = MailSpool(mserv, muser, mpassword, mfull_sender)
                        new_spool.mail_port = mport
                        db.session.add(new_spool)
                        db.session.commit()

                    break
        else:
            if mode in action_list:
                ret = render_template('mail_spool.html', mode=mode, spools=MailSpool.query.all())
            else:
                ret = redirect(url_for('admin'))
    else:
        ret = redirect(url_for('index'))
    return ret

# ------------------------------------------------------------------------------
#
