#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import urllib2
import lxml.html
import urlparse
from string import maketrans

#-------------------------------------------------
class Rules_fullbags_ru:
    name = "fullbags.ru"

    prod_div    = "//div[@class='c_box']/div[@class='p_id_cat prod']"
    href        = ".//div[@class='product-name']/a"                         # attr href
    price       = ".//div[@class='product-price']/span[@class='price']"     # text
    title       = str(href)                                                 # text
    front_img   = ".//img[@class='product-retina']"                         # attr src

    prod_page_div   = "//div[@id='product-new']"
    desc            = ".//div[@class='right_product_d']/div/div/div"        # text_content()
    images          = ".//div[@class='min_iamfges']/a"                      # attr href

    brand           = ".//div[@class='description_product']/div/table/tr[1]/td[@class='text_table_2']" # text
    material        = ".//div[@class='description_product']/div/table/tr[2]/td[@class='text_table_2']" # text
    color           = ".//div[@class='description_product']/div/table/tr[3]/td[@class='text_table_2']" # text
    podkladka       = ".//div[@class='description_product']/div/table/tr[4]/td[@class='text_table_2']" # text
    dimensions      = ".//div[@class='description_product']/div/table/tr[5]/td[@class='text_table_2']" # text
    size            = ".//div[@class='description_product']/div/table/tr[6]/td[@class='text_table_2']" # text

    urls = [
        (u'Женские сумки',  'http://fullbags.ru/catalog/zhenskie-sumki?page=all'),
        (u'Мужские сумки',  'http://fullbags.ru/catalog/muzhskie-sumki?page=all'),
        (u'Саквояжи',       'http://fullbags.ru/catalog/sakvoyazhi?page=all'),
        (u'Клатчи и папки', 'http://fullbags.ru/catalog/klatchi-i-papki?page=all'),
        (u'Рюкзаки',        'http://fullbags.ru/catalog/ryukzaki?page=all'),
        (u'Кошельки',       'http://fullbags.ru/catalog/koshelki?page=all'),
        (u'Перчатки',       'http://fullbags.ru/catalog/perchatki'),
        (u'Ремни',          'http://fullbags.ru/catalog/remni')
    ]

#-------------------------------------------------
class Prod:
    category = ''
    url = ''
    price = ''
    title = ''
    prod_page = ''

    desc = ''
    images = []
    brand = ''
    material = ''
    color = ''
    podkladka = ''
    dimensions = ''
    size = ''

    @staticmethod
    def PrintCSVTitle():
        t = [
            "Товар",
            "Категория",
            "Бренд",                # бренд товара
            "Вариант",              # название варианта
            "Цена",                 # цена товара
            "Старая цена",          # старая цена товара
            "Склад",                # количество товара на складе
            "Артикул",              # артикул товара
            "Видим",                # отображение товара на сайте (0 или 1)
            "Рекомендуемый",        # является ли товар рекомендуемым (0 или 1)
            "Аннотация",            # краткое описание товара
            "Адрес",                # адрес страницы товара
            "Описание",             # полное описание товара
            "Изображения",          # имена локальных файлов или url изображений в интернете, через запятую
            "Заголовок страницы",   # заголовок страницы товара (Meta title)
            "Ключевые слова",       # ключевые слова (Meta keywords)
            "Описание страницы",    # описание страницы товара (Meta description)
            # дополнительные характеристики
            "Бренд",
            "Материал",
            "Цвет",
            "Подкладка",
            "Размеры",
            "Размер"
        ]
        s = '"' + '";"'.join(t) + '"'
        print s

    def Print(s):
        # Simpla-CMS CSV-format:
        res = [
            s.title,        # Товар название товара
            s.category,     # Категория категория товара
            s.brand,        # Бренд бренд товара
            u'',            # Вариант название варианта
            s.price,        # Цена цена товара
            u'',            # Старая цена старая цена товара
            u'',            # Склад количество товара на складе
            u'',            # Артикул артикул товара
            1,              # Видим отображение товара на сайте (0 или 1)
            0,              # Рекомендуемый является ли товар рекомендуемым (0 или 1)
            s.title,        # Аннотация краткое описание товара
            s.prod_page,     # Адрес адрес страницы товара
            s.desc,         # Описание полное описание товара
            s.images,       # Изображения имена локальных файлов или url изображений в интернете, через запятую
            s.title,        # Заголовок страницы заголовок страницы товара (Meta title)
            s.title,        # Ключевые слова ключевые слова (Meta keywords)
            s.title,        # Описание страницы описание страницы товара (Meta description)
            # add chars
            s.brand,        # Бренд
            s.material,     # Материал
            s.color,        # Цвет
            s.podkladka,    # Подкладка
            s.dimensions,   # Размеры
            s.size          # Размер
        ]

        out = u''
        for r in res:
            if len(out) > 0:
                out += ';'
            if type(r) is int:
                out += str(r)
            elif type(r) is list:
                out += '"' + ', '.join(r) + '"'
            else:
                out += '"' + r + '"'

        print out.encode('utf-8')

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
tr_from = u' абвгдеёжзийклмнопрстуфхцчшщъыьэюя!"#%\'()*+,-./:;<=>?@[\]^_`{|}~'
tr_to   = u'-abvgdeejzijklmnoprstufhc4ssqyqeuy-------------------------------'
tr_from = [ord(c) for c in tr_from]
tr_table = dict(zip(tr_from, tr_to))

