# -*- coding: utf-8 -*-

""" #@(#)------------------------------------------------------------------
    #@(#) OBJET            : Process helpers
    #@(#)------------------------------------------------------------------
    #@(#) AUTEUR           : Sarfraz Kapasi
    #@(#) DATE DE CREATION : 03.01.2015
    #@(#) LICENSE          : GPL-3
    #@(#)------------------------------------------------------------------
"""
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
import binascii
import random
import datetime
import logging, logging.handlers
from subprocess import call
import shutil
import tempfile
import csv
# installed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# custom
from net.shksystem.common.error import FileNotFound, CommandFailure

#==========================================================================
# Environment/Static variables
#==========================================================================
# NONE
#==========================================================================
# Classes/Functions
#==========================================================================

log = logging.getLogger(__name__)

def init_logger(log_path, log_level):
    """ This function add console and file handlers to a Logger object
        init_logger :: FilePath
                   -> String
                   -> IO Logger
    """
    loggo = logging.getLogger()
    # setting formatter
    formater = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s", "%d-%m %H:%M")
    # configuring rotation
    rotate_file_handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=5000000, backupCount=5)
    rotate_file_handler.setFormatter(formater)
    # adding console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formater)
    # configuring logger
    loggo.setLevel(log_level)
    loggo.addHandler(rotate_file_handler)
    loggo.addHandler(console_handler)

    return loggo

def compile_tex(tex_source_file):
    """ This function calls pdflatex on LaTEX source file and performs basic cleanup afterwards
        compileTex :: FilePath
                   -> IO ()
    """
    if not os.path.isfile(tex_source_file):
        log.warn('Input file does not exist : %s.', tex_source_file)
        raise FileNotFound
    tex_file_name = os.path.splitext(tex_source_file)[0]
    exts = ['aux', 'log']

    log.info('Calling pdflatex on %s.', tex_source_file)
    code = call(['pdflatex', '-interaction=nonstopmode', tex_source_file, '>', os.devnull])
    if code != 0:
        log.warn('Compilation failure.')
        raise CommandFailure

    for ext in exts:
        final_file = '{0}{1}{2}'.format(tex_file_name, os.extsep, ext)
        if os.path.isfile(final_file):
            log.info('Deleting %s.', final_file)
            os.unlink(final_file)

    log.info('Compilation success.')

def get_current_timestamp():
    """ This function gets current date and time with the following format: dd/mm/yy:HH:MM
        get_current_timestamp :: IO String
    """
    ret = datetime.datetime.now().isoformat()
    return ret

def gen_random_token(token_len):
    """ This function generate random token_len lenght token
        gen_random_token :: IO String
    """
    ret = binascii.hexlify(os.urandom(token_len))
    return ret

def get_random_elem(lst):
    """ This function returns the nth element of a list
        get_random_elem :: [a]
                        -> IO a
    """
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
        fich, temp_fic = tempfile.mkstemp()
        nfic = open(temp_fic, 'w')
        ofic = open(fic)
        for line in ofic:
            nfic.write(line.replace(patt, subst))
        os.remove(fic)
        shutil.move(temp_fic, fic)
    except OSError:
        log.exception('Replace of patern %s by %s failed on file %s.', patt, subst, fic)
    finally:
        nfic.close()
        ofic.close()
        os.close(fich)

def remove_existing_fics(list_of_fics):
    """ This function unlink a list of file given that they exist on filesystem
        remove_existing_fics :: [FilePath] -- ^ List of files to be removed
                             -> IO ()
    """
    for path in list_of_fics:
        if os.path.isfile:
            os.unlink(path)

def remove_csv_duplicates(csv_fic):
    """ This function recreate a file while removing duplicates lines in it
        remove_csv_duplicates :: FilePath
                              -> IO ()
    """
    if os.path.isfile(csv_fic):
        try:
            fich, tmp_fic = tempfile.mkstemp()
            in_file = open(csv_fic, 'r')
            out_file = open(tmp_fic, 'w')
            seen = set() # fast O(1) amortized lookup

            for line in in_file:
                if line in seen:
                    continue # skip duplicate
                seen.add(line)
                out_file.write(line)
        except OSError:
            log.exception('Cannot remove duplicate in csv file : %s.', csv_fic)
        finally:
            in_file.close()
            out_file.close()
            os.close(fich)

        os.unlink(csv_fic)
        shutil.move(tmp_fic, csv_fic)
    else:
        log.error('Csv file to be filtered does not exist : %s.', csv_fic)

#==========================================================================
#0
