#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
# installed
from sqlalchemy import create_engine, Table, Column, Integer, Double, String, \
                       ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# custom
from net.shksystem.common.utils import get_current_timestamp

## Globals
# =============================================================================

Base = declarative_base()

## Functions and Classes
# =============================================================================


class Action(Base):
    __tablename__ = 'actions'

    cid = Column(Integer, primary_key=True)
    timestamp = Column(String, nullable=False)
    name = Column(String, nullable=False, unique=True)
    value = Column(Double)
    owner = Column(String, nullable=False)
    subcategory_cid = Column(Integer, ForeignKey('subcategories.cid'))

    def __init__(self, name, owner, subcategory, value=None):
        self.name = name
        self.owner = owner
        self.subcategory = subcategory
        self.value = value
        self.timestamp = get_current_timestamp()

    def to_dict(self):
        ret = {}
        ret['timestamp'] = self.timestamp
        ret['name'] = self.name
        ret['value'] = self.value
        ret['subcategory'] = self.subcategory.name
        ret['owner'] = self.owner
        return ret


class Flogger(Base):
    __tablename__ = 'floggers'

    cid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    owner = Column(String, nullable=False)
    subcategory_cid = Column(Integer, ForeignKey('subcategories.cid'))

    def __init__(self, name, owner, subcategory):
        self.name = name
        self.owner = owner
        self.subcategory = subcategory

    def to_dict(self):
        ret = {}
        ret['name'] = self.name
        ret['owner'] = self.owner
        ret['subcategory'] = self.subcategory.name
        return ret


class SubCategory(Base):
    __tablename__ = 'subcategories'

    cid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    actions = relationship('Action', backref='subcategory')
    floggers = relationship('Flogger', backref='subcategory')
    category_cid = Column(Integer, ForeignKey('categories.cid'))


class Category(Base):
    __tablename__ = 'categories'

    cid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    subcategories = relationship('SubCategory', backref='category')


#
