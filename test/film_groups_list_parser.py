#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import json
import urllib2
import lxml.html
import urlparse
import time
import datetime

#-------------------------------------------------------------------------------
# main options
kGetTopK         = 100
kChromeDriverExe = './chromedriver.exe'
kBaseUrl         = 'http://ok.ru'
kLogin           = 'zucker@land.ru'
kPassword        = '12345678dv'

#-------------------------------------------------------------------------------
if len(sys.argv) < 2:
    print >> sys.stderr, "Usage:\n  " + sys.argv[0] + "  <groups_list_file.html>"
    sys.exit(1)

html_file = sys.argv[1]

#-------------------------------------------------------------------------------
def del_spaces(s):
    s = s.replace(' ', '').strip()
    s = s.replace(unichr(0x00A0), '')   # 0x00A0 == &nbsp after decoding from UNICODE
    return s

#-------------------------------------------------------------------------------
print >> sys.stderr, "Parsing '%s'" % html_file
try:
    tree = lxml.html.parse(html_file)
except Exception, e:
    print >> sys.stderr, "Can't open html, exception: '%s'" % str(e)
    sys.exit(2)

xpath_g_list        = "//ul[@class='cardsList __groups']/li[@class='cardsList_li']"
_xpath_item_info    = ".//div/div/div[@class='ucard-b_info']"
xpath_item_href     = _xpath_item_info + "/div[@class='ellip']/a[@class='ucard-b_name o']"  # attr href
xpath_item_name     = xpath_item_href + "/span"                                             # text
xpath_item_mmb_num  = _xpath_item_info + "/div[@class='ucard-b_info_i ellip']/a"            # text

groups = []

n = 0
stored = 0

re_mnum = re.compile(u'(\s?[0-9]+\s?)+', flags=re.UNICODE)

g_list = tree.getroot().xpath(xpath_g_list)
for g_item in g_list:
    n += 1
    try:
        href = g_item.xpath(xpath_item_href)[0].get('href')
        name = g_item.xpath(xpath_item_name)[0].text
        mnum = g_item.xpath(xpath_item_mmb_num)[0].text
    except Exception, e:
        print >> sys.stderr, "Can't parse item, exception: %s" % str(e)
        continue

    # normalize
    try:
        href = kBaseUrl + href
        mnum = del_spaces( re_mnum.match(mnum).group(0) )
        mnum = int(mnum)
    except Exception, e:
        print >> sys.stderr, "Can't normalize, exception: %s" % str(e)
        continue

    groups.append( (href, name, mnum) )
    stored += 1

groups = sorted(groups, key=lambda x: x[2], reverse=True)

"""
for g in groups:
    print (u"%s\t%s\t%s" % (g[0], g[1], g[2])).encode('utf-8')
"""
print >> sys.stderr, "OK, Parsed: %d, stored: %d" % (n, stored)


#-------------------------------------------------------------------------------
print >> sys.stderr, "Crawling groups"


import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


# brws = webdriver.Firefox()    # firefox hangs with selenium :(
brws = webdriver.Chrome(kChromeDriverExe)

# login first
print >> sys.stderr, "Trying to get login..."
try:
    brws.get(kBaseUrl)
    el_login = brws.find_element_by_xpath('//input[@id="field_email"]')
    el_login.send_keys(kLogin)
    el_pswd = brws.find_element_by_xpath('//input[@id="field_password"]')
    el_pswd.send_keys(kPassword)
    el_pswd.send_keys(Keys.RETURN)
except Exception, e:
    print >> sys.stderr, "can't open and login to '%s', exception: %s" % (kBaseUrl, str(e))
    sys.exit(4)

time.sleep(3)       # wait while logging in

print >> sys.stderr, "OK! Crawling..."

xpath_group_cnts    = "//div[@id='hook_Block_MiddleColumnTopCard_MenuAltGroup']/div[1]"
xpath_group_cnt_forums = ".//a[starts-with(@hrefattrs, 'st.cmd=altGroupForum')]/span"       # text
xpath_group_cnt_videos = ".//a[starts-with(@hrefattrs, 'st.cmd=altGroupVideoAll')]/span"    # text