def translit(txt):
    txt = txt.lower()
    t = ''
    for z in xrange(0, len(txt)):
        t += tr_table.get(ord(txt[z]), txt[z])
    return t

#-------------------------------------------------
def download_images(img_dir, images, brand, name):
    kBaseUrl = ''

    flist = []
    i = 0
    for img in images:
        i += 1
        try:
            content = urllib2.urlopen(img).read()

            ext = ''
            path = urlparse.urlparse(img).path
            pos = path.rfind('.')
            if pos > 0:
                ext = path[pos:]
            fname = translit(brand) + '_' + translit(name) + ('_%d' % i) + ext

            open(img_dir + '/' + fname, 'wb+').write(content)
            flist.append( kBaseUrl + fname )
        except Exception, e:
            print >> sys.stderr, "Can't download image '%s', exception '%s'" % (img, str(e))
            raise
            continue
    return flist

#-------------------------------------------------
norm_re1 = re.compile(u'\r\n\t', flags=re.UNICODE)
norm_re2 = re.compile(u'\s+', flags=re.UNICODE)
def norm_text(txt):
    txt = norm_re1.sub(' ', txt)
    txt = norm_re2.sub(' ', txt)
    return txt

#-------------------------------------------------
def Dl(rules, images_dir):
    try:
        print >> sys.stderr, "creating dir"
        os.mkdir(images_dir)
    except Exception, e:
        print >> sys.stderr, "can't create, exc: '%s'" % str(e)
        pass

    r = rules   # shorten alias

    price_norm_re = re.compile(u"[ '`]", flags=re.UNICODE)

    Prod.PrintCSVTitle()

    for (category, front_url) in r.urls:
        print >> sys.stderr, "Downloading '%s'" % front_url
        try:
            tree = lxml.html.parse(front_url)
        except Exception, e:
            print >> sys.stderr, "Can't open url, exception: '%s'" % str(e)
            continue

        prod_list = tree.getroot().xpath(r.prod_div)
        print >> sys.stderr, " - found %d products" % len(prod_list)

        n_prod = 0
        for p in prod_list:
            n_prod += 1
            print >> sys.stderr, " . downloading product #%d" % n_prod

            prod = Prod()
            prod.category = category

            try:
                prod.url         = norm_url( front_url, p.xpath(r.href)[0].get('href') )
                prod.price       = price_norm_re.sub( '', p.xpath(r.price)[0].text )
                prod.title       = norm_text( p.xpath(r.title)[0].text )
            except Exception, e:
                print >> sys.stderr, "Error get prod, exception: '%s'" % str(e)
                raise
                continue

            # load product's page
            try:
                prod_tree = lxml.html.parse(prod.url)
            except:
                print >> sys.stderr, "Can't open product-page, exception: '%s'" % str(e)
                continue

            p = prod_tree.getroot().xpath(r.prod_page_div)[0]
            # parse characteristics
            try:
                prod.desc = norm_text( p.xpath(r.desc)[0].text_content() )
                prod.brand = norm_text( p.xpath(r.brand)[0].text )
                prod.material = norm_text( p.xpath(r.material)[0].text )
                prod.color = norm_text( p.xpath(r.color)[0].text )
                prod.podkladka = norm_text( p.xpath(r.podkladka)[0].text )
                prod.dimensions = norm_text( p.xpath(r.dimensions)[0].text )
                prod.size = norm_text( p.xpath(r.size)[0].text )
            except Exception, e:
                print >> sys.stderr, "WARNING: Error parse characteristics, exception: '%s'" % str(e)

            # parse images
            try:
                images = p.xpath(r.images)
                prod.images = [norm_url(front_url, x.get('href')) for x in images]

                print >> sys.stderr, "   downloading product's images"
                prod.images = download_images(images_dir, prod.images, prod.brand, prod.title)

                prod.prod_page = translit(prod.brand) + '-' + translit(prod.title)
            except Exception, e:
                print >> sys.stderr, "Error parse images, exception: '%s'" % str(e)
                raise
                continue

            prod.Print()
            '''
            if n_prod > 19:
                sys.exit(0)
            '''


