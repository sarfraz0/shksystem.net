# -*- coding: utf-8 -*-

"""
    OBJET            : Process helpers
    AUTEUR           : Sarfraz Kapasi
    DATE DE CREATION : 03.01.2015
    LICENSE          : GPL-3
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# standard
import os
from datetime import datetime
from logging import getLogger, StreamHandler
from logging.handlers import RotatingFileHandler
from subprocess import call
from shutil import move
from tempfile import mkstemp
# installed
# custom

# -----------------------------------------------------------------------------
# Environment/Static variables
# -----------------------------------------------------------------------------
# NONE
# -----------------------------------------------------------------------------
# Classes and Functions
# -----------------------------------------------------------------------------

log = getLogger(__name__)


def init_logger(log_path, log_level):
    """ This function add console and file handlers to a Logger object
        init_logger :: FilePath
                   -> String
                   -> IO Logger
    """
    loggo = getLogger()
    # setting formatter
    formater = logging \
        .Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s",
                   "%d-%m %H:%M")
    # configuring rotation
    rotate_file_handler = RotatingFileHandler(log_path,
                                              maxBytes=5000000, backupCount=5)
    rotate_file_handler.setFormatter(formater)
    # adding console output
    console_handler = StreamHandler()
    console_handler.setFormatter(formater)
    # configuring logger
    loggo.setLevel(log_level)
    loggo.addHandler(rotate_file_handler)
    loggo.addHandler(console_handler)

    return loggo


def compile_tex(tex_source_file):
    """ This function calls pdflatex on LaTEX source file and performs basic
    cleanup afterwards
        compileTex :: FilePath
                   -> IO ()
    """
    if not os.path.isfile(tex_source_file):
        log.warn('Input file does not exist : %s.', tex_source_file)
        raise OSError
    tex_file_name = os.path.splitext(tex_source_file)[0]
    exts = ['aux', 'log']

    log.info('Calling pdflatex on %s.', tex_source_file)
    code = call(['pdflatex', '-interaction=nonstopmode',
                 tex_source_file, '>', os.devnull])
    if code != 0:
        log.warn('Compilation failure.')
        raise IOError

    for ext in exts:
        final_file = '{0}{1}{2}'.format(tex_file_name, os.extsep, ext)
        if os.path.isfile(final_file):
            log.info('Deleting %s.', final_file)
            os.unlink(final_file)

    log.info('Compilation success.')


def get_current_timestamp():
    """ This function gets current date and time with the following
    format: dd/mm/yy:HH:MM
        get_current_timestamp :: IO String
    """
    ret = datetime.now().isoformat()
    return ret


def replace_in_file(fic, patt, subst):
    """ This function replaces the string value in the file for the new one
        replace_in_file :: FilePath
                        -> String
                        -> String
                        -> IO ()
    """
    nfic = None
    ofic = None
    fich = None
    try:
        fich, temp_fic = mkstemp()
        nfic = open(temp_fic, 'w')
        ofic = open(fic)
        for line in ofic:
            nfic.write(line.replace(patt, subst))
        os.remove(fic)
        move(temp_fic, fic)
    except OSError:
        log.exception('Replace of patern %s by %s failed on file %s.',
                      patt, subst, fic)
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


def remove_file_duplicates(fic):
    """ This function recreate a file while removing duplicates lines in it
        remove_file_duplicates :: FilePath
                              -> IO ()
    """
    if os.path.isfile(fic):
        try:
            fich, tmp_fic = mkstemp()
            in_file = open(fic, 'r')
            out_file = open(tmp_fic, 'w')
            seen = set()  # fast O(1) amortized lookup

            for line in in_file:
                if line in seen:
                    continue  # skip duplicate
                seen.add(line)
                out_file.write(line)
        except OSError:
            log.exception('Cannot remove duplicate in file : %s.', fic)
        finally:
            in_file.close()
            out_file.close()
            os.close(fich)

        os.unlink(fic)
        move(tmp_fic, fic)
    else:
        log.error('File to be filtered does not exist : %s.', fic)


def intersperse(iterable, delimiter):
    """ This function adds given string between elements of a list
    http://stackoverflow.com/questions
        /5655708/python-most-elegant-way-to-intersperse-a-list-with-an-element
        intersperse :: [String]
                    -> String
                    -> [String]
    """
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x


def format_to_regex(to_format):
    ret = ''
    ret = to_format.lower().strip()
    for c in ['-', '_']:
        ret = ret.replace(c, '.*')
    ret = ''.join(intersperse(ret.split(' '), '.*'))
    ret = ret.translate(dict.fromkeys(map(ord, '!?'), None))
    ret = '^.*' + ret + '.*$'

    return ret

# -----------------------------------------------------------------------------
#
