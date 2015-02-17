#!/usr/bin/env python

### Author : Sarfraz Kapasi
### Date   : 09.02.2015

import os
import sys
import logging
from sqlalchemy                 import create_engine, Column, Integer, String, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import sessionmaker, relationship, backref
import paramiko
from net.shksystem.common.utils import init_logger

## Date Sink

Base = declarative_base()

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
    serv_name     = Column(String, nullable=False)
    serv_port     = Column(Integer, default=22)
    serv_username = Column(String, nullable=False)
    serv_password = Column(String, nullable=False)
    component     = Column(Integer, ForeignKey('components.nudoss'))

    def __init__(self, serv_name, serv_username, serv_password, component):
        self.serv_name     = serv_name
        self.serv_username = serv_username
        self.serv_password = serv_password
        self.component     = component

class Rule(Base):
    __tablename__ = "rules"
    nudoss       = Column(Integer, primary_key=True)
    is_active    = Column(Boolean, default=False)
    abs_src_path = Column(String, nullable=False)
    abs_tgt_path = Column(String, nullable=False)
    mod_tgt      = Column(Integer, default=750)
    usr_tgt      = Column(String, nullable=False)
    grp_tgt      = Column(String, nullable=False)
    component    = Column(Integer, ForeignKey('components.nudoss'))

    def __init__(self, abs_src_path, abs_tgt_path, mod_tgt, usr_tgt, grp_tgt, component):
        self.is_active    = True
        self.abs_src_path = abs_src_path
        self.abs_tgt_path = abs_tgt_path
        self.mod_tgt      = mod_tgt
        self.usr_tgt      = usr_tgt
        self.grp_tgt      = grp_tgt
        self.component    = component

## Globals

logger = logging.getLogger()
init_logger(logger, '../log/liv_deploy.out', logging.INFO)

# ../conf/liv_deploy.db
sqlite_fic = os.path.join(os.path.abspath('../conf'), 'liv_deploy.db')
engine     = create_engine('sqlite:///' + sqlite_fic.replace('\\', '\\\\'))

Session = sessionmaker(bind=engine)
s= Session()

## Process
if __name__ == '__main__':

    if lenght(sys.argv) != 2:
        comps = s.query(Component).all()
        logger.info('All components will be processed.')
    else:
        comp  = s.query(Component).filter_by(nudoss=sys.argv[1]).first()
        comps = [comp]
        logger.info('Component {0}/{1} will be processed.'.format(comp.env_group, comp.rule_comp))

    for compo in comps:
        for compu in compo.computers:
            try:
                tr = paramiko.Transport.connect((compu.hostname, compu.port))
                tr.connect(username=compu.username, password=compu.password)
                sf = paramiko.SFTPClient.from_transport(tr)
                logger.info('Connected to {0}@{1}:{2}.'.format(compu.username, compu.hostname, compu.port))

                for rule in compo.rules:
                    sf.put(rule.abs_src_path, rule.abs_tgt_path, confirm=True)
                    sf.chmod(rule.abs_tgt_path, rule.mod_tgt)
                    sf.chown(rule.abs_tgt_path, rule.tgt_)
                    logger.info('Transfert of {0} to {1} done.'.format(rule.abs_src_path, rule.abs_tgt_path))

            finally:
                sf.close()
                tr.close()

#0
