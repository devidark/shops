# -*- coding: utf-8 -*-

import hashlib

#-------------------------------------------------------------------------------
def get_file_hash(fname):
    try:
        sha1 = hashlib.sha1()
        for line in open(fname):
            sha1.update(line)
        return sha1.hexdigest()
    except Exception, e:
        logger.Log("Can't to calculate hash for file %s, Exception: %s" % (fname, str(e)))
    return None
