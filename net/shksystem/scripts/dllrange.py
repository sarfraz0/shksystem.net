# -*- coding: utf-8 -*-

"""
    OBJET            : Automatic rules based folder cleanup
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 15.02.2015
    LICENSE          : GPL-3
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# standard
import os
import shutil
import re
import logging
# installed
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# custom

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)
Base = declarative_base()

# -----------------------------------------------------------------------------
# Classes & Functions
# -----------------------------------------------------------------------------

# MODELS
# -----------------------------------------------------------------------------


class Rule(Base):
    __tablename__ = 'rules'
    nudoss = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    regex = Column(String, nullable=False)
    dest = Column(String, nullable=False)

# PROCESSES
# -----------------------------------------------------------------------------


def run_rules(conf):
    Session = sessionmaker(bind=create_engine(conf['DB_URI']))
    db = Session()
    for source in conf['SOURCES']:
        logger.info('Processing source : %s.', source)
        logger.info('There is %d rules to process', db.query(Rule).count())
        for rule in db.query(Rule).all():
            logger.info('Treating rule named : %s', rule.title)
            dest = os.path.join(rule.dest, rule.title)
            if not os.path.isdir(dest):
                try:
                    os.mkdir(dest)
                except OSError:
                    logger.warn('Rule destination {0} is not accessible.'
                                .format(dest,) + ' Skipping.')
                    continue
            for filename in os.listdir(source):
                if re.match(rule.regex, filename.strip().lower()):
                    logger.info('Filename %s matches rule.', filename)
                    dest_path = os.path.join(dest, filename)
                    try:
                        os.unlink(dest_path)
                    except:
                        pass
                    logger.info('Moving file.')
                    shutil.move(os.path.join(source, filename), dest_path)

# -----------------------------------------------------------------------------
#
