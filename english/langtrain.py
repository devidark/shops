#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Цель: система обучения иностранным словам/фразам по методу доктора Пимслера.
Особенность метода Пимслера заключается вот в чём:
 - человеку показывают слово и его перевод;
 - затем напоминают это слово по такому алгоритму:
    - через 10-20 секунд;
    - через минуту;
    - через 5 минут;
    - через час;
    - через день;
    - через 3 дня.
Такой подход заставляет впечатываться информацию в долгосрочную память.

Основная идея данной проги в том, чтобы построить курс эффективно и ненавязчиво
на основе указанного метода:
1. примерно раз в 40 минут-в час пользователю предлагается серия простых тестов
   длительностью минут на 5. Мы будем засекать не по времени, а по количеству тестов:
   скажем, буквально 40-60;
2. эта серия тестов должна автоматически предлагаться пользователю в такой последовательности,
   чтобы напоминания новых слов происходило с такой же периодичностью, что и описано выше
   (примерно через 10 секунд, примерно через минуту, примерно через 5 минут...).
   NOTE: будем замерять среднее время, которое обучаемый тратит на 1 ответ.
3. прелесть данной проги ещё и в том, что она учитывает, на сколько хорошо обучаемый
   усвоил то или иное слово. Например, он может путать слова "obvious" и "oblivious",
   тогда плохо усвоенные слова программа будет напоминать чаще, чем остальные и до тех пор,
   пока обучаемый их не запомнит основательно.