Dl( Rules_fullbags_ru(), images_dir = './images' )



#========================================================================================================
# Autodetector
#========================================================================================================
"""
def AutoDetectStoreFront(urls):
    price_re = re.compile(u'[$]?\s?[1-9][0-9]{,2}(\s?[0-9]{3})*\s?(р.|руб.|рублей|rur|rub|usd|eur)?', flags=re.UNICODE)

    storefront = []

    for (category, url) in urls:
        print >> sys.stderr, url

        tree = lxml.html.parse(url)
        elems = [x for x in tree.getroot().iter('div', 'tr', 'td', 'span')]
        print >> sys.stderr, "elements: %d" % len(elems)

        attrs_list = ['id', 'class']
        for attr in attrs_list:
            # сортим по атрибуту
            print >> sys.stderr, ' - sorting by attr "%s"' % attr
            els = sorted(elems, key=lambda x: x.get(attr))

            # ищем группы тегов с одинаковыми атрибутами
            print >> sys.stderr, ' - selecting groups'
            kMinGroupSize = 5
            attr_groups = []

            group = []
            el = None
            el_1st = None
            attr_val = None
            attr_val_1st = None
            parent = None
            parent_1st = None
            z = 0
            while z < len(els):
                el = els[z]
                z += 1

                attr_val = el.get(attr)
                if attr_val == None:
                    continue

                parent = el.getparent()
                if attr_val != attr_val_1st: #  or not parent is parent_1st:
                    if len(group) >= kMinGroupSize:     # не маленькая группа? сохраняем
                        attr_groups.append( (el_1st, parent_1st, attr, attr_val_1st, group) )
                    group = []
                    el_1st = el
                    attr_val_1st = attr_val
                    parent_1st = parent

                group.append( el )

            # - добавляем финальную группу, если с ней всё ок
            if len(group) >= kMinGroupSize:
                attr_groups.append( (el_1st, parent, attr, attr_val, group) )

            print >> sys.stderr, " - found %d groups" % len(attr_groups)

            # идём по группам, считаем, сколько картинок и цен нашли в дочерних элементах
            print >> sys.stderr, ' - detecting store-front tags'
            for (el, parent, attr, attr_val, group) in attr_groups:
                img_found = 0
                price_found = 0
                img_els = []
                price_els = []
                for elem in group:
                    # обходим всех детей, ищем среди них картинки и цены внутри текста
                    for child in elem.iter():
                        if child.tag == 'img':
                            img_found += 1
                        if child.text:
                            text = child.text.strip().lower()
                            if price_re.match(text) != None:
                                price_found += 1

                # если цен и картинок среди детей не меньше, чем самих тегов группы, считаем, что
                # это потенциальные элементы витрины
                if price_found >= len(group) and img_found >= len(group):
                    storefront.append( (el, parent, attr, attr_val, group, img_els, price_els) )

    return storefront

storefront = AutoDetectStoreFront(urls)

print >> sys.stderr, "Found groups: %d" % len(storefront)
for (elem, parent, attr, attr_val, group, img_els, price_els) in storefront:
    print " - parent: <%s id='%s' class='%s'> -> children:<%s %s='%s'>" % \
          (parent.tag, parent.get('id'), parent.get('class'), \
           elem.tag, attr, attr_val)
    '''
    for el in group:
        print "\t<%s> -> <%s %s=%s>" % (el.getparent().tag, el.tag, attr, el.get(attr))
    '''

"""

