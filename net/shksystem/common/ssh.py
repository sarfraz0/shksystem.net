# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Fabric automation helpers
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 30.11.2014
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

from fabric.api import *
from error      import *

#==========================================================================
# Environment/Static variables
#==========================================================================
# NONE
#==========================================================================
# Classes/Functions
#==========================================================================

class RemoteAction(object):

    def __init__(self, hostName, hopUser=None):

        self.hostName = hostName
        self.hopUser  = hopUser

    def sendRemote(self, localPath, remotePath, ficMod, *args, **kwargs):

        if self.hopUser is not None:
            env.host_string = "{0}@{1}".format(self.hopUser, self.hostName)
            put(localPath, remotePath, mode=ficMod, use_sudo=True)
            if ('ficOwn' in kwargs) and ('ficGrp' in kwargs):
                ficOwn = kwargs['ficOwn']
                ficGrp = kwargs['ficGrp']
                sudo("chown -R {0}:{1} {2}".format(ficOwn, ficGrp, remotePath))
            else:
                raise MissingParameter('File owner and group must be given.')
        else:
            env.host_string = self.hostName
            put(localPath, remotePath, mode=ficMod)

#==========================================================================
#0