'''

import os
import sys
import json
import csv
import time
import random

import logger
import utils

#-----------------------------------------------------------------------------------------------------------------------
init_Word = {
    'word': '',
    'translation': '',
    'asked': 0,
    'mistakes': 0,
    'last_asked_time': 0        # последний абсолютный номер выполненного теста (см. ниже performed_tests)
}

init_Dict = {
    'file': '',                 # абсолютный путь к словарю
    'hash': 0,                  # хеш файла
    'words': [],                # слова
    'performed_tests': 0        # абсолютное количество выполненных тестов
}

init_User = {
    'name': '',
    'dicts': [],
    'studying_dict': -1
}

#-----------------------------------------------------------------------------------------------------------------------
class User:
    def __init__(self, user, folder='.'):
        self.fname = os.path.abspath( folder + '/' + user + '.user')
        self.u = None
        if not self.load():
            self.u = dict(init_User)
            self.u['name'] = user

    #---------------------------------------------------------------------------
    # автосохранение при выходе
    def __del__(self):
        if self.is_loaded():
            self.save()

    #---------------------------------------------------------------------------
    def load(self):
        try:
            with open(self.fname) as f:
                self.u = json.load(f, encoding='utf-8')
        except Exception, e:
            logger.Log("ERROR reading user-file %s: '%s'" % (self.fname, str(e)))
            self.u = None
            return False
        return True

    #---------------------------------------------------------------------------
    def is_loaded(self):
        return (self.u != None)

    #---------------------------------------------------------------------------
    def save(self, fname=None):
        if fname == None:
            fname = self.fname
        if fname == None:
            raise Exception("Specify filename to save config")
        try:
            fp = open(fname, 'wb+')
            # т.к. json-либа по умолчанию не умеет сохранять в utf-8, то сначала выводим в unicode
            s = json.dumps(self.u, ensure_ascii=False, indent=2, sort_keys=False)
            # а потом кодим уже саму строку в utf-8
            s = s.encode('utf-8')
            fp.write(s)
        except Exception, e:
            logger.Log("ERROR while writing user-file %s: '%s'" % (fname, str(e)))
            return False
        return True

    #---------------------------------------------------------------------------
    def add_dict(self, fname, encoding):
        # приводим путь словаря к абсолютному виду
        fname = os.path.abspath(fname)
        try:
            open(fname).close()
        except Exception, e:
            logger.Log("ERROR: can't open dictionary file '%s'. Exception: %s" % (fname, str(e)))
            return False

        # ищем заданный словарь среди имеющихся у данного юзера
        have_dicts = len(self.u['dicts'])
        if have_dicts > 0:
            logger.Log("User allready has %d dictionaries. Checking them." % have_dicts)
            for i in xrange( have_dicts ):
                d = self.u['dicts'][i]
                if fname == d['file']:
                    logger.Log("The dictionary '%s' is found in the user's profile" % fname)
                    if utils.get_file_hash(fname) == d['hash']:
                        logger.Log(" - dictionary not changed")
                        return True
                    else:
                        logger.Log(" - dictionary changed, merging it into user's dictionary")
                        if self._merge_dict(self.u['dicts'][i], fname, encoding):
                            self.u['studying_dict'] = i
                            logger.Log(" > selecting dictionary: %s" % fname)
                            return True
                        else:
                            return False

        # добавляем словарь, если он не найден среди имеющихся
        if fname == None:
            return False    # словарь не вмёржен и не добавлен

        logger.Log("Adding the dictionary '%s' to user's profile" % fname)
        i = len(self.u['dicts'])
        self.u['dicts'].append( dict(init_Dict) )
        if self._merge_dict(self.u['dicts'][i], fname, encoding):
            self.u['studying_dict'] = i
            logger.Log(" > selecting dictionary: %s" % fname)
            return True
        return False

    #---------------------------------------------------------------------------
    def _merge_dict(self, udict, fname, encoding):
        h = utils.get_file_hash(fname)
        if h == None:
            return False
        udict['hash'] = h
        udict['file'] = fname

        # читаем словарь из файла
        words = dict()
        try:
            with open(fname) as f:
                csv_reader = csv.reader(f, delimiter=';')
                n = 0
                for row in csv_reader:
                    n += 1
                    if n == 1:          # пропускаем заголовок
                        continue
                    if len(row) != 2:
                        logger.Log(" - warn: skipping bad line %d" % n)
                        continue
                    w = row[0].decode(encoding)
                    t = row[1].decode(encoding)
                    words[w] = t
        except Exception, e:
            logger.Log("ERROR while parsing dictionary file %s. Excpetion: %s" % (fname, str(e)))
            return False

        # просматриваем, какие из слов уже имеются; при нахождении заменяем переводы - возможно они изменились
        for i in xrange( len(udict['words']) ):
            w = udict['words'][i]
            wtext = w['word']
            if wtext in words:
                w['translation'] = words[wtext]
                del words[wtext]

        # добавляем оставшиеся слова, которые не были найдены
        i = len(udict['words'])
        for (w, t) in words.iteritems():
            udict['words'].append( dict(init_Word) )
            udict['words'][i]['word'] = w
            udict['words'][i]['translation'] = t
            i += 1

        logger.Log(" - added %d new word(s)" % len(words))

        return True

#-----------------------------------------------------------------------------------------------------------------------
class Learner:
    progress = [
        15,
        60,
        3 * 60,
        5 * 60,
        40 * 60,
        3 * 60 * 60,
        5 * 60 * 60,
        24 * 60 * 60
    ]

    def __init__(self, udict):
        self.d = udict

    def learn(self):
        if len(self.d['words']) == 0:
            raise Exception("Can't to teach you. Empty dict!")

        test = 0
        kTestsToPerform = 50
        variants_num = 5
        while test < kTestsToPerform:
            test += 1

            # выбираем слово для теста
            selected_word = self.d['words'][0]
            level = selected_word['asked'] / (selected_word['mistakes'] + 1)
            level %= len(self.progress)
            selected_word_period = self.progress[level]

            for w in self.d['words']:
                # рассчитываем, на какой стадии находится юзер по данному слову
                level = w['asked'] / (w['mistakes'] + 1)
                level %= len(self.progress)
                # берём период, через который нужно повторить данное слово
                word_period = self.progress[level]
                # если ранее найдено ближайшее по времени слово, это пропускаем
                if selected_word_period <= word_period:
                    continue
                # не настало ли время для этого слова?
                left_word_period = int(time.time()) - w['last_asked_time']
                if left_word_period >= word_period:
                    selected_word = w
                    selected_word_period = word_period

            # ask
            # - генерим варианты ответов
            variants = random.sample( self.d['words'], variants_num )
            variants = [x['word'] for x in variants]

            ans = selected_word['word']

            already_here = False
            ans_idx = 0
            for i in xrange(0, len(variants)):  # а нет ли среди сэмпла того, что мы выбрали
                if variants[i] == ans:
                    already_here = True
                    ans_idx = i
                    break

            if not already_here:
                ans_idx = random.randint(0, variants_num-1)
                variants[ans_idx] = ans

            # - спрашиваем
            print
            print "Test %d / %d. Translate:" % (test, kTestsToPerform)
            print
            print "   %s" % selected_word['translation'].encode('cp866')
            print
            for i in xrange(len(variants)):
                print "%d. %s" % (i+1, variants[i].encode('cp1251'))

            while True:
                try:
                    user_ans_idx = int(raw_input('Enter number of answer (0-exit): '))
                except:
                    print "Bad number, try again"
                    continue
                if user_ans_idx == 0:
                    print "Exiting."
                    sys.exit(0)
                if user_ans_idx < 1 or user_ans_idx > variants_num:
                    print "Bad number, try again"
                    continue
                break

            user_ans_idx -= 1
            #
            if user_ans_idx == ans_idx:
                print "That's right!"
            else:
                print " *** NO *** the right variant is %d" % (ans_idx+1)
                selected_word['mistakes'] += 1

            # save results
            selected_word['asked'] += 1
            selected_word['last_asked_time'] = int(time.time())

        print
        print "That's good. All tests have done!"

#-----------------------------------------------------------------------------------------------------------------------
def Usage():
    print >> sys.stderr, "Usage:\n  %s <user_name> [<dict> [<encoding>=cp1251]]" % sys.argv[0]

#-----------------------------------------------------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        Usage()
        return 1

    user_name = sys.argv[1]
    dict_file = None
    encoding = 'cp1251'

    if len(sys.argv) > 2:
        dict_file = sys.argv[2]
    if len(sys.argv) > 3:
        encoding = sys.argv[3]

    # загружаем/создаём юзера
    user_dir = '.'
    user = User(user_name, user_dir)

    # проверяем/загружаем словари
    if dict_file == None and len(user.u['dicts']) == 0:
        logger.Log('You have no dictionaries. Please specify a dictionary to learn it.')
        Usage()
        return 2
    elif dict_file != None and not user.add_dict(dict_file, encoding):
        return 3

    # выбираем словарь для обучения
    logger.Log("You have %d dictionary(s)" % len(user.u['dicts']))
    studying_dict = user.u['studying_dict']
    if studying_dict < 0:
        user.u['studying_dict'] = 0
        studying_dict = 0

    # обучаемся
    learner = Learner(user.u['dicts'][studying_dict])
    learner.learn()

    return 0

#-----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit( main() )
