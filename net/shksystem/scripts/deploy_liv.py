# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Automatic rules based liv deployment
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 18.02.2015
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
from sqlalchemy                 import create_engine, Column, Integer, String, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import sessionmaker, relationship, backref
import paramiko
from ..common.error             import FileNotFound

#==========================================================================
# Environment/Static variables
#==========================================================================

logger    = logging.getLogger(__name__)
base_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
Base      = declarative_base()

conf_dir  = os.path.abspath('../etc/{0}'.format(base_name,))
rules_fic = os.path.join(conf_dir, 'rules.csv')
compu_fic = os.path.join(conf_dir, 'computers.csv')
compo_fic = os.path.join(conf_dir, 'components.csv')
db_fic    = os.path.join(conf_dir, '{0}.db'.format(base_name,))
engine    = create_engine('sqlite:///' + db_fic.replace('\\', '\\\\'))

#==========================================================================
# Classes/Functions
#==========================================================================

## Data Sink

class Component(Base):
    __tablename__  = "components"
    nudoss         = Column(Integer, primary_key=True)
    env_group      = Column(String, nullable=False)
    rule_comp      = Column(String, nullable=False)
    computers      = relationship('Computer', backref='computers')
    rules          = relationship('Rule', backref='rules')
    __table_args__ = (UniqueConstraint('env_group', 'rule_comp', name='uq_component'),)

    def __init__(self, nudoss, env_group, rule_comp):
        self.nudoss    = nudoss
        self.env_group = env_group
        self.rule_comp = rule_comp

class Computer(Base):
    __tablename__ = "computers"
    nudoss        = Column(Integer, primary_key=True)
    hostname      = Column(String, nullable=False)
    port          = Column(Integer, default=22)
    username      = Column(String, nullable=False)
    password      = Column(String, nullable=False)
    component     = Column(Integer, ForeignKey('components.nudoss'))

    def __init__(self, hostname, username, password, component):
        self.hostname  = hostname
        self.username  = username
        self.password  = password
        self.component = component

class Rule(Base):
    __tablename__ = "rules"
    nudoss        = Column(Integer, primary_key=True)
    is_active     = Column(Boolean, default=False)
    source        = Column(String, nullable=False)
    target        = Column(String, nullable=False)
    mode          = Column(Integer, default=750)
    uid           = Column(Integer, nullable=False)
    gid           = Column(Integer, nullable=False)
    component     = Column(Integer, ForeignKey('components.nudoss'))

    def __init__(self, source, target, mode, uid, gid, component):
        self.is_active = True
        self.source    = source
        self.target    = target
        self.mode      = mode
        self.uid       = uid
        self.gid       = gid
        self.component = component

## Processes

def run_deployment():
    logger.info('#### Running all rules. ####')

    logger.info('--> Checking data.')
    if not os.path.isfile(db_fic):
        logger.info('----> Database file does not exist. Creating it.')
        if not (os.path.isfile(rules_fic) and os.path.isfile(compu_fic) and os.path.isfile(compo_fic)):
            logger.error('----> Required data files do not exists. Please create them and run again.')
            raise FileNotFound
        Base.metadata.create_all(engine)
        logger.info('----> Database file created.')
        logger.info('----> Creating session to feed database.')
        Session = sessionmaker(bind=engine)
        s       = Session()
        logger.info('------> Reading and adding components info.')
        i = 1
        with open(compo_fic, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                s.add(Component(i, row[0], row[1]))
                i += 1
        s.flush()
        logger.info('------> Reading and adding computers info.')
        with open(compu_fic, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                s.add(Computer(row[0], row[1], row[2], int(row[3])))
        logger.info('------> Reading and adding rules info.')
        with open(rules_fic, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                r = Rule(row[0], row[1], int(row[2]), int(row[3]), int(row[4]), int(row[5]))
                if int(row[6]) != 0:
                    r.is_active = False
                s.add(r)
        s.commit()
        logger.info('----> Database feeding is done.')
    logger.info('--> Database is ready for business')

    logger.info('--> Running rules.')
    Session1 = sessionmaker(bind=engine)
    s1       = Session1()

    if len(sys.argv) != 2:
        comps = s1.query(Component).all()
    else:
        comp  = s1.query(Component).filter_by(nudoss=sys.argv[1]).first()
        comps = [comp]

    for compo in comps:
        logger.info('----> Runing rules for component {0}/{1}'.format(compo.env_group, compo.rule_comp))
        for compu in compo.computers:
            try:
                tr = paramiko.Transport((compu.hostname, compu.port))
                tr.start_client()
                tr.connect(username=compu.username, password=compu.password)
                sf = paramiko.SFTPClient.from_transport(tr)
                logger.info('------> Connected to {0}@{1}:{2}.'.format(compu.username, compu.hostname, compu.port))

                for rule in compo.rules:
                    sf.put(rule.source, rule.target, confirm=True)
                    sf.chmod(rule.target, rule.mode)
                    sf.chown(rule.target, rule.uid, rule.gid)
                    logger.info('--------> Transfert of {0} to {1} done.'.format(rule.source, rule.target))
                logger.info('------> All rules treated for current computer.')
            finally:
                sf.close()
                tr.close()
        logger.info('----> Rules ran dry for component.')
    logger.info('--> All component have been deployed')

    logger.info('#### Done.')

#==========================================================================
#0
