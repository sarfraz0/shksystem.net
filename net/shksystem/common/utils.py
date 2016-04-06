# -*- coding: utf-8 -*-

""" Generic helpers """

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import re
from logging import getLogger, Formatter, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from subprocess import call
from shutil import move, rmtree
from tempfile import mkstemp

# Globals
# =============================================================================

log = getLogger(__name__)

# Classes and Functions
# =============================================================================

def init_logger(log_path, log_level):
    """
        init_logger :: FilePath -> Int -> RootLogger
        ============================================
        This function add console and file handlers to a Logger object
    """
    loggo = getLogger()
    # setting formatter
    formater = Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s",
                         "%d-%m %H:%M")
    # configuring rotation
    rotate_file_handler = TimedRotatingFileHandler(log_path, when="d",
                                                   interval=1, backupCount=10)
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
    """
        compile_tex :: FilePath -> IO ()
        ================================
        This function calls pdflatex on LaTEX file and performs cleanup afterwards
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

def replace_in_file(fic, patt, subst):
    """
        replace_in_file :: FilePath -> String -> String -> IO ()
        ========================================================
        This function replaces the string value in the file for the new one
    """
    nfic = None # type: Any
    ofic = None # type: Any
    fich = None # type: Any
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
    """
        remove_existing_fics :: [FilePath] -> IO ()
        ===========================================
        This function unlink a list of file given that they exist on filesystem
    """
    for path in list_of_fics:
        if os.path.isfile:
            os.unlink(path)

def rmrf(path):
    """
        rmrf :: FilePath -> IO ()
        =========================
        Remove the path object from filesystem if it exists
    """
    if os.path.exists(path):
        if os.path.isdir(path):
            rmtree(path)
        else:
            os.unlink(path)

def empty_dir(dirpath):
    """
        empty_dir :: FilePath -> IO ()
        ==============================
        Remove the content of a directory
    """
    if os.path.isdir(dirpath):
        rmtree(dirpath)
        os.makedirs(dirpath)

def filter_empty_dir(dirpath, filterlist):
    """
        filter_empty_dir :: FilePath -> [FilePath] -> IO ()
        ===================================================
        Remove the content of a directory, leaving only given paths
    """
    if os.path.isdir(dirpath):
        for l in os.listdir(dirpath):
            if l not in filterlist:
                rmrf(os.path.join(dirpath, l))

def remove_file_duplicates(fic):
    """
        remove_file_duplicates :: FilePath -> IO ()
        ===========================================
        This function recreate a file while removing duplicates lines in it
    """
    if os.path.isfile(fic):
        try:
            fich, tmp_fic = mkstemp()
            in_file = open(fic, 'r')
            out_file = open(tmp_fic, 'w')

            # fast O(1) amortized lookup
            seen = set() # type: Set[str]

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
    """ intersperse :: [a] -> a -> [a]
        ==============================
        This function adds given string between elements of a list
        http://stackoverflow.com/questions/5655708
    """
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x

#
