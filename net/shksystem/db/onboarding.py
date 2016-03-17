#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# anaconda
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, ForeignKey, String, Integer, Boolean, create_engine
from sqlalchemy.orm import relationship, sessionmaker
# installed
from passlib.hash import sha512_crypt


## Globals
# =============================================================================

Base = declarative_base()

## Functions and Classes
# =============================================================================


class Collab(Base):
    __tablename__ = 'collabs'

    owner_pseudo = Column(String, nullable=False)


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

    session.commit()

#
