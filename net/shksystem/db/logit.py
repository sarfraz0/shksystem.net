#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
from datetime import datetime
# installed
from sqlalchemy import create_engine, Table, Column, Integer, Float, String, \
                       ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# custom

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
    value = Column(Float)
    owner = Column(String, nullable=False)
    subcategory_cid = Column(Integer, ForeignKey('subcategories.cid'))

    def __init__(self, name, owner, subcategory, value=None):
        self.name = name
        self.owner = owner
        self.subcategory = subcategory
        self.value = value
        self.timestamp = datetime.now().isoformat()

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

    def to_action(self, value=None):
        return Action(self.name, self.owner, self.subcategory, value)

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

    def __init__(self, name, category):
        self.name = name
        self.category = category

    def to_dict(self):
        ret = {}
        ret['name'] = self.name
        ret['actions'] = [x.name for x in self.actions]
        ret['floggers'] = [x.name for x in self.floggers]
        ret['category'] = self.category.name
        return ret


class Category(Base):
    __tablename__ = 'categories'

    cid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    subcategories = relationship('SubCategory', backref='category')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        ret = {}
        ret['name'] = self.name
        ret['subcategories'] = [x.name for x in self.subcategories]
        return ret


def init_db(easy_connect):
    """
        init_db :: String -> IO ()
        ==========================
        Initialize the database schema
    """
    engine = create_engine(easy_connect)
    Base.metadata.create_all(engine)

def populate_db(easy_connect):
    """
        populate_db :: String -> IO ()
        ==============================
        Initialize the database schema and adds the standard columns
    """
    engine = create_engine(easy_connect)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # categories
    alimentation = Category('ALIMENTATION')
    sante = Category('SANTE')
    divertissement = Category('DIVERTISSEMENT')
    finance = Category('FINANCE')
    work = Category('WORK')
    session.add_all([alimentation, divertissement, finance, work])
    session.commit()

    # subcategories
    asthme = SubCategory('ASTHME', sante)
    douleurs = SubCategory('DOULEURS', sante)
    debit = SubCategory('DEBIT', finance)
    credit = SubCategory('CREDIT', finance)
    pomo = SubCategory('POMO', work)
    timimg = SubCategory('TIME', work)
    session.add_all([asthme, douleurs, debit, credit, pomo, timimg])
    session.commit()

#
