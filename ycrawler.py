#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import logging
import argparse
import re
import os

from html.parser import HTMLParser

parser = argparse.ArgumentParser(
    description="Asynchronous feedline for news site. default https://news.ycombinator.com")
parser.add_argument(
    '--period',
    type=int,
    default=360,
    help="Number of seconds between poll"
)
parser.add_argument(
    '--url',
    type=str,
    default="https://news.ycombinator.com",
    help='url site'
)
parser.add_argument(
    '--dir',
    type=str,
    default='./NEWS'
)

URL_EXCEPTIONS = [r'^bookmarklet.html',]

class HtmlParser(HTMLParser):
    def __init__(self, html_text, args, url = ''):
        self.links = []
        self.args = args
        self.html_text = html_text
        self.url = url
        super().__init__()
        self.feed(self.html_text)
    
    def handle_starttag(self, tag, attrs):
        argum = {key:val for key, val in self.args.items() if key not in ('tag','par_find')}
        flag = False if argum else True
        if tag == self.args['tag']:
            ind, pos = 0, 0
            for attr in attrs:
                if (attr) in argum.items():
                    flag = True
                if flag and self.args['par_find'] in attr:
                    flag = True
                    pos = ind
                ind += 1
            else:
                if flag:
                    data = self.url + '/' + attrs[pos][1] if re.search('^item\?id', attrs[pos][1]) else attrs[pos][1]
                    for excpt in URL_EXCEPTIONS:
                        if not re.search(excpt, attrs[pos][1]):
                            self.links.append(data)


def save_page(path, data):
    filename = path
    with open(filename, 'wb') as file:
        file.write(data)


async def fetch_save(client, url, fsave, path = './NEWS'):
    try:
        async with client.get(url, allow_redirects=True) as resp:
            #assert resp.status == 200
            data = await resp.read()
            if fsave:
                simbs = [ '\\', '/', ':', '*', '?', '"', '<', '>', '|', '+', '!', '%', '@']
                for simb in simbs:
                    if simb in url:
                        url = url.replace(simb, '')
                path = path + '/' + url
                save_page(path, data)
            return await resp.text()
    except Exception as e:
        log.info('Error ({}) load {}'.format(e, url))
    

def make_dir(path):
    """
    """
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except OSError:
            log.error("Create directories {} failed".format(path))


async def main(opt):
    list_uploaded_news = []
    tasks_news = []
    task_comments = []
    tm = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=tm) as client:
        while True:
            html_text = await fetch_save(client, opt.url, False)
            pars_url_news = HtmlParser(html_text, {'tag':'a', 'class': 'storylink', 'par_find':'href',}, opt.url)
            pars_id_news = HtmlParser(html_text, {'tag':'tr', 'class': 'athing', 'par_find':'id'}, opt.url)
            make_dir(opt.dir)
            pars_url_news_links, pars_id_news_links= [], []
            for index in range(len(pars_id_news.links)):
                if pars_id_news.links[index] not in list_uploaded_news:
                    pars_id_news_links.append(pars_id_news.links[index])
                    pars_url_news_links.append(pars_url_news.links[index])

            list_uploaded_news += pars_id_news_links 
            for inews in range(len(pars_url_news_links)):
                path = opt.dir + '/' + 'id_news_' + pars_id_news_links[inews]
                make_dir(path)
                task = asyncio.create_task(fetch_save(client, pars_url_news_links[inews], True, path))
                tasks_news.append(task)
                url_comment = opt.url + '/' + 'item?id=' + pars_id_news_links[inews]
                path_comments = path + '/' + 'comments'
                make_dir(path_comments)
                html_text = await fetch_save(client, url_comment, False)
                pars_url_comment = HtmlParser(html_text, {'tag':'a', 'rel': 'nofollow', 'par_find':'href',}, opt.url)
                for comment in pars_url_comment.links:
                    #print(comment)
                    task_com = asyncio.create_task(fetch_save(client, comment, True, path_comments))
                    task_comments.append(task_com)
                await asyncio.gather(*task_comments)
            await asyncio.gather(*tasks_news)
            print('1')
            await asyncio.sleep(opt.period)
            


if __name__ == "__main__":
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.ERROR, format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='[%H:%M:%S]')
    log = logging.getLogger()
    try:    
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass