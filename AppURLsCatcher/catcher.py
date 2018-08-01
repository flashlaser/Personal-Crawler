# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2017/11/15
# @Author   : Zhangjw
# @File     : catcher.py
# @Company  : Meiya Pico

import os
import re
import queue
import time
import threading
import psutil
import requests
from requests.adapters import HTTPAdapter

from AppURLsCatcher.config import SQL_CATCHER_EXCEPT, SQL_CATCHER_NORMAL
from AppURLsCatcher.bloomfilter import BloomFilter
from AppURLsCatcher.htmlpage import URLSourceFactory, HTMLPage
from AppURLsCatcher.progressbar import ProgressBar
from AppURLsCatcher.threadpool import WorkManager
from AppURLsCatcher.netload import WebdriverManager


class AppURLsCatcher(object):
    def __init__(self,
                 appname,
                 subappname,
                 all_sources,
                 pending_sources,
                 save_path,
                 record,
                 headless = True,
                 thread_count = 5,
                 config = None,
                 log=None
                 ):
        self.appname = appname
        self.subappname = subappname
        # 下载资源队列
        self.source_list = list(pending_sources)
        self.total = len(all_sources)
        self.exist = self.total - len(pending_sources)
        # 捕获的网络资源存储路径
        self.save_path = save_path + '\\AppURLs\\'
        self.request = self.Requests
        # 并发数目
        self.thread_count = thread_count
        self.record = record
        self.progress = ProgressBar(self.appname, self.subappname, self.total, self.exist, record.record_queue, log)
        time.sleep(3)
        if self.total == self.exist:
            return
        self.log = log
        # 资源重复过滤器
        self.filter = BloomFilter(0.001, 1000000)
        self.drivermanager = WebdriverManager(log, screenshot_folder=self.save_path + "thumbnails\\", browser_max= self.thread_count,
                                              headless=headless , screenshot = True)
        self.drivermanager.open_chromedriver()
        self.workmanager = WorkManager(self.fetch_network_resource, self.source_list, thread_num = self.thread_count)
        self.workmanager.wait_allcomplete()
        self.drivermanager.close_chromedriver()


    def save_file(self, filepath, filename, content):
        """
        生成文件
        :return:
        """
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        fileobj = filepath + '\\' + filename

        if not os.path.exists(fileobj):
            with open(fileobj, 'wb') as f:
                f.write(content)

    @property
    def Requests(self):
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=3))
        s.mount('https://', HTTPAdapter(max_retries=3))
        return s

    def download_file(self, url, filepath, filename, timeout=5):
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        response = self.request.get(url, timeout=timeout)
        self.save_file(filepath, filename, response.content)

    def is_url_invalid(self, url):
        """
        判断URL是否合法
        :param url:
        :return: True or False
        """
        if re.match(r'^https?:/{2}\w.+$', url):
            return True
        else:
            return False

    def except_record(self, source, error_type, error_desc):
        sql = SQL_CATCHER_EXCEPT.format(source[0], source[1], error_type, error_desc)
        self.record.record_queue.put((self.subappname, sql))
        self.progress.add_count

    def normal_record(self, source, fileobj):
        sql = SQL_CATCHER_NORMAL.format(source[0], source[1], fileobj.filename, fileobj.relpath, fileobj.filetype)
        self.record.record_queue.put((self.subappname, sql))
        self.progress.add_count

    def download_resouce(self, htmlfile:HTMLPage):
        file = htmlfile
        if isinstance(file, HTMLPage):
            for address in file.style_set:
                style_url = address[1]
                style_name = address[2]
                try:
                    self.download_file(style_url, file.source_abspath, style_name)
                except Exception as e:
                    continue

            for address in file.image_set:
                image_url = address[1]
                image_name = address[2]
                try:
                    self.download_file(image_url, file.source_abspath, image_name)
                except Exception as e:
                    continue

            for address in file.script_set:
                script_url = address[1]
                script_name = address[2]
                try:
                    self.download_file(script_url, file.source_abspath, script_name)
                except Exception as e:
                    continue

    def fetch_network_resource(self, source:tuple):
        """
        云数据获取
        :param source:
        :return:
        """
        appname = source[0]
        url = source[1]

        if self.filter.is_element_exist(source):
            self.except_record(source, "已处理", "已处理过的取证元素")
            return

        #  判断URL是否合法
        if not self.is_url_invalid(url):
            self.except_record(source, "无效的URL", "不合法的url,无法进行数据获取")
            return
        self.filter.insert_element(source)

        response = None
        # 利用工厂方法对 url 对应资源进行分类和实例化
        try:
            factory = URLSourceFactory()
            file = factory.get_source(url=url, appname=appname, root=self.save_path)
        except Exception as e:
            self.except_record(source, "请求文件异常", e)
            # self.log.error("Request network resources failed. error info: {}".format(e))
            return

        if file.filetype == 'others':
            self.except_record(source, '不支持的文件类型', "Unsupported File Type.")
            return

        if file.filetype == 'image/jpeg':
            try:
                file.parse_file_info()
            except Exception as e:
                self.except_record(source, '无法解析的图片文件', e)
                self.log.exception('Parse source file failed. error info:{}'.format(e))
                return

            try:
                self.save_file(file.abspath, file.filename, file.content)
            except Exception as e:
                self.except_record(source, "创建文件失败", e)
                self.log.error('Download picture failed:{}. error info: {} '.format(source,e))
                return
            file.filetype = 2
            self.normal_record(source, file)
            return True

        elif file.filetype == 'text/html':
            try:
                screenshot_name = file.url_md5 +'.png'
                title, page_source = self.drivermanager.load_resource(file.url, file.url_md5, screenshot_name)
            except Exception as e:
                self.except_record(source, "加载文件失败", e)
                self.log.info('[{}] Page resource loading exception.'.format(file.url_md5))
                # self.log.error("Request network resources failed. error info: {}".format(e))
                return

            try:
                file.parse_file_info(title, page_source)
            except Exception as e:
                self.except_record(source, '无法解析的网页文件', e)
                self.log.exception('Parse source file failed. error info:{}'.format(e))
                return

            # 下载网页对应的资源文件
            self.download_resouce(file)
            # 创建html文件
            try:
                self.save_file(file.abspath, file.filename, file.local_content.encode())
            except Exception as e:
                self.except_record(source, "创建文件失败", "创建文件：{} 失败，异常信息：{}".format(file.filename, e))
                self.log.error('Failed to create file:{}. error info: {} '.format(source, e))
                return
            file.filetype = 1
            self.normal_record(source, file)
        return True