xpath_feed_list     = '//div[@class="feed-list"]/div[@class="feed"]'
xpath_feed_pinned   = './/div[@class="feed-i_pin"]'
xpath_feed_date     = './/div[@class="feed_ac"]/span[@class="feed_date"]'                    # text
xpath_feed_comments = './/a[@data-module="CommentWidgets"]/span[@class="widget_count js-count"]'        # text
xpath_feed_likes    = ".//button[@data-module='LikeComponent']/span[@class='widget_ico ic12 ic12_klass']"  # parent attr data-count
xpath_feed_reposts  = ".//button[@data-module='LikeComponent']/span[@class='widget_ico ic12 ic12_share']"  # parent attr data-count

header = ['url', 'name', 'mem_num', 'forums', 'videos', 'posts', 'period', 'comments', 'likes', 'reposts']
print '"' + '";"'.join(header) + '"'

n = 0
for (url, name, mem_num) in groups:
    if n >= kGetTopK:
        break

    print >> sys.stderr, "%d> group url: %s (members: %d)" % (n, url, mem_num)
    try:
        brws.get(url)
        time.sleep(1)

        # проматываем хорошенько вниз
        for i in range(0, 10):
            if i % 3 == 0:
                # периодически передёргиваем вверх, т.к. одноклассники тупят и не дают промотать вниз.
                brws.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            brws.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        time.sleep(2)

        try:
            cnts = brws.find_element_by_xpath(xpath_group_cnts)
            try:
                forums = int(del_spaces( cnts.find_element_by_xpath(xpath_group_cnt_forums).text ))
            except:
                forums = 0
            try:
                videos = int(del_spaces( cnts.find_element_by_xpath(xpath_group_cnt_videos).text ))
            except:
                videos = 0
        except:
            pass

        # получаем html чтобы распарсить через lxml
        html_el = brws.find_element_by_tag_name('html')
        html_text = html_el.get_attribute("outerHTML")

        # парсим html через lxml
        tree = lxml.html.document_fromstring(html_text)

        flist = tree.xpath(xpath_feed_list)

        posts = len(flist)
        comments = 0
        likes = 0
        reposts = 0
        min_post_time = 10 ** 20
        max_post_time = 0

        print >> sys.stderr, "  parsing, found posts: %d" % posts

        if posts == 0:
            print >> sys.stderr, "  non posts found, skip this group"
            continue

        for feed in flist:
            # пропускаем запиненные посты
            is_pinned = (len(feed.xpath(xpath_feed_pinned)) > 0)
            if is_pinned:
                continue

            post_time = 0

            try:
                feed_data_json = feed.get('data-log-click')
                if feed_data_json != None:
                    feed_data_json = json.loads(feed_data_json)
                    feed_details = feed_data_json.get('feedDetails', None)
                    if feed_details != None:
                        feed_details = json.loads(feed_details)
                        post_time = feed_details.get('createdAt', 0)
            except Exception, e:
                print >> sys.stderr, "post_time exception: %s" % str(e)

            min_post_time = min(post_time, min_post_time)
            max_post_time = max(post_time, max_post_time)

            cm = feed.xpath(xpath_feed_comments)
            if len(cm) > 0:
                comments += int(del_spaces( cm[0].text ))
            lk = feed.xpath(xpath_feed_likes)
            if len(lk) > 0:
                likes += int(del_spaces( lk[0].getparent().get('data-count')))
            rp = feed.xpath(xpath_feed_reposts)
            if len(rp) > 0:
                reposts += int(del_spaces( rp[0].getparent().get('data-count')))

        min_post_time = time.gmtime(min_post_time / 1000)
        max_post_time = time.gmtime(max_post_time / 1000)

        min_dt = datetime.datetime( *min_post_time[:6] )    # since epoch -> timestamp -> datetime
        max_dt = datetime.datetime( *max_post_time[:6] )

        period = max_dt - min_dt
        period = period.days * 24 + period.seconds / (60*60)

        print >> sys.stderr, "  members: %d, forums: %d, videos: %d, posts: %d, comments: %d, likes: %d, reposts: %d, period: %s hours" % \
                             (mem_num, forums, videos, posts, comments, likes, reposts, period)

        z = [url, name, mem_num, forums, videos, posts, period, comments, likes, reposts]
        z = [unicode(x) for x in z]
        print '"' + ( u'";"'.join( z ) ).encode('utf-8') + '"'
    except Exception, e:
        print >> sys.stderr, "Exception: %s" % str(e)
        raise

    # go to parse the next group
    n += 1

brws.quit()
sys.exit(0)
