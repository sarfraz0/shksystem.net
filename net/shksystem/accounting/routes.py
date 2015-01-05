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
import os, sys
import logging
# Environment defined
from net.shksystem.common.logic import Switch
from passlib.hash               import sha512_crypt
from flask                      import Flask, render_template, request, redirect, url_for, session, flash
from flask.ext.login            import LoginManager, login_required, login_user, logout_user, current_user
from sqlalchemy                 import and_
# User defined
from models                     import db, User, Environment, UserConf
from processing                 import deployUtil, deployLiv

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
        pseudo = request.form['pseudo']
        passwd = request.form['password']
        user   = User.query.filter_by(pseudo=pseudo).first()
        if user is not None:
            if sha512_crypt.verify(passwd, user.passwhash):
                login_user(user)
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
    if current_user.isAdmin:
        ret = render_template('admin.html')
    else:
        ret = redirect(url_for('index'))
    return ret

@app.route('/admin/manage_users/<mode>', methods=['GET', 'POST'])
@login_required
def manage_users(mode):
    actionList = ['REMOVE', 'MODIFY', 'ADD']
    if current_user.isAdmin:
        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    db.session.delete(User.query.get(int(request.form['pseudo'])))
                    db.session.commit()
                    break
                if case('MODIFY'):
                    userObj  = User.query.get(int(request.form['pseudo']))
                    userObj.password = sha512_crypt.encrypt(request.form['password'])
                    userObj.isAdmin  = ('isAdmin' in request.form)
                    db.session.commit()
                    break
                if case('ADD'):
                    isadm   = ('isAdmin' in request.form)
                    newUser = User(request.form['pseudo'], request.form['password'], isadm)
                    db.session.add(newUser)
                    db.session.commit()
                    break
        else:
            if mode in actionList:
                ret = render_template('users.html', mode=mode, users=User.query.all())
            else:
                ret = redirect(url_for('admin'))
    else:
        ret = redirect(url_for('index'))
    return ret

@app.route('/admin/manage_environements/<mode>', methods=['GET', 'POST'])
@login_required
def manage_environments(mode):
    actionList = ['REMOVE', 'MODIFY', 'ADD']
    if current_user.isAdmin:
        if request.method == 'POST':
            ret = redirect(url_for('admin'))
            for case in Switch(mode):
                if case('REMOVE'):
                    db.session.delete(Environment.query.get(int(request.form['inv'])))
                    db.session.commit()
                    break
                if case('MODIFY'):
                    envObj  = Environment.query.get(int(request.form['inv']))
                    envObj.envName   = request.form['envName'] if 'envName' in request.form else ''
                    envObj.applName  = request.form['applName']
                    envObj.hostname  = request.form['hostname']
                    envObj.envGroup  = request.form['envGroup']
                    envObj.component = request.form['component']
                    envObj.userName  = request.form['userName']
                    envObj.userGroup = request.form['userGroup']
                    db.session.commit()
                    break
                if case('ADD'):
                    envName = request.form['envName'] if 'envName' in request.form else ''
                    newEnv  = Environment(envName
                                          , request.form['applName']
                                          , request.form['hostname']
                                          , request.form['envGroup']
                                          , request.form['component']
                                          , request.form['userName']
                                          , request.form['userGroup'])
                    db.session.add(newEnv)
                    db.session.commit()
                    break
        else:
            if mode in actionList:
                ret = render_template('environments.html', mode=mode, environments=Environment.query.all())
            else:
                ret = redirect(url_for('admin'))
    else:
        ret = redirect(url_for('index'))
    return ret

@app.route('/livraison', methods=['POST'])
@login_required
def livraison():
    try:
        logger.info('Getting current user configuration')
        userConf = UserConf.query.get(current_user.nudoss)
        app.logger('probleme denv')
        envsU = Environment.query.filter_by(userGroup=request.form['inv']
                                            , component=request.form['COM']).all()
        envsL = Environment.query.filter_by(userGroup=request.form['inv']
                                            , component=request.form['LIV']).all()

        for case in Switch(request.form['comp']):
            if case('ALL'):
                deployUtil(envsU, userConf)
                deployLiv(envsL, userConf)
                break
            if case('utilitaires'):
                deployUtil(envsU, userConf)
                break
            if case('Livraison'):
                deployLiv(envsL, userConf)
                break
        logger.info('Deployment successful')
        logger.info(compteRendu)
    except:
        logger.error(sys.exc_info()[0])
    ret = redirect(url_for('index'))
    return ret

@app.route('/jira/<action>', methods=['POST'])
@login_required
def jira(action):
    ret = render_template('jira.html', action=None)
    return ret

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    ret = redirect(url_for('index'))
    if request.method == 'POST':
        currentConf = UserConf.query.get(current_user.nudoss)
        if currentConf is not None:
            db.session.delete(currentConf)
        pprint(request.form)
        newConf = UserConf(current_user.nudoss
                           , request.form['javaUtilsUrl']
                           , request.form['svnUser']
                           , request.form['svnPasswd']
                           , request.form['hopUser']
                           , request.form['hopPasswd'])
        db.session.add(newConf)
        db.session.commit()
    else:
        ret = render_template('settings.html', conf=UserConf.query.get(current_user.nudoss))
    return ret

#==========================================================================
# End sequence
#==========================================================================
#0
