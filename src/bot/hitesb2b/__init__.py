import logging
from datetime import datetime
from functools import lru_cache
from os import getenv
from time import sleep

from dateparser import parse
from googletrans import Translator
from python3_anticaptcha import NoCaptchaTaskProxyless
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as Ec
from selenium.webdriver.support.wait import WebDriverWait as Wait


class LoggerMixin:

    @property
    def log(self):
        return logging.getLogger(self.__class__.__name__)


class WebDriverWait(Wait, LoggerMixin):

    def click_until_element_available_to_show(self, element_to_click: callable, element_to_wait_for, timeout: int = 10):
        prev_timeout = timeout
        self._timeout = timeout
        while True:
            element_to_click()
            try:
                self.until(element_to_wait_for)
                break
            except TimeoutException:
                pass
        self._timeout = prev_timeout


class HitesB2bLoginFailedException(Exception):
    pass


def solve_captcha(site_key, page_url, key):
    user_answer = NoCaptchaTaskProxyless.NoCaptchaTaskProxyless(anticaptcha_key=key) \
        .captcha_handler(websiteURL=page_url,
                         websiteKey=site_key)
    while 1:
        if user_answer.get("errorCode") == "ERROR_ZERO_BALANCE":
            raise ValueError("Captcha Account has zero or negative balance!")

        if user_answer.get('solution') and user_answer.get('errorId') == 0:
            return user_answer.get('solution').get('gRecaptchaResponse')
        else:
            return solve_captcha(site_key, page_url, key)


class HitesB2bMonth:

    def __init__(self, driver: webdriver.Chrome, select_opening_date: bool = True):
        self._parent = driver
        if select_opening_date:
            self._parent.find_elements_by_css_selector(
                '.popupContent .v-window-wrap .v-horizontallayout .v-datefield .v-datefield-button')[0].click()
        else:
            self._parent.find_elements_by_css_selector(
                '.popupContent .v-window-wrap .v-horizontallayout .v-datefield .v-datefield-button')[1].click()

    @property
    def previous_button(self):
        return self._parent.find_element_by_css_selector('.v-button-prevmonth')

    @property
    def next_button(self):
        return self._parent.find_element_by_css_selector('.v-button-nextmonth')

    def open(self):
        try:
            self._parent.find_element_by_css_selector(
                '#PID_VAADIN_POPUPCAL .v-datefield-calendarpanel-month span')
            return
        except NoSuchElementException:
            pass

        self._parent.wait.click_until_element_available_to_show(self._parent.find_element_by_css_selector(
            '.popupContent .v-window-wrap .v-horizontallayout .v-datefield .v-datefield-button').click,
                                                                Ec.visibility_of_element_located((By.CSS_SELECTOR,
                                                                                                  '#PID_VAADIN_POPUPCAL .v-datefield-calendarpanel-month span')))

    @property
    def current_month(self) -> datetime:
        self.open()
        heading = self._parent.find_element_by_css_selector(
            '#PID_VAADIN_POPUPCAL .v-datefield-calendarpanel-month span')
        translator = Translator()
        result = translator.translate(heading.text, dest='en')
        return parse(result.text)

    def go_to_at_month(self, date):
        while True:
            if self.current_month.month < date.month:
                self.next_button.click()
                # self._parent.save_screenshot('fk.png')
            elif self.current_month.month > date.month:
                self.previous_button.click()
                # self._parent.save_screenshot('fk.png')
            elif self.current_month.month == date.month:
                break
            sleep(1)

        elements = filter(lambda x: int(x.text.strip()) == date.day,
                          self._parent.find_elements_by_css_selector('#PID_VAADIN_POPUPCAL td[role="gridcell"]'))
        next(elements).click()

    def find_and_click_at_date(self, date):
        if not isinstance(date, datetime):
            date = parse(date)
        self.go_to_at_month(date)


