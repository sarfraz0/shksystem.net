# -*- coding: utf-8 -*-

__author__  = 'Sarfraz Kapasi'
__license__ = 'GPL-3'

# standard
import os
import logging
import json
# installed
import requests
import feedparser
import pandas
# custom
import net.shksystem.common.constants as const
import net.shksystem.constants.feeds as fconst
from net.shksystem.common.utils import check_url, regexify

# Globals
# =============================================================================

logger = logging.getLogger(__name__)

# Classes and Functions
# =============================================================================

class TVShow(object):
    """ TV shows feeds grabber """

    def __init__(self, repo_path):

        if not os.path.exists(repo_path):
            raise OSError(const.PATH_NOT_FOUND_MSG)
        self.repo_path = repo_path

        if not check_url(fconst.NYAA_URL):
            raise ValueError(const.URL_NOT_FOUND_MSG)
        self.nyaa_url  = fconst.NYAA_URL

        self.new_shows = self._get_new_shows(self.nyaa_url)
        self.repo_regexes = self._get_repo_regexes(self.repo_path)

    def _get_new_shows(self, rss_url):
        """
            _get_new_shows :: Self -> Url -> IO Map String MagnetLink
            =================================================================
            This method gets new show names and url couples from the RSS feed
        """
        ret = {}
        f = feedparser.parse(rss_url)[fconst.ITEMS_KEY]
        return ret

    def _get_repo_regexes(self, repo_path):
        """
            _get_repo_regexes :: Self -> String -> IO [Regex]
            ==================================================================
            This method gets the regexes based on the folders in the repo path
        """
        ret = []
        return ret

    def get_new_animes(self):
        """
            get_new_animes :: IO ()
            ===============================================================
            This method checks for new animes and adds them to transmission
        """
        pass
#
