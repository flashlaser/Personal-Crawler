# -*- coding: utf-8 -*-

# @Function : 简陋的http下载模块
# @Time     : 2017/9/30
# @Author   : Zhangjw
# @File     : downloader.py
# @Company  : Meiya Pico

import requests
import threading
import queue
import os
import re
import hashlib
import time
from WeiboCatcher.logger import Logger


class Downloader(object):
    '''
    版本一：
    多线程
    轻便下载：图片 网页
    可反馈下载结果
    可对URL进行去重
    日志
    计划版本二：
    分块下载
    断点续传
    支持大文件下载 视频
    '''
    def __init__(self,thread_count = 5,timeout = 5,record=False):
        self.url_queue = queue.Queue()
        self.thread_list = []
        self.result = set()
        self.timeout = timeout
        self.log = Logger("Weibo-download.log")
        self.thread_count = thread_count
        self.recode = record
        self.add_count = 0
        self.remove_count = 0
        self._run()
        self.session = None
        self.log.info('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

    def __del__(self):
        '''
        :return:
        '''
        for i in self.thread_list:
            # 设置等待
            i.join()
        pass

    def set_session(self,session):
        self.session = session

    def add_task(self, url, path='', name=''):
        '''
        文件下载
        :param url: url
        :param path: 存储地址默认当前目录
        :param name: 存储文件名 默认为空 取url.split('/')[-1]
        :return:url的md5 暂定为md5
        '''
        #判断url是否合法，不合法 return None
        try:
            if not re.match(r'^https?:/{2}\w.+$', url):
                return None
        except Exception as e:
            self.log.error("invalid url:{}， error info:{}. ".format(url, e))
            return None

        if not path:
            path = os.getcwd()
        else:
            if not os.path.exists(path):
                os.makedirs(path)

        md5str = self._md5_encode(url)

        if not name:
            name = url.split('/')[-1]
        source = (url,path,name,md5str)
        self.url_queue.put(source)
        self.add_count += 1
        return md5str

    def get_result(self, md5str):
        '''
        根据url的md5判断文件是否下载成功
        :return:
        '''
        if md5str in self.result.keys():
            return True
        return False

    def download_wait(self, time_interval=5):
        while (not self.url_queue.empty()) and \
                (self.add_count != self.remove_count):
            time.sleep(time_interval)
        #self.log.info("wait util.")
    
    def download_queue_empty(self):
        return self.url_queue.empty()

    def _download(self):
        while True:
            source = self.url_queue.get()

            url = source[0]
            localpath = source[1]
            filename = source[2]
            md5str = source[3]
            content = None

            try:
                if self.session:
                    response = self.session.get(url, timeout=self.timeout)
                    content = response.content
                else:
                    response = requests.get(url, timeout=self.timeout)
                    content = response.content
            except Exception as e:
                self.log.error('{}:{}:{}'.format(filename, url, e))
                self.remove_count += 1
                continue

            if not content:
                self.log.error('get file content fail:{}'.format(url))
                self.remove_count += 1
                continue

            try:
                self._generate_file(localpath, filename, content)
                self.remove_count += 1
            except Exception as e:
                self.log.error("Picture download failed!-{}:{}".format(e, url))
                self.remove_count += 1
                continue
            continue

    def _run(self):
        for i in range(self.thread_count):
            thread = threading.Thread(target=self._download, args=())
            thread.start()
            self.thread_list.append(thread)

    def _md5_encode(self,str):
        '''
        将字符串进行md5加密
        :param str:
        :return: md5str
        '''
        m = hashlib.md5()
        m.update(str.encode("utf8"))
        return m.hexdigest()

    def _generate_file(self, filepath, filename, content):
        '''
        生成文件
        :return:
        '''
        fileobj = filepath + '/' +filename
        filetmp = fileobj + '.do'

        if os.path.exists(fileobj) or os.path.exists(filetmp):
            return 0

        with open(filetmp, 'wb') as f:
            f.write(content)
        #self.log.info('CreateFile:{}'.format(fileobj))
        os.rename(filetmp, fileobj)
        return 0


def generate_file(filepath, filename, content):
    fileobj= filepath+'\\'+filename
    i = 1
    filesub = fileobj
    while os.path.exists(filesub):
        filesub = fileobj+'({})'.format(i)
        i += 1
    if not os.path.exists(filesub):
        with open(filesub, 'wb') as f:
            f.write(content)

def download_file(url, filepath, filename, timeout=5):
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    response = requests.get(url, timeout=timeout)
    generate_file(filepath, filename, response.content)



class download_image:
    # 构造函数
    def __init__(self, url):
        # 设置url
        self.url = url
        # 设置线程数
        self.num = 4
        # 文件名从url最后取
        self.name = self.url.split('/')[-1]
        # 用head方式去访问资源
        r = requests.head(self.url)
        # 取出资源的字节数
        self.total = int(r.headers['Content-Length'])
        print('total is %s' % (self.total))

    def get_range(self):
        ranges = []
        # 比如total是50,线程数是4个。offset就是12
        offset = int(self.total / self.num)
        for i in range(self.num):
            if i == self.num - 1:
                # 最后一个线程，不指定结束位置，取到最后
                ranges.append((i * offset, ''))
            else:
                # 没个线程取得区间
                ranges.append((i * offset, (i + 1) * offset))
        # range大概是[(0,12),(12,24),(25,36),(36,'')]
        return ranges


    def download(self, start, end):
        headers = {'Range': 'Bytes=%s-%s' % (start, end), 'Accept-Encoding': '*'}
        # 获取数据段
        res = requests.get(self.url, headers=headers)
        # seek到指定位置
        print('%s:%s download success' % (start, end))
        self.fd.seek(start)
        self.fd.write(res.content)

    def run(self):
        # 打开文件，文件对象存在self里
        self.fd = open(self.name, 'w')
        thread_list = []

        n = 0
        for ran in self.get_range():
            start, end = ran
            print('thread %d start:%s,end:%s' % (n, start, end))
            n += 1
            # 开线程
            thread = threading.Thread(target=self.download, args=(start, end))
            thread.start()
            thread_list.append(thread)
        for i in thread_list:
            # 设置等待
            i.join()
        print('download %s load success' % (self.name))
        self.fd.close()