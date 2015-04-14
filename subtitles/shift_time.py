#!/usb/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

kSecInMinute = 60
kSecInHour = kSecInMinute * 60

def add_time(s, add_seconds):
    (h,m,sss) = s.split(':')
    (sec, mls) = sss.split(',')
    h = int(h)
    m = int(m)
    sec = int(sec)
    mls = int(mls)

    ms_time = (h * kSecInHour + m * kSecInMinute + sec) * 1000 + mls
    ms_time += int(float(add_seconds) * 1000.0)

    mls = ms_time % 1000; ms_time /= 1000
    h = ms_time / kSecInHour; ms_time = ms_time % kSecInHour
    m = ms_time / kSecInMinute; ms_time = ms_time % kSecInMinute
    s = ms_time

    res = '%02d:%02d:%02d,%03d' % (h, m, s, mls)
    return res

if len(sys.argv) < 3:
    print >> sys.stderr, "Usage:\n  " + sys.argv[0] + "  <srt-file>  <(+|-)float-shift-time-in-seconds>"
    sys.exit(1)

srt_file = sys.argv[1]
shift_time = float(sys.argv[2])

lines = open(srt_file).readlines()

i = 0
while i < len(lines):
    print lines[i].strip()
    i += 1

    times = lines[i].strip()
    i += 1

    t = times.split(' --> ')
    tfrom = add_time(t[0], shift_time)
    tto = add_time(t[1], shift_time)
    print "%s --> %s" % (tfrom, tto)

    while i < len(lines) and len(lines[i].strip()) > 0:
        print lines[i].strip()
        i += 1

    print ''
    i += 1

