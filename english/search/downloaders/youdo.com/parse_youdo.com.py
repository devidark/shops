#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import json

import lxml.html
import urllib2
import urlparse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

if len(sys.argv) < 2:
    print >> sys.stderr, "Usage:\n  " + sys.argv[0] + " file"
    sys.exit(1)

plist = []
for line in open(sys.argv[1]):
    line = line.strip().decode('utf-8')
    f = line.split('\t')
    if len(f) != 2:
        continue
    (cat, url) = f
    plist.append( (cat, url) )

print >> sys.stderr, "Loaded %d categories, downloading them" % len(plist)

#-------------------------------------------------
def norm_url(base_url, add_url):
    netloc = urlparse.urlparse(add_url).netloc
    if len(netloc) > 0:
        p = add_url.find(netloc) + len(netloc)
        add_url = add_url[p:]
    else:
        add_url = '/' + add_url.lstrip('/')
    return urlparse.urljoin(base_url, add_url)

#-------------------------------------------------
def norm_price(price):
    price = price.strip().replace(' ', '')
    return int(price)

#-------------------------------------------------
kSpacesDelRe = re.compile(u'[\s]+')
def norm_text(text):
    text = text.strip()
    text = kSpacesDelRe.sub(' ', text)
    return text

#-------------------------------------------------
'''
kBrowser = None

def download_html(url):
    global kBrowser
    try:
        if kBrowser == None:
            kBrowser = webdriver.Firefox()
        kBrowser.get(url)
        elm = kBrowser.find_element_by_tag_name('html')
        elm.send_keys(Keys.ESCAPE)
        item = kBrowser.find_element_by_xpath("//li[@class='b-tasks__item']")

        actions = ActionChains(kBrowser)
        actions.move_to_element(item)
        # actions.context_click(item)
        # actions.send_keys(Keys.ESCAPE)
        actions.perform()

        html_string = kBrowser.page_source
        return html_string
    except Exception, e:
        print >> sys.stderr, "  exc: %s" % str(e)
        return None
'''

kFrontUrl = 'https://youdo.com'
kParsePages = 35

kXpathTasks = "//div/ul/li"
kXpathTaskSubCat    = "//li[@class='b-task-block__brief__item']"
kXpathTaskTitle     = "//h1[@class='b-task-block__header__title']"
kXpathTaskPrice     = "//span[@class='js-price-label']"
kXpathTaskDesc      = "//div[@class='b-task-block__description js-descriptionResult']/span[@class='b-nl2br js-value']"
kXpathTaskAddress   = "//div[@class='b-task-block__info']/span[@class='js-value']"

nnn = 0

for (cat, url) in plist:
    print >> sys.stderr, (" - %s, url: %s" % (cat, url)).encode('cp866')
    for i in xrange(1, kParsePages+1):
        page_url = '%s%d' % (url, i)
        print >> sys.stderr, "   trying download page url: %s" % page_url

        try:
            html_string = urllib2.urlopen(page_url).read()
            page_tree = lxml.html.document_fromstring(html_string)
        except Exception, e:
            print >> sys.stderr, "   download exc: %s" % str(e)
            continue

        tasks_url_list = []

        tasks_list = page_tree.xpath(kXpathTasks)
        for task_item in tasks_list:
            href = task_item.get('data-url')
            if href == None:
                continue
            task_url = norm_url(kFrontUrl, href)
            tasks_url_list.append( task_url )

        print >> sys.stderr, "   tasks pages: %d" % len(tasks_url_list)

        for turl in tasks_url_list:
            print >> sys.stderr, "   downloading task url: %s" % turl
            try:
                html_string = urllib2.urlopen(turl).read()
                task_page_tree = lxml.html.document_fromstring(html_string)

                sub_cat = norm_text( task_page_tree.xpath(kXpathTaskSubCat)[2].text.strip() )
                title = norm_text( task_page_tree.xpath(kXpathTaskTitle)[0].text.strip() )
                desc  = norm_text( task_page_tree.xpath(kXpathTaskDesc)[0].text )
            except Exception, e:
                print >> sys.stderr, "   exc: " + str(e)
                continue

            try:
                price = norm_price( task_page_tree.xpath(kXpathTaskPrice)[0].text.strip() )
            except:
                price = -1

            try:
                addr  = norm_text( task_page_tree.xpath(kXpathTaskAddress)[0].text_content() )
            except Exception, e:
                print >> sys.stderr, "   addr exc: " + str(e)
                addr = ''

            obj = dict()
            obj['cat'] = cat
            obj['sub_cat'] = sub_cat
            obj['title'] = title
            obj['price'] = price
            obj['desc'] = desc
            obj['addr'] = addr
            jstr = json.dumps(obj, ensure_ascii=False)
            print jstr.encode('utf8')
