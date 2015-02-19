# -*- coding: utf-8 -*-

import datetime
import sys

#-----------------------------------------------------------------------------------------------------------------------
kGlobalIdent = 0

#-----------------------------------------------------------------------------------------------------------------------
def Log(msg, ident = 0):
    if ident == 0 :
        ident = kGlobalIdent
    now = datetime.datetime.now()
    ident_str = ' ' * ident
    fmt = "[%0.4u-%0.2u-%0.2u_%0.2u:%0.2u:%0.2u]%s %s" % (now.year, now.month, now.day, now.hour, now.minute, now.second, ident_str, msg)
    print >> sys.stderr, fmt
