#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# DESCRIPTION : shksystem.net build and installation
# DATE        : 27.07.2015
# AUTHOR      : Sarfraz Kapasi
# LICENSE     : GPL-3
# -----------------------------------------------------------------------------

# standard
import os
from os.path import join, abspath, exists
from shutil import rmtree
import json
from subprocess import call
# installed
# custom

# Globals
# ---------------------------------------

cnf = {}
with open(abspath('deploy.json')) as f:
    cnf = json.load(f)
pip = join(cnf['bin'], 'pip')
buildpath = join(abspath('dist'), cnf['build_name'])
buildirs = ['build', 'dist', '{0}.egg-info'.format(cnf['pkg_name'],)]
wheel_build = '{0} setup.py bdist_wheel'.format(join(cnf['bin'], 'python'),)
remove_command = 'sudo su - -c \'echo y|{0} uninstall {1}\'' \
        .format(pip, cnf['pkg_name'])
install_command = 'sudo su - -c \'{0} install {1}\''.format(pip, buildpath)


# Classes and functions
# ---------------------------------------

def cleanup():
    for f in buildirs:
        if exists(abspath(f)):
            rmtree(f)

def main():
    cleanup()
    b_ret = call([wheel_build], shell=True)
    if b_ret == 0:
        call([remove_command], shell=True)
        call([install_command], shell=True)
        cleanup()

# ---------------------------------------

if __name__ == '__main__':
    main()

#
