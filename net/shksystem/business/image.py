# -*- coding: utf8 -*-

""" Image manipulation helpers """

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
# anaconda
from PIL import Image

# Globals
# =============================================================================

logger = logging.getLogger()

# Functions and Classes
# =============================================================================

def resize_for_keepass(imgpath: str) -> None:
    """ This function resizes a png file
    so that it can be used as a  keepass entry icon """

    logger.info('Trying to resize file %s to 24x24', imgpath)
    size = (24, 24)
    if not os.path.isfile(imgpath):
        logger.error('File to resize does not exist!')
    else:
        im = Image.open(imgpath)
        im.resize(size, Image.LINEAR)
        im.save(imgpath)
        logger.info('Resizing done.')

#
