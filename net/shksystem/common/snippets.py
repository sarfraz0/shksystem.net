# -*- coding: utf-8 -*-

""" Do not uses these functions in code, they are just for information"""


__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
from datetime import datetime
import multiprocessing
import uuid
# installed
# custom

# Globals
# =============================================================================

logger = getLogger(__name__)

# Classes and Functions
# =============================================================================

def get_current_timestamp():
    """
        get_current_timestamp :: IO String
        ==================================
        This function gets current date and time with the ISO format
    """
    return datetime.now().isoformat()

def get_cpu_number():
    """
        get_cpu_number :: IO Int
        =============================================================
        This proceduce gets the numbers of cpu on the current machine
    """
    return multiprocessing.cpu_count()

def get_random_string(lengt):
    """
        get_random_string :: Int -> IO String
        ==========================================
        Generate a midsize random string
        http://stackoverflow.com/questions/2257441
    """
    if lengt > 32:
        raise ValueError('lenght is too hight')
    return str(uuid.uuid4()).upper().replace('-', "")[0:lengt]


#