class RequestFilterBtn:

    def __init__(self, _parent: 'HitesB2b', is_first: bool):
        self._parent = _parent
        self._is_first = is_first

    def wait(self):
        if self._is_first:
            self._parent.wait.until(
                Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button-btn-filter-search'))).click()
        else:
            self._parent.wait.until(
                Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button-btn-filter-search'))).click()


class Hitesb2bMenuChooser:

    def __init__(self, driver: 'HitesB2b', is_first: bool = True):
        self._parent = driver
        self._is_first = is_first

        self._parent.get(self._parent.MAIN_URL)

    def select_menu(self):
        if self._is_first:
            self._parent.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-menubar-menuitem')))
            self._parent.find_elements_by_css_selector('.v-menubar-menuitem')[2].click()
            sleep(3)
            self._parent.find_elements_by_css_selector('.v-menubar-menuitem')[7].click()
        else:
            self._parent.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-menubar-menuitem')))
            self._parent.find_elements_by_css_selector('.v-menubar-menuitem')[3].click()
            sleep(2.4)
            self._parent.find_elements_by_css_selector('.v-menubar-menuitem')[8].click()

    def request_generate_btn(self):
        if self._is_first:
            self._parent.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button')))
            self._parent.wait.until(lambda x: len(self._parent.find_elements_by_css_selector('.v-button')) > 7)
            self._parent.find_elements_by_css_selector('.v-button')[7].click()
            self._parent.wait.until(
                Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button-btn-filter-search'))).click()
        else:
            self._parent.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button')))
            self._parent.wait.until(lambda x: len(self._parent.find_elements_by_css_selector('.v-button')) > 4)
            self._parent.find_elements_by_css_selector('.v-button')[4].click()
            self._parent.wait.until(
                Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button-btn-filter-search'))).click()


class HitesB2b(webdriver.Chrome, LoggerMixin):
    MAIN_URL = 'https://www.hitesb2b.com/BBRe-commerce/main'

    @lru_cache()
    def get_wait_driver(self, timeout: int = 60):
        return WebDriverWait(self, timeout)

    @property
    @lru_cache()
    def wait(self):
        return self.get_wait_driver()

    def __del__(self):
        try:
            self.close()
            self.quit()
        except:
            pass

    def __init__(self, api_key: str = None, download_path: str = "/code/static/downloads", *args, **kwargs):
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-infobars')
        options.add_argument("--headless")
        options.add_argument("window-size=1280,1696")
        options.add_argument("-js-flags=--expose-gc")
        options.add_experimental_option('prefs', {
            'download.default_directory': download_path,
            "download.prompt_for_download": False,
            "directory_upgrade": True
        })
        super().__init__(chrome_options=options, *args, **kwargs)
        if api_key is None:
            self.anti_captcha_key = getenv('ANTI_CAPTCHA_API_KEY')
        else:
            self.anti_captcha_key = api_key

    def login(self, username: str, password: str):
        self.log.info('opening url')
        self.get(self.MAIN_URL)
        self.log.info('entering login')
        username_element = self.wait.until(Ec.presence_of_element_located((By.NAME, 'username')))
        username_element.send_keys(username)
        self.find_element_by_name('password').send_keys(password)

        print("Solving captcha.")
        token = solve_captcha("6Le6POkUAAAAAPrhWc5b14fntw6TCU1tRgEKaLnk", self.current_url, self.anti_captcha_key)
        self.execute_script("document.getElementsByName('g-recaptcha-response')[0].value = '{}'".format(token))
        self.find_element_by_name('login').click()

        if self.title.strip() != '| B2B Hites |':
            raise HitesB2bLoginFailedException("Login failed for user: %s" % username)
        print('logging successful')

        return self

    def _download(self):
        # wait for file to download
        self.wait.until(Ec.presence_of_element_located((By.CSS_SELECTOR, '.v-link.v-widget a')))
        link = self.find_elements_by_css_selector('.v-link.v-widget a')[0]
        url = link.get_attribute('href')
        self.get(url)

        return url.split("/")[-1]

    def download_third_file(self):
        self.get(self.MAIN_URL)
        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-menubar-menuitem')))
        self.find_elements_by_css_selector('.v-menubar-menuitem')[2].click()
        sleep(3)
        self.find_elements_by_css_selector('.v-menubar-menuitem')[7].click()

        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button')))
        self.wait.until(lambda x: len(self.find_elements_by_css_selector('.v-button')) > 7)
        self.find_elements_by_css_selector('.v-button')[7].click()
        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button-btn-filter-search'))).click()

        # wait for element to visible.
        dl = self.wait.until(Ec.element_to_be_clickable((By.XPATH,
                                                         '//*[@id="BBRecommercemain-1422079705"]/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[3]/div/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div/div/div/div[1]/div/div/div[3]/div/div[1]/div')))
        dl.click()
        self.wait.click_until_element_available_to_show(dl.click, Ec.element_to_be_clickable(
            (By.CSS_SELECTOR, '.popupContent .v-slot-action-button')))
        self.wait.click_until_element_available_to_show(
            self.find_elements_by_css_selector('.popupContent .v-slot-action-button')[1].click,
            Ec.visibility_of_element_located((By.CSS_SELECTOR, '.popupContent .v-window-wrap')))

        # grab its information
        self.find_element_by_css_selector(
            '.v-align-center .v-select-optiongroup .v-select-option:not(.v-select-option-selected)').click()
        self.find_element_by_css_selector('.v-horizontallayout .v-slot-btn-generic .v-button').click()
        return self._download()

    def download_first_file(self, start_date: str, end_date: str):
        self.get(self.MAIN_URL)
        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-menubar-menuitem')))
        self.find_elements_by_css_selector('.v-menubar-menuitem')[2].click()
        sleep(3)
        self.find_elements_by_css_selector('.v-menubar-menuitem')[7].click()

        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button')))
        self.wait.until(lambda x: len(self.find_elements_by_css_selector('.v-button')) > 7)
        self.find_elements_by_css_selector('.v-button')[7].click()
        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button-btn-filter-search'))).click()

        # wait for element to visible.
        dl = self.wait.until(Ec.element_to_be_clickable((By.XPATH,
                                                         '//*[@id="BBRecommercemain-1422079705"]/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[3]/div/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div/div/div/div[1]/div/div/div[3]/div/div[1]/div')))
        dl.click()
        self.wait.click_until_element_available_to_show(dl.click, Ec.element_to_be_clickable(
            (By.CSS_SELECTOR, '.popupContent .v-slot-action-button')))
        self.wait.click_until_element_available_to_show(
            self.find_elements_by_css_selector('.popupContent .v-slot-action-button')[2].click,
            Ec.visibility_of_element_located((By.CSS_SELECTOR, '.popupContent .v-window-wrap')))

        HitesB2bMonth(self).find_and_click_at_date(start_date)
        HitesB2bMonth(self, False).find_and_click_at_date(end_date)
        # grab its information
        self.find_element_by_css_selector(
            '.v-align-center .v-select-optiongroup .v-select-option:not(.v-select-option-selected)').click()
        self.find_element_by_css_selector('.v-horizontallayout .v-slot-btn-generic .v-button').click()

        return self._download()

    def download_second(self):
        self.get(self.MAIN_URL)
        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-menubar-menuitem')))
        self.find_elements_by_css_selector('.v-menubar-menuitem')[3].click()
        sleep(2.4)
        self.find_elements_by_css_selector('.v-menubar-menuitem')[8].click()

        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button')))
        self.wait.until(lambda x: len(self.find_elements_by_css_selector('.v-button')) > 4)
        self.find_elements_by_css_selector('.v-button')[4].click()
        self.wait.until(Ec.element_to_be_clickable((By.CSS_SELECTOR, '.v-button-btn-filter-search'))).click()

        dl = self.wait.until(Ec.element_to_be_clickable((By.XPATH,
                                                         '//*[@id="BBRecommercemain-1422079705"]/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[3]/div/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div[1]/div/div/div[3]/div/div[1]')))
        dl.click()
        self.wait.click_until_element_available_to_show(dl.click, Ec.element_to_be_clickable(
            (By.CSS_SELECTOR, '.popupContent .v-slot-action-button')))
        self.wait.click_until_element_available_to_show(
            self.find_elements_by_css_selector('.popupContent .v-slot-action-button')[1].click,
            Ec.visibility_of_element_located((By.CSS_SELECTOR, '.popupContent .v-window-wrap')))
        self.find_element_by_css_selector(
            '.v-align-center .v-select-optiongroup .v-select-option:not(.v-select-option-selected)').click()
        self.find_element_by_css_selector('.v-horizontallayout .v-slot-btn-generic .v-button').click()

        return self._download()
