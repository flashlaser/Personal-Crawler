# -*- coding: utf-8 -*-
# Author: ZhangJave
# Email: []
# 2017-11-29
#
# 测试平台 Windows 10 X86_64 Python 3.6

import requests
import threading
import queue
import os
import re
import hashlib
import time
from pyjdmallcatcher.config import log, BIN64_PATH



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
        self.log = log
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
        if not re.match(r'^https?:/{2}\w.+$', url):
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
                if filename.find(".webp") != -1:
                    try:
                        srcfile = localpath + "\\" + filename
                        dstfile = localpath + "\\" + filename + ".png"
                        self.webp2jpg(srcfile, dstfile)
                    except Exception as e:
                        self.log.error("webp to png error. error info:{}".format(e))
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
        fileobj = filepath + '\\' +filename
        filetmp = fileobj + '.do'

        if os.path.exists(fileobj) or os.path.exists(filetmp):
            return 0

        with open(filetmp, 'wb') as f:
            f.write(content)

        os.rename(filetmp, fileobj)
        return 0

    def webp2jpg(self, srcfile, dstfile):
        command = ' "{}\\Tool\\libwebp\\bin\\dwebp.exe" "{}" -o "{}" '.format(BIN64_PATH, srcfile, dstfile)
        os.popen(command)

