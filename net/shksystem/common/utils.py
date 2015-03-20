# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Process helpers
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 03.01.2015
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

# standard
import os
import sys
import binascii
import random
import datetime
import logging, logging.handlers
from subprocess                 import call
import shutil
import tempfile
import csv
from pprint                     import pprint
# installed
from sqlalchemy                 import create_engine
from sqlalchemy.orm             import sessionmaker
# custom
from net.shksystem.common.error import *

#==========================================================================
# Environment/Static variables
#==========================================================================
# NONE
#==========================================================================
# Classes/Functions
#==========================================================================

logger = logging.getLogger(__name__)

## This function add console and file handlers to a Logger object
# initLogger :: FilePath
#            -> String
#            -> IO Logger
def init_logger(log_path, log_level):

    loggo = logging.getLogger()
    # setting formatter
    formater = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s", "%d-%m %H:%M")
    # configuring rotation
    hd = logging.handlers.RotatingFileHandler(log_path, maxBytes=5000000, backupCount=5)
    hd.setFormatter(formater)
    # adding console output
    ch = logging.StreamHandler()
    ch.setFormatter(formater)
    # configuring logger
    loggo.setLevel(log_level)
    loggo.addHandler(hd)
    loggo.addHandler(ch)

    return loggo

## This function calls pdflatex on LaTEX source file
#    and performs basic cleanup afterwards
# compileTex :: FilePath
#            -> IO ()
def compile_tex(tex_source_file):
    if not os.path.isfile(tex_source_file):
        logger.warn('Input file does not exist'.format(tex_source_file,))
        raise FileNotFound
    tex_file_name = os.path.splitext(tex_source_file)[0]
    exts          = ['aux', 'log']

    logger.info('Calling pdflatex on {0}.'.format(tex_source_file,))
    code = call(['pdflatex', '-interaction=nonstopmode', tex_source_file, '>', os.devnull])
    if code != 0:
        logger.warn('Compilation failure.')
        raise CommandFailure

    for ext in exts:
        final_file = '{0}{1}{2}'.format(tex_file_name, os.extsep, ext)
        if os.path.isfile(final_file):
            logger.info('Deleting {0}.'.format(final_file,))
            os.unlink(final_file)

    logger.info('Compilation success.')

## This function gets current date and time with the following format:
#    dd/mm/yy:HH:MM
# get_current_timestamp :: IO String
def get_current_timestamp():
    ret = datetime.datetime.now().isoformat()
    return ret

## This function generate random n lenght token
# gen_random_token :: IO String
def gen_random_token(n):
    ret = binascii.hexlify(os.urandom(n))
    return ret

## This function returns the nth element of a list
# get_random_elem :: [a]
#                 -> IO a
def get_random_elem(lst):
    ret = random.choice(lst)
    return ret

def replace_in_file(fic, patt, subst):
    """ This function replaces the string value in the file for the new one
        replace_in_file :: FilePath
                        -> String
                        -> String
                        -> IO ()
    """
    try:
        fh, pabs = tempfile.mkstemp()
        nfic     = open(pabs,'w')
        ofic     = open(fic)
        for line in ofic:
            nfic.write(line.replace(patt, subst))
        os.remove(fic)
        shutil.move(pabs, fic)
    except:
        logger.exception('Replace of patern {0} by {1} failed on file {2}.'
                     .format(patt, subst, fic))
    finally:
        nfic.close()
        ofic.close()
        os.close(fh)

def remove_existing_fics(list_of_fics):
    """ This function unlink a list of file given that they exist on filesystem
        remove_existing_fics :: [FilePath] -- ^ List of files to be removed
                             -> IO ()
    """
    for p in list_of_fics:
        if os.path.isfile:
            os.unlink(p)

