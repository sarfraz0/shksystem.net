# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Automatic rules based folder cleanup
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 15.02.2015
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
import shutil
import re
import csv
import logging
from sqlalchemy                 import create_engine, Column, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import sessionmaker
from ..common.error             import FileNotFound

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

class DataSource(Base):
    __tablename__  = 'data_sources'
    nudoss         = Column(Integer, primary_key=True)
    path           = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('path', name='uq_data_source'),)

    def __init__(self, path):
        self.path = path

class Rule(Base):
    __tablename__ = 'rules'
    nudoss        = Column(Integer, primary_key=True)
    is_active     = Column(Boolean, default=False)
    name          = Column(String, nullable=False)
    dest          = Column(String, nullable=False)
    regex         = Column(String, nullable=False)

    def __init__(self, name, dest, regex):
        self.name  = name
        self.dest  = dest
        self.regex = regex

## Processes

def run_rules():

    conf_dir  = os.path.abspath('../etc/{0}'.format(base_name,))
    rules_fic = os.path.join(conf_dir, 'rules.csv')
    roots_fic = os.path.join(conf_dir, 'roots.csv')
    db_fic    = os.path.join(conf_dir, '{0}.db'.format(base_name,))
    engine    = create_engine('sqlite:///' + db_fic.replace('\\', '\\\\'))

    logger.info('#### Running all rules. ####')

    logger.info('--> Checking data.')
    if not os.path.isfile(db_fic):
        logger.info('----> Database file does not exist. Creating it.')
        if not (os.path.isfile(rules_fic) and os.path.isfile(roots_fic)):
            logger.error('----> Required data files do not exists. Please create them and run again.')
            raise FileNotFound
        Base.metadata.create_all(engine)
        logger.info('----> Database file created.')
        logger.info('----> Creating session to feed database.')
        Session = sessionmaker(bind=engine)
        s       = Session()
        logger.info('------> Reading and adding roots info.')
        with open(roots_fic, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                s.add(DataSource(row[0]))
        logger.info('------> Reading and adding rules info.')
        with open(rules_fic, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                r = Rule(row[0], row[1], row[2])
                if int(row[3]) != 0:
                    r.is_active = False
                s.add(r)
        s.commit()
        logger.info('----> Database feeding is done.')
    logger.info('--> Database is ready for business')

    logger.info('--> Running rules.')
    Session1 = sessionmaker(bind=engine)
    s1       = Session1()
    for root in s1.query(DataSource).all():
        logger.info('----> Processing root : {0}.'.format(root.path,))
        if not os.path.isdir(root.path):
            logger.error('----> Root being processed is not accessible. Skipping.')
            break
        for rule in s1.query(Rule).all():
            logger.info('------> Treating rule name : {0}'.format(rule.name,))
            if not os.path.isdir(rule.dest):
                logger.error('------> Rule destination is not accessible. Skipping.')
            else:
                for path in os.listdir(root.path):
                    if re.match(rule.regex, path.lower()):
                        logger.info('--------> Filename {0} matches rule.'.format(path,))
                        logger.info('--------> Moving file.')
                        shutil.move(os.path.join(root.path, path), os.path.join(rule.dest, path))
                logger.info('------> Rule treated.')
        logger.info('----> Root processed')
    logger.info('--> Rules ran dry.')

    logger.info('#### Done.')

#==========================================================================
#0
