from typing import List
from time import sleep
from xml.etree import ElementTree
from urllib import parse
from random import sample
from itertools import cycle

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from chromedriver_binary import add_chromedriver_to_path
import requests


class AutoNiconico:
    def __init__(self):
        add_chromedriver_to_path()
        self.driver = webdriver.Chrome()

    def play(self, url):
        self.driver.get(url)

        self.click_play_pause_button()

        try:
            self.driver.find_element_by_class_name('VideoAdContainer')
        except Exception as e:
            return

        sleep(7.5)

        try:
            ad_frame = self.driver.find_element_by_xpath('//*[@id="IMALinearView"]/div[1]/iframe')
            self.driver.switch_to.frame(ad_frame)
            skip_button = self.driver.find_element_by_class_name('videoAdUiRedesignedSkipButton')
            skip_button.click()
        except NoSuchElementException:
            pass
        finally:
            self.driver.switch_to.parent_frame()

    def click_play_pause_button(self):
        try:
            self.driver.find_element_by_class_name('PlayerPlayButton').click()
        except NoSuchElementException:
            self.driver.find_element_by_class_name('PlayerPauseButton').click()

    def get_duration(self):
        duration_panel = self.driver.find_element_by_class_name('PlayerPlayTime-duration')
        return duration_panel.text

    def get_playtime(self):
        playtime_panel = self.driver.find_element_by_class_name('PlayerPlayTime-playtime')
        return playtime_panel.text

    def is_ended(self):
        return self.get_duration() == self.get_playtime()

    def get_urls_from_ranking(self, url) -> List[str]:
        pr = parse.urlparse(url)
        d = parse.parse_qs(pr.query)
        d['rss'] = ["2.0"]
        url = pr.scheme + '://' + pr.netloc + pr.path + '?' + '&'.join([f'{k}={",".join(v)}' for k, v in d.items()])
        res = requests.get(url)
        root = ElementTree.fromstring(res.text)
        items = root[0][10:]
        link = 1

        return [i[link].text for i in items]

    def play_ranking(self, url, loop=True, shuffle=False):
        urls = self.get_urls_from_ranking(url)

        playlist_p = range(len(urls))
        if shuffle:
            playlist_p = sample(playlist_p, len(urls))
        if loop:
            playlist_p = cycle(playlist_p)

        playlist_p = iter(playlist_p)

        while True:
            url_p = urls[next(playlist_p)]

            self.play(url_p)

            while not self.is_ended():
                sleep(0.9)


if __name__ == '__main__':
    import sys
    try:
        url = sys.argv[1]
    except IndexError:
        sys.stderr.write(f'Usage: python {sys.argv[0]} ランキングのURL [-l --loop] [-s --shuffle]')
        exit(1)
    loop = '--loop' in sys.argv or '-l' in sys.argv
    shuffle = '--shuffle' in sys.argv or '-s' in sys.argv
    niconico = AutoNiconico()
    niconico.play_ranking(url, loop=loop, shuffle=shuffle)
