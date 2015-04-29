# -*- coding: utf-8 -*-

"""
    OBJET            : Issues modelisation
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 19.04.2015
    LICENSE          : GPL-3
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# standard
import logging
# installed
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
# custom

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)
Base = declarative_base()

# -----------------------------------------------------------------------------
# Classes and Functions
# -----------------------------------------------------------------------------'


class Issue(Base):
    __tablename__ = 'issues'
    nudoss = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    current_step = Column(String, nullable=False)
    closed = Column(Boolean, default=False)
    owner = Column(String, nullable=False)
    issuer = Column(String, nullable=False)
    wkflow_id = Column(Integer, ForeignKey('workflows.nudoss'), nullable=False)


class Step(Base):
    __tablename__ = 'steps'
    nudoss = Column(Integer, primary_key=True)
    step = Column(String, nullable=False)
    terminal = Column(Boolean, default=False)
    previous_step = Column(Integer, nullable=False)
    next_step = Column(Integer, nullable=False)


class Workflow(Base):
    __tablename__ = 'workflows'
    nudoss = Column(Integer, primary_key=True)
    issues = relationship('Issue', backref='workflow')

# -----------------------------------------------------------------------------
#
