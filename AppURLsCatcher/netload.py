
import queue
import os, sys
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
import threading
import time
from AppURLsCatcher.config import WEBDRIVE_PATH, CHROME_PATH


class WebdriverManager(object):
    interval = 0.00001
    webdrive_path = WEBDRIVE_PATH
    # webdrive_path = "D:\Program Files\CloudForensic\CloudSupport\Bin64\Tool\webdriver\chromedriver.exe"
    chrome_path = CHROME_PATH
    # chrome_path = "D:\Program Files\CloudForensic\\3rdParty\Chrome\chrome.exe"

    def __init__(self, log, screenshot_folder=None, browser_max=5, screenshot=True, timeout=10, headless=True):
        self.log= log
        self.browser_max = browser_max
        self.timeout = timeout
        self.screenshot_folder = screenshot_folder
        self.queue_webdriver = queue.Queue()  ##存放phantomjs进程队列
        self.screenshot = screenshot #默认进行网页截图
        self.headless = headless

    def _init_chrome_driver(self):
        mobile_emulation = {
            "deviceMetrics": {"width": 320, "height": 450, "pixelRatio": 3.0},
        }
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        chrome_options.binary_location = WebdriverManager.chrome_path
        if self.headless:
            chrome_options.add_argument('--headless')
        if os.path.exists(WebdriverManager.webdrive_path):
            cnt = 3
            while cnt > 0:
                try:
                    browser = webdriver.Chrome(executable_path=self.webdrive_path, chrome_options=chrome_options)
                    break
                except WebDriverException as e:
                    self.log.exception('start webdriver failed', exc_info=e)
                    cnt -= 1
            else:
                self.log.info('webdriver start failed three times, quit...')
                return
            browser.implicitly_wait(self.timeout)
        else:
            self.log.error('chrome not exist..., quit.')
            os._exit(1)
        return browser

    def _quit_driver(self, browser):
        try:
            browser.quit()
        except Exception as e:
            self.log.info('browser quit error')

    def open_chromedriver(self):
        """
        多线程开启进程
        :return:
        """

        def open_threading():
            driver = self._init_chrome_driver()
            driver.set_page_load_timeout(self.timeout)
            self.queue_webdriver.put(driver)  # 将phantomjs进程存入队列

        th = []
        for i in range(self.browser_max):
            t = threading.Thread(target=open_threading)
            th.append(t)
        for i in th:
            i.start()
            time.sleep(WebdriverManager.interval)  # 设置开启的时间间隔
        for i in th:
            i.join()

        if self.screenshot:
            if not os.path.exists(self.screenshot_folder):
                os.makedirs(self.screenshot_folder)

        self.log.info("Chrome 开启完成。开启数目：{}".format(self.browser_max))


    def close_chromedriver(self):
        """
        多线程关闭chromedriver对象
        :return:
        """
        th = []

        def close_threading():
            d = self.queue_webdriver.get()
            self._quit_driver(d)

        for i in range(self.queue_webdriver.qsize()):
            t = threading.Thread(target=close_threading)
            th.append(t)
        for i in th:
            i.start()
        for i in th:
            i.join()
        self.log.info("Chrome 全部关闭。")


    def load_resource(self, url, url_md5='', screenshot_name=''):
        """
        利用phantomjs加载网络资源
        """
        # 从队列取出创建好的phantomjs进程对象

        d = self.queue_webdriver.get()
        try:
            self.log.info('[{}] Start loading page resources. '.format(url_md5))
            d.get(url)
            self.log.info('[{}] Page resource loading is complete. '.format(url_md5))
        except Exception as e:
            self.queue_webdriver.put(d)
            raise Exception('Browser Open URL Error:{}'.format(e))
        time.sleep(8)
        title = d.title
        content = d.page_source

        if self.screenshot:
            screenshot_path = self.screenshot_folder + screenshot_name
            d.save_screenshot(screenshot_path)

        # 对象用完返还给队列
        self.queue_webdriver.put(d)
        return title, content