#========================================================================================================
# Selenium
#========================================================================================================

"""
from selenium import webdriver

def det_it(url):
    # TODO:
    #   - handle 404,
    #   - handle timeouts
    storefront = []
    try:
        br = webdriver.Firefox()
        br.get(url)

        tag2elems = []

        tags_list = ['div', 'tr', 'td', 'span']

        for tag in tags_list:
            print >> sys.stderr, "selecting tags '%s'" % tag
            elems = [(x.get_attribute('id'), \
                      x.get_attribute('class'), \
                      x) \
                     for x in br.find_elements_by_tag_name(tag)]
            tag2elems.append( (tag, elems) )

        '''
        общий алгоритм такой:
            - сортим все найденные теги по атрибутам: сначала по id, потом по class;
            - затем выбираем достаточно объёмные группы таких тегов, сгруппированных
              по одному и тому же атрибуту;
            - если у всех элементов группы была найдена потецниальная цена и картинка,
              считаем, что это элементы витрины.
        '''
        price_re = re.compile(u'[$]?\s?[1-9][0-9]{,2}(\s?[0-9]{3})*\s?(р.|руб.|рублей|rur|rub|usd|eur)', flags=re.UNICODE)

        for (tag, elems) in tag2elems:
            for attr_i in range(0, 2):
                print >> sys.stderr, "--- parsing tag %s attr %d" % (tag, attr_i)
                if len(elems) == 0:
                    continue

                # сортим по атрибуту
                elems = sorted(elems, key=lambda x: x[attr_i])

                # группируем по атрибутам, выкидываем группы меньше kMinGroupSize элементов
                kMinGroupSize = 5
                attr_groups = []

                attr_1st = None
                parent_1st = None
                group = []
                z = 0
                while z < len(elems):
                    el = elems[z]
                    z += 1

                    attr = el[attr_i]
                    parent = el[2].parent
                    if attr != attr_1st or parent != parent_1st:
                        if len(group) >= kMinGroupSize:     # не маленькая группа? сохраняем
                            attr_groups.append( (attr, group) )
                        group = []
                        attr_1st = attr
                        parent_1st = parent

                    group.append( el )

                # - добавляем финальную группу, если с ней всё ок
                if len(group) >= kMinGroupSize:
                    attr_groups.append( (attr, group) )

                print >> sys.stderr, "found %d groups" % len(attr_groups)

                # идём по группам, считаем, сколько картинок и цен нашли в дочерних элементах
                for (attr, group) in attr_groups:
                    img_found = 0
                    price_found = 0
                    for elem in group:
                        # обходим всех детей, ищем среди них картинки и цены внутри текста
                        children = elem[2].find_elements_by_xpath('./*')
                        for child in children:
                            if child.tag_name.lower() == 'img':
                                img_found += 1
                            text = child.text.strip().lower()
                            if price_re.match(text) != None:
                                price_found += 1
                    # если цен столько же, сколько элементов, а картинок не меньше, считаем, что
                    # это потенциальные элементы витрины
                    print >> sys.stderr, "attr='%s', group volume=%d, price_found=%d, img_found=%d" % (attr, len(group), price_found, img_found)
                    if price_found >= len(group) and img_found >= len(group):
                        storefront.append( group )

        # sort by id
        # sort by class
        #   - for all elemns with the same id/class
        #       - is there any image presented between elem's children?
        #       - is there any price presented between elem's children?
        #   - yes -> potential good
    except Exception, e:
        print >> sys.stderr, "webdriver exception '%s'" % str(e)
        return None

    return storefront


sf = det_it('http://www.bestwatch.ru/models.phtml?min=0&max=10000000&x=320&y=100&pages=1')
if sf != None:
    i = 0
    for sfront in sf:
        i += 1
        print >> sys.stderr, "store front %d" % i
        for (e_id, e_class, elem) in sfront:
            print >> sys.stderr, "\t<%s id=%s class=%s" % (elem.tag_name, e_id, e_class)

"""
