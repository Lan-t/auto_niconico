from typing import List
from time import sleep, strptime
from xml.etree import ElementTree
from urllib import parse
from random import sample
from itertools import cycle

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from chromedriver_binary import add_chromedriver_to_path
import requests


class AutoNiconico:
    def __init__(self):
        add_chromedriver_to_path()
        self.driver = webdriver.Chrome()

    def login(self, username='', password=''):
        self.driver.get('https://account.nicovideo.jp/login')
        username_input = self.driver.find_element_by_id('input__mailtel')
        password_input = self.driver.find_element_by_id('input__password')

        username_input.send_keys(username)
        password_input.send_keys(password)

        if username and password:
            self.driver.find_element_by_id('login__submit').click()
        else:
            while True:
                p = parse.urlparse(self.driver.current_url)
                if p.netloc != 'account.nicovideo.jp':
                    break

    def play(self, url, comment_off=True, fullscreen=False):
        self.driver.get(url)

        self.click_play_pause_button()

        self.skip_ad()

        if comment_off and self.comment_is_on():
            self.must_click(self.click_comment_on_off_button)
        if fullscreen and not self.fullscreen_is_on():
            self.must_click(self.click_fullscreen_button)

    def skip_ad(self, frame_timeout=3, click_timeout=3):
        t = 0
        while True:
            try:
                ad_frame = self.driver.find_element_by_xpath('//*[@id="IMALinearView"]/div[1]/iframe')
            except NoSuchElementException:
                sleep(0.1)
                t += 0.1
                if t >= frame_timeout:
                    # print('フレームがない')
                    return None
                continue
            break
        if not self.mute_is_on():
            self.click_mute_button()
        self.driver.switch_to.frame(ad_frame)
        try:
            sleep(click_timeout)
            skip_button = self.driver.find_element_by_class_name('videoAdUiRedesignedSkipButton')
        except NoSuchElementException:
            # print('スキップボタンない')
            self.driver.switch_to.parent_frame()
            while not self.ad_is_ended():
                sleep(0.1)
        else:
            self.must_click(skip_button.click)
            self.driver.switch_to.parent_frame()

        if self.mute_is_on():
            self.click_mute_button()
        return True

    def click_play_pause_button(self):
        try:
            self.driver.find_element_by_class_name('PlayerPlayButton').click()
        except NoSuchElementException:
            self.driver.find_element_by_class_name('PlayerPauseButton').click()

    def click_comment_on_off_button(self):
        self.driver.find_element_by_class_name('CommentOnOffButton').click()

    def click_fullscreen_button(self):
        try:
            self.driver.find_element_by_class_name('DisableFullScreenButton').click()
        except NoSuchElementException:
            self.driver.find_element_by_class_name('EnableFullScreenButton').click()

    def click_mute_button(self):
        try:
            self.driver.find_element_by_class_name('MuteVideoButton').click()
        except NoSuchElementException:
            self.driver.find_element_by_class_name('UnMuteVideoButton').click()

    def must_click(self, click_method):
        while True:
            try:
                click_method()
            except ElementNotInteractableException:
                sleep(0.1)
                continue
            break

    def get_duration(self):
        duration_panel = self.driver.find_element_by_class_name('PlayerPlayTime-duration')
        try:
            return strptime(duration_panel.get_attribute('innerHTML'), '%M:%S')
        except ValueError:
            print('error')
            return strptime('59:59', '%M:%S')

    def get_playtime(self):
        playtime_panel = self.driver.find_element_by_class_name('PlayerPlayTime-playtime')
        try:
            return strptime(playtime_panel.get_attribute('innerHTML'), '%M:%S')
        except ValueError:
            print('error')
            return strptime('00:00', '%M:%S')

    def video_is_ended(self):
        return self.get_duration() <= self.get_playtime()

    def ad_is_ended(self, frame_timeout=1):
        t = 0
        while True:
            try:
                ad_frame = self.driver.find_element_by_xpath('//*[@id="IMALinearView"]/div[1]/iframe')
            except NoSuchElementException:
                if t >= frame_timeout:
                    # print('フレームがない')
                    return True
                sleep(0.1)
                t += 0.1
                continue
            break

        return not ad_frame.is_displayed()

    def comment_is_on(self):
        try:
            self.driver.find_element_by_class_name('CommentOnOffButton-iconShow')
        except NoSuchElementException:
            return True
        else:
            return False

    def mute_is_on(self):
        try:
            self.driver.find_element_by_class_name('MuteVideoButton')
        except NoSuchElementException:
            return True
        else:
            return False

    def fullscreen_is_on(self):
        try:
            self.driver.find_element_by_class_name('DisableFullScreenButton').click()
        except NoSuchElementException:
            return False
        else:
            return True

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

    def play_ranking(self, url, loop=True, shuffle=False, comment_off=True, fullscreen=True):
        urls = self.get_urls_from_ranking(url)

        playlist_p = range(len(urls))
        if shuffle:
            playlist_p = sample(playlist_p, len(urls))
        if loop:
            playlist_p = cycle(playlist_p)

        playlist_p = iter(playlist_p)

        while True:
            try:
                url_p = urls[next(playlist_p)]
            except StopIteration:
                break

            self.play(url_p, comment_off=comment_off, fullscreen=fullscreen)

            while not self.video_is_ended():
                sleep(0.1)


if __name__ == '__main__':
    import sys

    try:
        url = sys.argv[1]
    except IndexError:
        sys.stderr.write(
            f'Usage: python {sys.argv[0]} ランキングのURL [-l --loop] [-s --shuffle] [-c --no-comment] [-f --fullscreen] [-a --login] [--user=username] [--password=password]')
        exit(1)
    argv = set(sys.argv)
    loop = '--loop' in argv or '-l' in argv
    shuffle = '--shuffle' in argv or '-s' in argv
    no_comment = '--no-comment' in argv or '-c' in argv
    login = '--login' in argv or '-a' in argv
    fullscreen = '--fullscreen' in argv or '-f' in argv
    user = ''
    password = ''
    for arg in sys.argv:
        if arg[:7] == '--user=':
            user = arg[7:]
            login = True
        if arg[:11] == '--password=':
            password = arg[11:]
            login = True

    niconico = AutoNiconico()
    if login:
        niconico.login(username=user, password=password)
    niconico.play_ranking(url, loop=loop, shuffle=shuffle, comment_off=no_comment, fullscreen=fullscreen)
