#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sudo apt-get install python-sklearn python-nltk

import os
import sys
import json

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

#-------------------------------------------------------------------------------
if len(sys.argv) < 3:
    print >> sys.stderr, "Usage:\n  %s <scan_json_file> <test_scan_json_file>" % sys.argv[0]
    sys.exit(1)

#-------------------------------------------------------------------------------
cats = dict()
n2cat = dict()
cat_n = 0

def LoadData(json_file, out_docs, out_target):
    global cats
    global n2cat
    global cat_n

    for line in open(json_file):
        line = line.strip()
        rec = json.loads( line )

        cat_name = rec['cat']
        sub_cat_name = rec['sub_cat']
        title = rec['title']
        desc = rec['desc']

        c = cat_name
        cat_id = cats.get(c, None)

        if cat_id == None:
            cats[c] = cat_n
            n2cat[cat_n] = c
            cat_id = cat_n
            cat_n += 1

        out_docs.append( title )
        #out_docs.append( desc )
        out_target.append( cat_id )

def CatId2Name(id):
    return n2cat.get(id, '<UNKNOWN>')

#-------------------------------------------------------------------------------
# read
scan_json_file = sys.argv[1]
test_json_file = sys.argv[2]

docs = list()
target = list()
LoadData(scan_json_file, docs, target)

print >> sys.stderr, "Loaded %d documents" % len(docs)

# parse
# v = CountVectorizer()
# v = TfidfVectorizer(ngram_range=(1,1))
# v = TfidfVectorizer(ngram_range=(1,2))

import nltk.stem
russian_stemmer = nltk.stem.SnowballStemmer('russian')

class StemmedTfidfVectorizer( TfidfVectorizer ):
    def build_analyzer(self):
        analyzer = super(TfidfVectorizer, self).build_analyzer()
        return lambda doc: (russian_stemmer.stem(word) for word in analyzer(doc))

v = StemmedTfidfVectorizer(min_df=1, ngram_range=(1,2))
train_data = v.fit_transform(docs)
# print train_data.toarray()

# train
print >> sys.stderr, "Learning..."
from sklearn import svm

cls = svm.SVC()
print >> sys.stderr, cls
cls.fit(train_data, target)
print >> sys.stderr, " - done"

#-------------------------------------------------------------------------------
# test
print >> sys.stderr, "Testing..."

test_docs = list()
test_target = list()
test_predicted = list()
LoadData(test_json_file, test_docs, test_target)
print >> sys.stderr, "Loaded %d test documents" % len(test_docs)

eq = 0
for i in xrange( len(test_docs) ):
    d = test_docs[i]
    t = test_target[i]

    d_data = v.transform([d])
    pred_t = cls.predict(d_data)

    pred_t = pred_t[0]

    label = "BAD"
    if t == pred_t:
        eq += 1
        label = "OK"

    prn = u"%d\t%s\t'%s'\texpected/predicted: %d=%s / %d=%s" % (i, label, d, t, CatId2Name(t), pred_t, CatId2Name(pred_t))
    print prn.encode('utf-8')

    test_predicted.append( pred_t )

#-------------------------------------------------------------------------------
# show metrics
# accuracy = float(eq) / float(len(test_docs))
# print "Total: %d, equal: %d, accuracy: %f" % (len(test_docs), eq, accuracy)
from sklearn import metrics

cat_names = [CatId2Name(x) for x in xrange(cat_n)]
s = metrics.classification_report(test_target, test_predicted, target_names=cat_names)
print
print s.encode('utf-8')
