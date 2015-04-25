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
from sqlalchemy import Column, Integer  # , String
from sqlalchemy.ext.declarative import declarative_base
# custom

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)
Base = declarative_base()

# -----------------------------------------------------------------------------
# Classes and Functions
# -----------------------------------------------------------------------------


class Issue(Base):
    __tablename__ = 'issues'
    nudoss = Column(Integer)


# -----------------------------------------------------------------------------
#
