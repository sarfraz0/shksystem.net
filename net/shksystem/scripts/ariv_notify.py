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
from sqlalchemy                     import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative     import declarative_base
from sqlalchemy.orm                 import sessionmaker
from net.shksystem.common.error     import FileNotFound
from net.shksystem.common.utils     import get_current_timestamp
from net.shksystem.common.send_mail import SendMail
from net.shksystem.common.logic     import Switch

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
        with open(dest_fic) as f1:
            for w1 in csv.reader(f1):
                s.add(Recipient(w1[0]))
        with open(serv_fic) as f2:
            for w2 in csv.reader(f2):
                s.add(Server(w2[0], int(w2[1]), w2[2], w2[3], w2[4]))
        s.commit()
    logger.info('Database is ready for business')

    logger.info('Running recipients.')
    Session1 = sessionmaker(bind=engine)
    s1       = Session1()
    serv     = s1.query(Server).first()

    logger.info('Sending emails')
    sm      = SendMail(serv.hostname, serv.port, serv.username)
    recs    = [x.mail for x in s1.query(Recipient).all()]
    subject = '[DISPO] {0}'.format(get_current_timestamp(),)
    sender  = serv.sender
    send    = False
    for case in Switch(imperium):
        if case('arrivee'):
            msg  = 'Ready for business.'
            send = True
            break
        if case('depart'):
            msg  = 'Bonne soirée'
            send = True
            break
        if case('depart_pause'):
            msg  = 'Go pause, a toute.'
            send = True
            break
        if case('fin_pause'):
            msg  = 'Re.'
            send = True
            break
    if send:
        for rec in recs:
            sm.send_mail(sender, subject, msg, [rec], [])
    else:
        logger.info('Nothing to be done.')
    logger.info('#### Done.')

#==========================================================================
#0
