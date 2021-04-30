#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 10:12:55 2021

@author: nickj
"""
import os
import requests
import wget
import time
import threading
from gi.repository import GObject, GdkPixbuf
from gi.repository import Notify

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
        # print(time)
        
        link = article.attrib['data-href']
        
        # if(len(time) == 2): # ignore top articles
        if(time != ''):
            props[ID] = [
                title,
                image,
                price,
                time,
                link]
        
    # print(articles[0].keys())
    # print(articles[0].xpath('div/div/h2/a[@class="ellipsis"]/text()'))
    
    # print(titles)

    return props
    
class Scraper:
    def __init__(self):
        self.all_props = {}
        Notify.init("ebay")
        
    def start(self):
        self.scraper = threading.Thread(target=self.scrape)
        self.scraper.start()
        
    def scrape(self, interval = 60):
        self.scraping = True
        while self.scraping:
            props = {}
            props.update(getArticles(getResponse('zelda')))
            props.update(getArticles(getResponse('metroid')))
            props.update(getArticles(getResponse('nintendo 64')))
            props.update(getArticles(getResponse('n64')))
            props.update(getArticles(getResponse('game boy')))
            props.update(getArticles(getResponse('mole mania')))
            
            new_articles = set(props.keys()) - set(self.all_props.keys())
            # print(new_articles)
            # print()
            self.all_props.update(props)
            
            for key in new_articles:
                print('%s: %s' % (self.all_props[key][3], self.all_props[key][0]))
                # print(all_props)
                image_url  = self.all_props[key][1]
                image_file = os.path.dirname(os.path.realpath(__file__))+'/thumbnail.jpeg'
                print(image_url)
                if(image_url != ''):
                    wget.download(image_url, image_file)
                #     pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_file)
                #     n.set_image_from_pixbuf(pixbuf)
                    n = Notify.Notification.new(self.all_props[key][3], self.all_props[key][0], image_file)
                    n.show()
            
            time.sleep(interval)

if(__name__=='__main__'):
    scraper = Scraper()
    scraper.start()
        

    
    

    from flask import Flask, render_template
    app = Flask(__name__)



    @app.route('/')
    def hello_world():
        # props = {}
        # props.update(getArticles(getResponse('zelda')))
        # props.update(getArticles(getResponse('metroid')))
        # props.update(getArticles(getResponse('nintendo 64')))
        # props.update(getArticles(getResponse('n64')))
        # props.update(getArticles(getResponse('game boy')))
        # props.update(getArticles(getResponse('mole mania')))
        
        props = scraper.all_props
        # print('sort')
        def sortkey(key):
            return props[key][3]
        sorted_keys = sorted(props, key=sortkey, reverse=True)
        # print(sorted_keys)
        sorted_dict = {w:props[w]for w in sorted_keys}
        
        return render_template('index.html', props=sorted_dict)
    
    app.run(host='localhost', port=8080)
