# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Org todo to mail conversion and notification
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 19.02.2015
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
from subprocess                 import call
import csv
import logging
import keyring
from sqlalchemy                 import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import sessionmaker
from ..common.error             import FileNotFound
from ..common.utils             import get_current_timestamp, replace_in_file
from ..common.send_mail         import SendMail

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

class Config(Base):
    __tablename__ = 'configs'
    nudoss        = Column(Integer, primary_key=True)
    emacs_path    = Column(String, nullable=False)
    todo_path     = Column(String, nullable=False)

    def __init__(self, emacs_path, todo_path):
        self.emacs_path = emacs_path
        self.todo_path  = todo_path

## Processes

def run_recipients():

    conf_dir  = os.path.abspath('../etc/{0}'.format(base_name,))
    dest_fic  = os.path.join(conf_dir, 'recipients.csv')
    serv_fic  = os.path.join(conf_dir, 'servers.csv')
    conf_fic  = os.path.join(conf_dir, 'configs.csv')
    db_fic    = os.path.join(conf_dir, '{0}.db'.format(base_name,))
    engine    = create_engine('sqlite:///' + db_fic.replace('\\', '\\\\'))

    logger.info('#### Sending notification to all. ####')

    logger.info('Checking data.')
    if not os.path.isfile(db_fic):
        logger.info('Database file does not exist. Creating it.')
        if not (os.path.isfile(dest_fic) and os.path.isfile(serv_fic) and os.path.isfile(conf_fic)):
            logger.error('Required data files do not exists. Please create them and run again.')
            raise FileNotFound
        Base.metadata.create_all(engine)
        logger.info('Creating session to feed database.')
        Session = sessionmaker(bind=engine)
        s       = Session()
        logger.info('Reading and adding recipients info.')
        with open(dest_fic, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                s.add(Recipient(row[0]))
        logger.info('Reading and adding servers info.')
        with open(serv_fic, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                s.add(Server(row[0], int(row[1]), row[2], row[3], row[4]))
        logger.info('Reading and adding configuration info.')
        with open(conf_fic, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                s.add(Config(row[0], os.path.expanduser(row[1])))
        s.commit()
    logger.info('Database is ready for business')

    logger.info('Running recipients.')
    Session1 = sessionmaker(bind=engine)
    s1       = Session1()
    serv     = s1.query(Server).first()
    conf     = s1.query(Config).first()

    logger.info('Conversion from org to html')
    call([conf.emacs_path, conf.todo_path, '--batch', '-f', 'org-export-as-html', '--kill'])
    logger.info('Sending emails')
    sm      = SendMail(serv.hostname, serv.port, serv.username)
    htm_fic = conf.todo_path.replace('.org', '.html')
    #replace_in_file(htm_fic, 'iso-8859-1', 'utf8')
    sm.send_mail(serv.sender, '[TODO] {0}'.format(get_current_timestamp(),), open(htm_fic).read(), [x.mail for x in s1.query(Recipient).all()], [], True)

    #os.unlink(htm_fic)
    #os.unlink(htm_fic + '~')

    logger.info('#### Done.')

#==========================================================================
#0