def remove_csv_duplicates(csv_fic):
    """ This function recreate a file while removing duplicates lines in it
        remove_csv_duplicates :: FilePath
                              -> IO ()
    """
    if (os.path.isfile(csv_fic)):
        try:
            fh, tmp_fic = tempfile.mkstemp()
            in_file     = open(csv_fic, 'r')
            out_file    = open(tmp_fic, 'w')
            seen = set() # fast O(1) amortized lookup

            for line in in_file:
                if line in seen:
                    continue # skip duplicate
                seen.add(line)
                out_file.write(line)
        except:
            logger.exception('Cannot remove duplicate in csv file : {0}'.format(csv_fic,))
        finally:
            in_file.close()
            out_file.close()
            os.close(fh)

        os.unlink(csv_fic)
        shutil.move(tmp_fic, csv_fic)
    else:
        logger.error('Csv file to be filtered does not exist : {0}.'.format(csv_fic,))

def get_uq_comb_in_csv(csv_fic, uq_table):
    """ This function takes a csv file and an uniqueness table and returns
        the number of unique elements statisfying the table
        get_uq_comb_in_csv :: FilePath
                           -> [Integer]
                           -> IO Integer
    """
    ret = 0

    try:
        csv_hand  = open(csv_fic)
        data      = [k for k in csv.reader(csv_hand)]
        data_dups = []
        data_len  = len(data)
        i         = 0
        j         = 0
        while i < len(data):
            while j < len(data):
                # Test of value n with n+1
                # If elem z of n doesn't equal elem z of n+1 then rows aren't equal
                row_eq = False if i == j else all(map(lambda x: data[i][x] == data[j][x], uq_table))
                # The two rows aren't equal that's good, let's continue else this element isn't unique
                if not row_eq:
                    j += 1
                else:
                    del data[i]
                # Now we got to the end without getting any break
                if j == (len(data) -1):
                    ret += 1
            i += 1
            j = 0
    except:
        logger.exception('Error while reading csv file : {0}'.format(csv_fic,))
    finally:
        csv_hand.close()

    return ret

def sqlite_alchemy_feed(csv_fic, db_fic, dat, uq_table):
    """ This function feeds sqlite database with csv list
        sqlite_alchemy_feed :: FilePath          ^ -- Csv filepath
                            -> FilePath          ^ -- SQLite filepath
                            -> (M a, f b -> M a) ^ -- Tuple composed of datatype and function that produce such data from row
                            -> [Integer]         ^ -- Uniqueness table
                            -> IO ()
    """
    engine = create_engine('sqlite:///' + db_fic.replace('\\', '\\\\'))
    Session = sessionmaker(bind=engine)
    s       = Session()
    logger.info('Reading configuration files and updating database if needed.')
    remove_csv_duplicates(csv_fic)
    with open(csv_fic) as f1:
        db_count  = s.query(dat[0].nudoss).count()
        csv_count = get_uq_comb_in_csv(csv_fic, uq_table)
        logger.debug('Number of queryed feeds           : ' + str(db_count))
        logger.debug('Number of unique rows in csv file : ' + str(csv_count))
        if db_count == 0:
            for row in csv.reader(f1):
                s.add(dat[1](row))
        elif csv_count == db_count:
            logger.info('Nothing to update.')
        elif csv_count < db_count:
            logger.info('Csv data is too short. File may not be in sync with db or corrupt.')
        else:
            csv_dump = [r for r in csv.reader(f1)]
            for row in csv_dump[(csv_count - db_count):-1]:
                try:
                    s.add(dat[1](row))
                except:
                    logger.exception('New data already exist or is corrupt. Update the csv!')
                    break
    s.commit()

def dump_sqlite_alchemy_datatype(csv_fic, s, dat):
    """ This function takes a csv file, a SQLAlchemy session and datatype and dump its column given formating function
        dump_sqlite_alchemy_datatype :: FilePath
                                     -> DBSession
                                     -> M a
                                     -> IO ()
    """
    data = s.query(dat).all()


#==========================================================================
#0
