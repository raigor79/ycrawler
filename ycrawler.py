#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import logging
import re

from html.parser import HTMLParser

URL_SITE = "https://news.ycombinator.com"
PATH_SAVE_NEW = "./NEWS"
TIME_CYCLE_LOAD_SEC = 60


class HtmlParser(HTMLParser):
    def __init__(self, html_text, tag_str, dict_html_classes):
        self.html_text = html_text
        self.tag = tag_str
        self.dict_classes = dict_html_classes
        self.links = []
        super().__init__()
        self.feed(html_text)

    def handle_starttag(self, tag, attrs):
        if tag == self.tag:
            for attr in attrs:
                if attr[1] == self.dict_classes[list(self.dict_classes.keys())[0]]:
                   self.links.append(attrs[0][1])



async def fetch(client):
    async with client.get(URL_SITE) as resp:
        assert resp.status == 200
        return await resp.text()


async def main():
    async with aiohttp.ClientSession() as client:
        html = await fetch(client)
        pars_html = HtmlParser(html, 'a', {'class':'storylink'})
        print(pars_html.links)
        
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='[%H:%M:%S]')
    log = logging.getLogger()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()