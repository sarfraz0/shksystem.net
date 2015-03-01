# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Ordre d'arrivée et de sortie
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 25.02.2015
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

import os
import sys
import csv
import logging
import keyring
from sqlalchemy                 import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import sessionmaker
from ..common.error             import FileNotFound
from ..common.utils             import get_current_timestamp
from ..common.send_mail         import SendMail
from ..common.logic             import Switch

#==========================================================================
# Environment/Static variables
#==========================================================================

logger    = logging.getLogger(__name__)
base_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
Base      = declarative_base()

#==========================================================================
# Classes/Functions
#==========================================================================

## Data Sink

class Recipient(Base):
    __tablename__ = 'recipients'
    nudoss        = Column(Integer, primary_key=True)
    mail          = Column(String, nullable=False)

    def __init__(self, mail):
        self.mail = mail

class Server(Base):
    __tablename__ = 'servers'
    nudoss        = Column(Integer, primary_key=True)
    hostname      = Column(String, nullable=False)
    port          = Column(Integer, nullable=False)
    username      = Column(String, nullable=False)
    sender        = Column(String, nullable=False)

    def __init__(self, hostname, port, username, password, sender):
        self.hostname = hostname
        self.port     = port
        self.username = username
        keyring.set_password(hostname, username, password)
        self.sender   = sender

## Processes

def run_recipients(imperium):

    conf_dir  = os.path.abspath('../etc/{0}'.format(base_name,))
    dest_fic  = os.path.join(conf_dir, 'recipients.csv')
    serv_fic  = os.path.join(conf_dir, 'servers.csv')
    db_fic    = os.path.join(conf_dir, '{0}.db'.format(base_name,))
    engine    = create_engine('sqlite:///' + db_fic.replace('\\', '\\\\'))

    logger.info('#### Sending notification to all. ####')

    logger.info('Checking data.')
    if not os.path.isfile(db_fic):
        logger.info('Database file does not exist. Creating it.')
        if not (all(map(os.path.isfile, [dest_fic, serv_fic]))):
            logger.error('Required data files do not exists. Please create them and run again.')
            raise FileNotFound
        Base.metadata.create_all(engine)
        logger.info('Creating session to feed database.')
        Session = sessionmaker(bind=engine)
        s       = Session()
        logger.info('Reading configuraiton files and adding information to sqlite.')
        map(lambda x: s.add(Recipient(x[0])), csv.reader(open(dest_fic)))
        map(lambda x: s.add(Server(row[0], int(x[1]), x[2], x[3], x[4])), csv.reader(open(serv_fic)))
        s.commit()
    logger.info('Database is ready for business')

    logger.info('Running recipients.')
    Session1 = sessionmaker(bind=engine)
    s1       = Session1()
    serv     = s1.query(Server).first()

    logger.info('Sending emails')
    sm = SendMail(serv.hostname, serv.port, serv.username)
    for case in Switch(imperium):
        if case('arrivee'):
            sm.send_mail(serv.sender, '[DISPO] {0}'.format(get_current_timestamp(),), 'Je suis ready for business.', [x.mail for x in s1.query(Recipient).all()], [])
        if case('depart'):
            sm.send_mail(serv.sender, '[DISPO] {0}'.format(get_current_timestamp(),), 'Bonne soirée.', [x.mail for x in s1.query(Recipient).all()], [])
        if case('depart_pause'):
            sm.send_mail(serv.sender, '[DISPO] {0}'.format(get_current_timestamp(),), 'Go pause, a toute.', [x.mail for x in s1.query(Recipient).all()], [])
        if case('fin_pause'):
            sm.send_mail(serv.sender, '[DISPO] {0}'.format(get_current_timestamp(),), 'C\'est bon redispo.', [x.mail for x in s1.query(Recipient).all()], [])
        else:
            logger.info('Nothing to do.')

    logger.info('#### Done.')

#==========================================================================
#0
