#!/usb/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

kSecInMinute = 60
kSecInHour = kSecInMinute * 60

def parse_time_to_milliseconds(s):
    (h,m,sss) = s.split(':')
    (sec, mls) = sss.split(',')
    h = int(h)
    m = int(m)
    sec = int(sec)
    mls = int(mls)

    ms_time = (h * kSecInHour + m * kSecInMinute + sec) * 1000 + mls
    return ms_time

def add_time(ms_time, add_seconds):
    ms_time += int(float(add_seconds) * 1000.0)

    mls = ms_time % 1000; ms_time /= 1000
    h = ms_time / kSecInHour; ms_time = ms_time % kSecInHour
    m = ms_time / kSecInMinute; ms_time = ms_time % kSecInMinute
    s = ms_time

    res = '%02d:%02d:%02d,%03d' % (h, m, s, mls)
    return res

#-------------------------------------------------------------------------------
if len(sys.argv) < 4:
    print >> sys.stderr, "Usage:\n  " + sys.argv[0] + "  <srt-file>  <(+|-)float-shift-time-in-seconds>  <(+|-)stretch-time-in-seconds>"
    sys.exit(1)

srt_file = sys.argv[1]
shift_time = float(sys.argv[2])
stretch_time = float(sys.argv[3])

lines = open(srt_file).readlines()

# парсим
subs = []

i = 0
while i < len(lines):
    num = lines[i].strip()
    i += 1

    times = lines[i].strip()
    i += 1

    t = times.split(' --> ')
    tfrom = parse_time_to_milliseconds(t[0])
    tto = parse_time_to_milliseconds(t[1])

    s = ''
    while i < len(lines) and len(lines[i].strip()) > 0:
        if len(s) > 0:
            s += '\n'
        s += lines[i].strip()
        i += 1

    i += 1
    subs.append( (num, tfrom, tto, s) )

if len(subs) == 0:
    sys.exit(0)

# к каждому субтитру будет прибавляться маленькое время, чтобы конечное время растянулось на столько, сколько просили
stretch_time /= float(len(subs))

for s in subs:
    print s[0]
    print '%s --> %s' % (add_time(s[1], shift_time), add_time(s[2], shift_time))
    print s[3]
    print
    shift_time += stretch_time
