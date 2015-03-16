# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Flask routes
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 25.12.2014
#@(#) LICENSE          : GPL-3
#@(#)----------------------------------------------------------------------

#==========================================================================
#
# WARNINGS
# NONE
#
#==========================================================================

#==========================================================================
# Imports
#==========================================================================

# Standard
import os
import sys
import logging
# Environment defined
from net.shksystem.common.logic            import Switch
from passlib.hash                          import sha512_crypt
from flask                                 import Flask, render_template, request, redirect, url_for, session
from flask.ext.login                       import LoginManager, login_required, login_user, logout_user, current_user
# User defined
from net.shksystem.flask.accounting.models import db, User, Persona, Temp, MailSpool

#==========================================================================
# Environment/Parameters/Static variables
#==========================================================================

logger = logging.getLogger(__name__)

# -- FLASK INIT
# -------------------------------------------------------------------------
app = Flask(__name__)

# -- FLASK ALCHEMY
# -------------------------------------------------------------------------
db.init_app(app)

# -- FLASK-LOGIN
# -------------------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(nudoss):
    return User.query.get(int(nudoss))

#==========================================================================
# Classes/Functions
#==========================================================================
# NONE
#==========================================================================
# Routes
#==========================================================================

login_manager.login_view = 'login'
@app.route('/', methods=['GET', 'POST'])
def login():
    ret = render_template('login.html')
    if request.method == 'POST':
        pseudo        = request.form['pseudo']
        passwd        = request.form['password']
        user          = User.query.filter_by(pseudo=pseudo).first()
        if user is not None:
            if user.persona.valid:
                if sha512_crypt.verify(passwd, user.passwhash):
                    login_user(user)
                    ret = redirect(url_for('index'))
                else:
                    ret = redirect(url_for('validate', mode='VALID', pseudo_id=user.nudoss))
    return ret

@app.route('/register', methods=['POST'])
def register():
    logger.debug('100101 - BEGIN')
    logger.info('Registering new user.')

    pseudo   = request.form['pseudo']
    passw1   = request.form['passw1']
    passw2   = request.form['passw1']
    email    = request.form['email']
    logger.debug('100101 - 1 - Form for new user is pseudo ({0}), passw1 ({1}), passw2 ({2}) and email ({3}).'.format(pseudo, passw1, passw2, email))

    user     = User.query.filter_by(pseudo=pseudo).first()
    if user is None:
        logger.info('User does not exist, creating it.')
        if passw1 == passw2:
            logger.debug('100101 - 2 - Creating new user.')
            newusr = User(pseudo, passw1, False)
            db.session.add(newusr)
            db.session.flush()
            newusr_id      = User.query.filter_by(pseudo=pseudo).first().nudoss
            logger.debug('100101 - 3 - Flushing new user and getting back its id : {0}'.format(newusr_id,))
            newusr_persona = Persona(newusr_id, email)
            newusr_persona.set_optionnals(request.form)
            newusr_temp = Temp(newusr_id)
            newusr_temp.validation_token = newusr_persona.gen_validation_request()
            db.session.add(newusr_persona)
            db.session.add(newusr_temp)
            db.session.commit()
            ret = redirect(url_for('validate', mode='NULL', pseudo_id=0))
    elif not Persona.query.filter_by(nudoss=user.nudoss).first().validper:
        logger.info('User does exist but needs validation.')
        ret = redirect(url_for('validate', mode='NULL', pseudo_id=0))
    else:
        logger.info('Welcome {0}.'.format(user.pseudo))
        ret = redirect(url_for('index'))

    logger.debug('100101 - END')
    return ret

@app.route('/register/validate/<mode>/<pseudo_id>', methods=['GET', 'POST'])
def validate(mode, pseudo_id):
    logger.debug('100100 - BEGIN')
    logger.info('Token handling process for user. Action {0} for id {1}.'.format(mode, pseudo_id))
    logger.debug('100100 - 1 - Argument are mode ({0}) and pseudo_id ({1}).'.format(mode, pseudo_id))
    user = User.query.get(int(pseudo_id))
    logger.debug('100100 - 2 - User\'s pseudo is {0}.'.format(user.pseudo))
    if request.method == 'POST':
        for case in Switch(mode):
            if case('VALID'):
                logger.info('Validating user {0}.'.format(user.pseudo,))
                temporary_stored_token = user.temp.validation_token
                logger.debug('100100 - 3 - Stored token is {0}.'.format(temporary_stored_token))
                submited_token         = request.form['token_entry']
                logger.debug('100100 - 4 - Submited token is {0}.'format(submited_token))
                if temporary_stored_token == submited_token:
                    logger.debug('100100 - 5 - Token matches.')
                    user.persona.valid = True
                    db.session.commit()
            if case('REGEN'):
                logger.info('Regeneraiton of token for user {0}.'.format(user.pseudo,))
                new_token = user.persona.gen_validation_request()
                logger.debug('100100 - 6 - Regenerating user token')
                user.temp.validation_token = new_token
                db.session.commit()
    else:
        logger.info('Request is not post, rendering form.')
        ret = render_template('validate.html', mode='NULL', pseudo_id=0)
    logger.debug('100100 - END')
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
        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    db.session.delete(User.query.get(int(request.form['pseudo'])))
                    db.session.commit()
                    break
                if case('MODIFY'):
                    user_obj          = User.query.get(int(request.form['pseudo']))
                    user_obj.password = sha512_crypt.encrypt(request.form['password'])
                    user_obj.is_admin = ('is_admin' in request.form)
                    db.session.commit()
                    break
                if case('ADD'):
                    isadm    = ('is_admin' in request.form)
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
                    spool_obj               = MailSpool.query.filter_by(nudoss=request.form['mail_spool']).first()
                    spool_obj.mail_server   =     request.form['mail_server']
                    spool_obj.mail_port     = int(request.form['mail_port'])
                    spool_obj.mail_username =     request.form['mail_username']
                    spool_obj.mail_password =     request.form['mail_password']
                    spool_obj.full_sender   =     request.form['full_sender']
                    db.session.commit()
                    break
                if case('ADD'):
                    mserv        =     request.form['mail_server']
                    muser        =     request.form['mail_username']
                    mport        = int(request.form['mail_port'])
                    mpassword    =     request.form['mail_password']
                    mfull_sender =     request.form['full_sender']
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

#==========================================================================
# End sequence
#==========================================================================
#0
