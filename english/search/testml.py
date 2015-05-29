#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

if len(sys.argv) < 3:
    print >> sys.stderr, "Usage:\n  %s <scan_json_file> <test_scan_json_file>" % sys.argv[0]
    sys.exit(1)

# read
scan_json_file = sys.argv[1]
test_json_file = sys.argv[2]

cats = dict()
n2cat = dict()
cat_n = 0

docs = list()

for line in open(scan_json_file):
    line = line.strip()
    rec = json.loads( line )

    cat_name = rec['cat']
    sub_cat_name = rec['sub_cat']
    title = rec['title']
    desc = rec['desc']

    c = cat_name
    if not c in cats:
        cats[c] = cat_n
        n2cat[cat_n] = c
        cat_n += 1

    docs.append( title )

print >> sys.stderr, "Loaded %d documents" % len(docs)

# parse
v = CountVectorizer()
train_data = v.fit_transform(docs)
# print train_data.toarray()

# train
print >> sys.stderr, "Learning..."
from sklearn import svm

target = [n for (c, n) cats.iteritems()]

cls = svm.SVC()
cls.fit(train_data)
print >> sys.stderr, "DONE"

