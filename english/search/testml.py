#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Если у Ubuntu и у тебя нет python2.7 запусти на своём Бубне:
#   sudo apt-get install python2.7
# Затем нужно установить необходимые модули:
#   sudo apt-get install python-nltk \
#                      build-essential python-dev python-setuptools \
#                      python-numpy python-scipy \
#                      libatlas-dev libatlas3gf-base
# Либо просто поставь для питона либы:
#   pip install numpy scipy sklearn
#   pip install nltk
#
# На МакОСи должно сработать вот так (не пробовал; предполагается, что питон2.7 уже стоит):
#   pip install -U numpy scipy scikit-learn
#

import os
import sys
import json
import random

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

#-------------------------------------------------------------------------------
# parse argv
if len(sys.argv) < 2:
    print >> sys.stderr, "Usage:\n  %s <scan_json_file> [keyboard]" % sys.argv[0]
    sys.exit(1)

scan_json_file = sys.argv[1]

test_from_keyboard = False
if len(sys.argv) > 2 and sys.argv[2] == 'keyboard':
    test_from_keyboard = True
# test_json_file = sys.argv[2]

#-------------------------------------------------------------------------------
cats = dict()
n2cat = dict()
cat_n = 0

def LoadData(json_file, out_data):
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

        '''sss = u"%s\t%s\t%s" % (cat_name, title, desc)
        print sss.encode('utf-8')
        continue'''

        c = cat_name
        cat_id = cats.get(c, None)

        if cat_id == None:
            cats[c] = cat_n
            n2cat[cat_n] = c
            cat_id = cat_n
            cat_n += 1

        out_data.append( (title, cat_id) )
        #out_data.append( (desc, cat_id) )

def CatId2Name(id):
    global n2cat
    return n2cat.get(id, '<UNKNOWN>')


#-------------------------------------------------------------------------------
# read
data = list()
LoadData(scan_json_file, data)
print >> sys.stderr, "Loaded %d documents" % len(data)

# перемешиваем выборку и подготавливаем из неё обучающее и тестовое множества
random.seed()
random.shuffle( data )

r = len(data)*2/3
train_data = data[:r]
test_data = data[r:]

train_docs   = [d for (d, c) in train_data]
train_target = [c for (d, c) in train_data]

test_docs   = [d for (d, c) in test_data]
test_target = [c for (d, c) in test_data]

# парсим
# v = CountVectorizer()
# v = TfidfVectorizer(ngram_range=(1,1))
# v = TfidfVectorizer(ngram_range=(1,2))
#-----------------------------------------------------------
import nltk.stem
russian_stemmer = nltk.stem.SnowballStemmer('russian')

class StemmedTfidfVectorizer( TfidfVectorizer ):
    def build_analyzer(self):
        analyzer = super(TfidfVectorizer, self).build_analyzer()
        return lambda doc: (russian_stemmer.stem(word) for word in analyzer(doc))
#-----------------------------------------------------------

v = StemmedTfidfVectorizer(min_df=1, ngram_range=(1,2))
train_features = v.fit_transform(train_docs)

# train
print >> sys.stderr, "Learning..."
from sklearn import svm
from sklearn.linear_model import SGDClassifier

# cls = svm.SVC()
cls = SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, n_iter=5, random_state=42)

print >> sys.stderr, cls
cls.fit(train_features, train_target)
print >> sys.stderr, " - done"

#-------------------------------------------------------------------------------
# test
if test_from_keyboard:
    # predict from keyboard
    print "And now let's predict from keyboard.\nType any query in russian language:"
    while (True):
        line = raw_input()
        test_features = v.transform([line])
        pred_t = cls.predict(test_features)
        pred_t = pred_t[0]
        print "\t%d=%s" % (pred_t, CatId2Name(pred_t))
else:
    # predict from the same collection
    print >> sys.stderr, "Testing..."

    # test_docs = list()
    # test_target = list()
    # LoadData(test_json_file, test_docs, test_target)
    # print >> sys.stderr, "Loaded %d test documents" % len(test_docs) '''

    test_predicted = list()

    eq = 0
    for i in xrange( len(test_docs) ):
        d = test_docs[i]
        t = test_target[i]

        test_features = v.transform([d])
        pred_t = cls.predict(test_features)

        pred_t = pred_t[0]

        label = "BAD"
        if t == pred_t:
            eq += 1
            label = "OK"

        prn = u"%d\t%s\t'%s'\texpected/predicted: %d=%s / %d=%s" % (i, label, d, t, CatId2Name(t), pred_t, CatId2Name(pred_t))
        print prn.encode('utf-8')

        test_predicted.append( pred_t )

    # show metrics
    # accuracy = float(eq) / float(len(test_docs))
    # print "Total: %d, equal: %d, accuracy: %f" % (len(test_docs), eq, accuracy)
    from sklearn import metrics

    cat_names = [CatId2Name(x) for x in xrange(cat_n)]
    s = metrics.classification_report(test_target, test_predicted, target_names=cat_names)
    print
    print s.encode('utf-8')
