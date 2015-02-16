# -*- coding: utf-8 -*-
#@(#)----------------------------------------------------------------------
#@(#) OBJET            : Basic mail sending facility
#@(#)----------------------------------------------------------------------
#@(#) AUTEUR           : Sarfraz Kapasi
#@(#) DATE DE CREATION : 07.07.2014
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

import os
import sys
import keyring
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase      import MIMEBase
from email.MIMEText      import MIMEText
from email.Utils         import COMMASPACE, formatdate
from email               import Encoders

#==========================================================================
# Environment/Static variables
#==========================================================================
# NONE
#==========================================================================
# Classes/Functions
#==========================================================================

# -- SendMail
# --------------------------------------------------------------------------
class SendMail:
    """Basic email sending class"""

    def __init__(self, serv, port, usern):
        self._server   = serv
        self._port     = port
        self._username = usern
        self._password = keyring.get_password(serv, usern)

    def send_mail(self, frm, subj, bod, recs, atts=[], htmlbody=False):
        assert type(recs) == list

        msg = MIMEMultipart()
        msg["From"]    = frm
        msg["Subject"] = subj
        msg["To"]      = COMMASPACE.join(recs)
        msg["Date"]    = formatdate(localtime=True)

        if htmlbody:
            msg.attach(MIMEText(bod, "html"))
        else:
            msg.attach(MIMEText(bod))

        if atts:
            for att in atts:
                part = MIMEBase("application", "octet-stream")
                part.set_payload( open(att,"rb").read() )
                Encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment; filename=\"{0}\""
                                .format(os.path.basename(att)))
                msg.attach(part)

        server = smtplib.SMTP("{0}:{1}"
                              .format(self._server, self._port))
        server.starttls()
        server.login(self._username, self._password)
        server.sendmail(frm, recs, msg.as_string())
        server.quit()

#==========================================================================
#0
