from __future__ import annotations
from lxml import html
from urllib.parse import urlparse
from abc import ABC, abstractmethod
import requests
import re
import sys


class HandlerInterface(ABC):

    @abstractmethod
    def set_next(self, handler: HandlerInterface) -> HandlerInterface:
        pass

    @abstractmethod
    def handle(self, url_str: str):
        pass


class Handler(HandlerInterface):
    _next_handler: HandlerInterface

    @abstractmethod
    def handle(self, url_str: str):
        if self._next_handler:
            return self._next_handler.handle(url_str)

        return None

    def set_next(self, next_handler: HandlerInterface) -> HandlerInterface:
        self._next_handler = next_handler
        return next_handler


class HatenaHandler(Handler):
    def is_hatenablog(self, url_str: str) -> bool:
        url = urlparse(url_str)
        return re.search(
            r'(hatenablog\.jp|hatenablog\.com|hatenadiary\.jp|hatenadiary\.com|hateblo\.jp)$',
            url.netloc
        )

    def handle(self, url_str: str) -> str:
        if not self.is_hatenablog(url_str):
            return super().handle(url_str)

        resp = requests.get(url_str)
        tree = html.fromstring(resp.text)
        txts = tree.xpath('//div[contains(@class,"hatenablog-entry")]//text()')
        return [t.strip() for t in txts]


class NoteHandler(Handler):
    def is_note(self, url_str: str) -> str:
        url = urlparse(url_str)
        return re.search(
            r'(note\.com|note\.mu)$',
            url.netloc
        )

    def handle(self, url_str: str) -> str:
        if not self.is_note(url_str):
            return super().handle(url_str)

        resp = requests.get(url_str)
        tree = html.fromstring(resp.text)
        txts = tree.xpath('//div[@data-name="body"]/p/text()')
        return [t.strip() for t in txts]


class OtherHandler(Handler):
    def handle(self, url_str: str) -> str:
        print(url_str, file=sys.stdout)
        return []


def get_links(link: str) -> list[str]:
    resp = requests.get(link)
    tree = html.fromstring(resp.text)
    elems = tree.xpath('//div[@class="link"]/a/@href')
    return elems

if __name__ == "__main__":
    adcs = [
        "https://adventar.org/calendars/704",
        "https://adventar.org/calendars/1005",
        "https://adventar.org/calendars/1463",
        "https://adventar.org/calendars/2117",
        "https://adventar.org/calendars/3293",
        "https://adventar.org/calendars/4349",
        "https://adventar.org/calendars/4206",
        "https://adventar.org/calendars/5350",
        "https://adventar.org/calendars/5135",
        "https://adventar.org/calendars/6617",
        "https://adventar.org/calendars/8181",
    ]

    hatena = HatenaHandler()
    note = NoteHandler()
    other = OtherHandler()

    hatena.set_next(note).set_next(other)

    links = []
    for l in adcs:
        links += get_links(l)
        # for url_str in links:
        #     url = urlparse(url_str)
        #     print(url.netloc)

    for url in links:
        texts = hatena.handle(url)
        if len(texts) == 0: continue
        filtered_texts = list(filter(lambda txt: len(txt) != 0, texts))
        print(filtered_texts)
