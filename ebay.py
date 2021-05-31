#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 10:12:55 2021

@author: nickj
"""

from gevent import monkey
monkey.patch_all()

import os
import requests
import wget
import time
import threading
import logging
import geo
import shutil
# from gi.repository import GObject, Gdk, GdkPixbuf
# from gi.repository import Notify

def getResponse(query):
    keywords = query.split(' ')
    url = 'https://www.ebay-kleinanzeigen.de/s-%s/k0' % ('-'.join(keywords))
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}


    x = requests.request(method='GET', url=url, headers=headers)

    # print(x.text)
    return x.text

# with open('test.html', 'w+') as fp:
#     fp.write(x.text)


# import xml.etree.ElementTree as ET
# tree = ET.parse('test.html')
# root = tree.getroot()

from lxml import html


def getArticles(txt):
    # with open('test.html', 'r+') as fp:
        # tree = html.fromstring(fp.read())
    tree = html.fromstring(txt)
    # titles = tree.xpath('//a[@class="ellipsis"]/text()')
    # images = tree.xpath('//div[@class="imagebox srpimagebox"]/@data-imgsrc')

    articles = tree.xpath('//article[@class="aditem"]')

    props = {}

    for article in articles:
        ID = article.attrib['data-adid']
        # print(ID)
        # props

        title = article.xpath('div/div/h2/a[@class="ellipsis"]/text()')
        title = title[0].replace('\n','').strip()
        # print(title)

        image = article.xpath('div/a/div[@class="imagebox srpimagebox"]/@data-imgsrc')
        image = (''.join(image)).replace('\n','').strip()
        # print(image)

        price = article.xpath('div/div/p[@class="aditem-main--middle--price"]/text()')
        price = price[0].replace('\n','').strip()
        # print(price)

        time = article.xpath('div/div/div[@class="aditem-main--top--right"]/text()')
        time = (''.join(time)).replace('\n','').strip()
        time = parseTime(time)
        # print("'%s'" % (time))

        location = article.xpath('div/div/div[@class="aditem-main--top--left"]/text()')
        location = (''.join(location)).replace('\n','').strip()
        # print("'%s'" % (location))
        plz, city = location.split(' ', maxsplit=1)

        link = article.attrib['data-href']

        # if(len(time) == 2): # ignore top articles
        if(time is not None):
            props[ID] = [
                title,
                image,
                price,
                time,
                link,
                plz, city]

    # print(articles[0].keys())
    # print(articles[0].xpath('div/div/h2/a[@class="ellipsis"]/text()'))

    # print(titles)

    return props


import json

def pushbullet_message(title, body, image_url):
    msg = {"type": "file", "title": title, "body": body, "file_type": "image/jpeg", "file_url": image_url}
    TOKEN = 'o.cSoxLeNE6xvVb1XxkldTv9NhZe1QwKOu'
    resp = requests.post('https://api.pushbullet.com/v2/pushes',
                         data=json.dumps(msg),
                         headers={'Authorization': 'Bearer ' + TOKEN,
                                  'Content-Type': 'application/json'})
    if resp.status_code != 200:
        raise Exception('Error',resp.status_code)
    else:
        print ('Message sent')

class Signal:
    def __init__(self):
        self.__funcs = []
    def connect(self, func):
        if(func not in self.__funcs):
            self.__funcs.append(func)
    def disconnect(self, func):
        if(func in self.__funcs):
            self.__funcs.remove(func)
    def emit(self, *args, **kwargs):
        for func in self.__funcs:
            func(*args, **kwargs)

class Scraper:
    def __init__(self, configfile='scraper.json'):
        self.logger = logging.getLogger('Scraper')

        self.configfile = configfile
        self.all_props = {}
        self.newArticles = Signal()
        self.newArticle = Signal()
        self.queries = []
        self.__load(configfile)
        self.scraping = False
        self.postalcode = '81477' # Germany
        self.distance   = 1000    # in km
            # 'zelda', 'metroid', 'mole mania']

    def start(self):
        self.scraper = threading.Thread(target=self.__scrape)
        self.scraper.start()

    def stop(self):
        self.scraping = False
        self.scraper.join()
        self.scraper = None

    def addQuery(self, query):
        if(query not in self.queries):
            self.queries.append(query)
            self.__save(self.configfile)
    def removeQuery(self, query):
        if(query in self.queries):
            self.queries.remove(query)
            self.__save(self.configfile)

    def __load(self, filename):
        if(os.path.exists(filename)):
            with open(filename, 'r+') as fp:
                self.queries = json.load(fp)
    def __save(self, filename):
        with open(filename, 'w+') as fp:
            json.dump(self.queries, fp)

    def __scrape(self, interval = 60, delay = 2):
        print('started')
        self.scraping = True
        while self.scraping:
            props = {}
            start_time = time.time()
            try:
                for query in list(self.queries):
                    self.logger.info('Scrape query "%s"' % (query))
                    props.update(getArticles(getResponse(query)))
                    time.sleep(delay)

                new_articles = set(props.keys()) - set(self.all_props.keys())

                # self.all_props = {}
                self.all_props.update(props)

                self.newArticles.emit(new_articles)
            except Exception as e:
                self.logger.exception(e)

            while time.time() - start_time < interval:
                time.sleep(0.1)
                if(not self.scraping):
                    print('stopped')
                    return
            # time.sleep(interval)
        print('stopped')

class GnomeNotifier:
    def __init__(self, scraper):
        Notify.init("ebay")
        self.scraper = scraper
        scraper.newArticles.connect(self.onNewArticles)

    def onNewArticles(self, new_articles):
        for key in new_articles:
            image_url  = self.scraper.all_props[key][1]
            image_file = os.path.dirname(os.path.realpath(__file__))+'/thumbnail_%s.jpeg' % (key)
            if(image_url != ''):
                wget.download(image_url, image_file)
                n = Notify.Notification.new(str(self.scraper.all_props[key][3]), self.scraper.all_props[key][0], image_file)
                n.show()
                os.remove(image_file)

class PushbulletNotifier:
    def __init__(self, scraper):
        # Notify.init("ebay")
        self.scraper = scraper
        scraper.newArticles.connect(self.onNewArticles)

    def onNewArticles(self, new_articles):
        for key in new_articles:
            title  = self.scraper.all_props[key][0]
            image_url  = self.scraper.all_props[key][1]
            price  = self.scraper.all_props[key][2]
            time  = self.scraper.all_props[key][3]
            link  = 'https://www.ebay-kleinanzeigen.de' + self.scraper.all_props[key][4]

            #image_file = os.path.dirname(os.path.realpath(__file__))+'/thumbnail.jpeg'
            if(image_url != ''):
                title = '%s, %s, %s' % (time, title, price)
                body  = link
                # image_url = self.all_props[key][1]
                pushbullet_message(title, body, image_url)


import datetime
def parseTime(date_time_str):

    try:
        if("Heute" in date_time_str):
            date_time_obj = datetime.datetime.combine(
                datetime.datetime.today(),
                datetime.datetime.strptime(date_time_str, 'Heute, %H:%M').time())
        elif("Gestern" in date_time_str):
            date_time_obj = datetime.datetime.combine(
                datetime.datetime.today() - datetime.timedelta(days=1),
                datetime.datetime.strptime(date_time_str, 'Gestern, %H:%M').time())

        else:
            date_time_obj = datetime.datetime.strptime(date_time_str, '%d.%m.%Y')
    except:
        return None
    else:
        # print('%s --> %s' % (date_time_str, date_time_obj))
        return date_time_obj


if(__name__=='__main__'):

    logging.basicConfig(level=logging.INFO)

    scraper = Scraper()
    scraper.start()

    # gnomeNotifier = GnomeNotifier(scraper)
    # pbNotifier =  PushbulletNotifier(scraper)


    from flask import Flask, render_template, request
    from flask_socketio import SocketIO, emit



    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app, async_mode='gevent')

    @app.route('/', methods=['GET', 'POST'])
    def hello_world():

        #print(request.data)
        print(request.form)
        for command, value in request.form.items():
            if(command=='remove'):
                scraper.removeQuery(value)
            elif(command=='add'):
                scraper.addQuery(value)
            elif(command=='pause'):
                if(scraper.scraping):
                    scraper.stop()
                else:
                    scraper.start()
            elif(command=='distance'):
                scraper.distance = int(value)

        # filter
        props = {name: prop for name, prop in scraper.all_props.items() if geo.getDistance(scraper.postalcode, prop[5]) < scraper.distance}


        def sortkey(key):
            return props[key][3]
        sorted_keys = sorted(props, key=sortkey, reverse=True)
        sorted_dict = {w:props[w]for w in sorted_keys}
        
        

        return render_template('index.html', props=sorted_dict, queries=scraper.queries, scraping=scraper.scraping, update_time=str(datetime.datetime.now()), distance=scraper.distance)

    @socketio.on('my event')
    def handle_my_custom_event(json):
        print('received json: ' + str(json))

    # @socketio.event
    # def my_event(message):
    #     emit('update', {'data': 'got it!'})

    def onUpdate(*args):
        print('emit update')
        socketio.emit( 'my response', str(datetime.datetime.now()))
        # my_event('bla')

    scraper.newArticles.connect(onUpdate)

    # app.run(host='0.0.0.0', port=1234, debug=True)
    socketio.run(app, host='0.0.0.0', port=1234, debug=False)
