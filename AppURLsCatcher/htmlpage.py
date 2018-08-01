# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2017/11/15
# @Author   : Zhangjw
# @File     : collect.py
# @Company  : Meiya Pico

import requests
import random
import re
import os
import cgi
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def md5_encode(str):
    '''
    将字符串进行md5加密
    :param str:
    :return: md5str
    '''
    m = hashlib.md5()
    m.update(str.encode("utf8"))
    return m.hexdigest()


class URLSource(object):
    def __init__(self, url,
                 appname=None,
                 root = None
                 ):
        # url
        self.url = url
        # 文件标题
        self.title = None
        # 文件名称
        self.filename = None
        # 文件类型
        self.filetype = 'others'
        # 文件url的md5值
        self.url_md5 = None
        # 文件来自哪个app
        self.appname = appname
        # 文件对应url来自手机取证哪张表
        # 文件内容
        self.content = None
        # 存储路径
        self.root = root


class ImageFile(URLSource):
    def __init__(self, url,
                 appname=None,
                 packet = None,
                 root = None
                 ):
        URLSource.__init__(self, url, appname,  root)
        # 文件存储目录
        self.root = root
        # 图片存储的自定义相对路径
        self.relpath = None
        # 图片存储的绝对路径
        self.abspath = None
        # 文件类型
        self.filetype = 'image/jpeg'
        # 文件名称
        self.filename = ''
        # 网络应答包头
        self.headers = packet.headers
        # 本地文件内容
        self.content = None
        # 图片大小
        self.filesize = 0
        self.packet = packet

    def parse_file_info(self):

        self.url_md5 = md5_encode(self.url)

        self.filesize = self.__filesize()

        self.filename = self.__filename()
        if not self.filename:
            raise Exception('未获取到资源文件名称：{}'.format(self.url))

        self.relpath = '/AppURLs/pictures/'.format(self.url_md5)
        self.abspath = self.root + 'pictures\\'

        self.content = self.packet.content
        if not self.content:
            raise Exception('未获取到资源文件内容：{}'.format(url))

    def __filesize(self):
        '''获取文件大小'''
        # Content - Length
        if not self.headers:
            return 0
        else:
            try:
                filesize = int(self.headers.get('Content-Length'))
            except Exception as e:
                filesize = 0
        return filesize

    # def __filenameB(self):
    #     '''获取url对应的图片文件名称'''
    #     try:
    #         filename = self.url.split('/')[-1]
    #     except Exception as e:
    #         return md5_encode(self.url)
    #     pos = filename.find('?')
    #     if pos != -1:
    #         filename = filename[0:pos]
    #     return filename

    def __filename(self):
        url_md5 = md5_encode(self.url)
        filename = url_md5 + '.jpg'
        return filename


class HTMLPage(URLSource):
    def __init__(self, url,
                 appname=None,
                 packet = None,
                 root = None,
                 soup = None
                 ):
        URLSource.__init__(self, url, appname, root)
        self.url_md5 = md5_encode(url)
        self.root = root
        # 网页存储的自定义相对路径
        self.relpath = None
        # 网页存储的绝对路径
        self.abspath = None
        # 应答包头部
        self.headers = packet.headers
        # 文件类型
        self.filetype = 'text/html'
        # 文件名称
        self.filename = ''
        # 样式文件集合
        self.style_set = set()
        # js文件地址集合
        self.script_set = set()
        # 图片地址集合
        self.image_set = set()
        # 资源文件名称集合
        self.filename_set = set()
        # 页面编码
        self.charset = 'utf-8'
        # str类型的文本
        self.text = None
        # 本地文件内容
        self.local_content = None
        # Beautifulsoup用做解析html
        self.soup = soup
        self.packet = packet
        # 资源文件存储的绝对路径
        self.source_abspath = None
        # 资源文件的相对路径
        self.source_relpath = None

    def __del__(self):
        del self.soup

    def get_charset(self):
        '''获取页面编码'''
        """Returns encodings from given HTTP Header Dict.
        :param headers: dictionary to extract encoding from.
        """
        content_type = self.headers.get('content-type')
        if not content_type:
            return 'utf-8'  # 获取不到，默认返回utf-8
        content_type, params = cgi.parse_header(content_type)
        if 'charset' in params:
            if params['charset'].strip("'\"") == None:
                return 'utf-8'
            return params['charset'].strip("'\"")
        if 'text' in content_type:
            return 'ISO-8859-1'

    def get_encoding(self):
        '''
        获取网页编码
        :return:
        '''
        charset = self.soup.original_encoding
        return charset

    def get_title(self):
        '''
        获取网页标题
        :return:
        '''
        title_label = self.soup.title
        if not title_label:
            return False
        title = title_label.get_text()
        title = re.sub('[\/:*?"<>|]', '-', title).replace("\n","")
        title = title.strip()
        if len(title)>60:
            self.title = title[0:59]
            return True

        self.title = title
        if self.title:
            return True
        return False

    def remove_labels(self):
        '''删除特定标签'''
        # 删除base 标签
        [s.extract() for s in self.soup('base')]
        pass

    def format_filename(self, name=None):
        if name is None:
            return
        reg = re.compile(r'[///:*?"<>|/r/n]+')
        valid_name = reg.findall(name)
        if valid_name:
            for nv in valid_name:
                name = name.replace(nv, "_")
        return name

    def get_style_urls(self):
        '''
        解析获取网页中的css文件链接
        :return:
        '''
        for link in self.soup.find_all('link'):
            i = 1
            if link['rel'][0].lower() == 'stylesheet':
                relpath = link['href']
                abspath = urljoin(self.url, relpath)

                filename = relpath.split('/')[-1]
                pos = filename.find('.css')
                if pos != -1:
                    filename = filename[0:pos + 4]

                file_name = self.format_filename(filename)
                while file_name in self.filename_set:
                    file_name = filename + '({})'.format(i)
                    i += 1
                link['href'] = self.source_relpath + file_name
                self.style_set.add((relpath, abspath, file_name))
                self.filename_set.add(filename)

    def get_script_urls(self):
        '''
        解析获取网页中的js文件链接
        :return:
        '''
        for script in self.soup.find_all('script'):
            i = 1
            if 'src' in script.attrs:
                relnet_path = script['src']
                absnet_path = urljoin(self.url, relnet_path)
                filename = relnet_path.split('/')[-1]
                pos = filename.find('.js')
                if pos != -1:
                    filename = filename[0:pos + 3]
                file_name = self.format_filename(filename)
                while file_name in self.filename_set:
                    file_name = filename + '({})'.format(i)
                    i += 1

                file_relpath = self.source_relpath + file_name
                script['src'] = file_relpath
                self.script_set.add((relnet_path, absnet_path, file_name))
                self.filename_set.add(file_name)

    def get_image_urls(self):
        '''
        解析获取网页中图片链接
        :return:
        '''
        for link in self.soup.find_all('img'):
            i = 1
            if 'src' in link.attrs:
                relnet_path = link['src']
                absnet_path = urljoin(self.url, relnet_path)
                filename = relnet_path.split('/')[-1]
                pos = filename.find('?')
                if pos != -1:
                    filename = filename[0:pos]

                file_name = self.format_filename(filename)
                while file_name in self.filename_set:
                    file_name = filename + '({})'.format(i)
                    i += 1
                file_relpath = self.source_relpath + file_name
                link['src'] = file_relpath

                self.image_set.add((relnet_path, absnet_path, file_name))
                self.filename_set.add(file_name)

            if 'data-src' in link.attrs:
                relnet_path = link['data-src']
                absnet_path = urljoin(self.url, relnet_path)
                filename = relnet_path.split('/')[-1]
                pos = filename.find('?')
                if pos != -1:
                    filename = filename[0:pos]
                file_name = self.format_filename(filename)
                while file_name in self.filename_set:
                    file_name = filename + '({})'.format(i)
                    i += 1
                file_relpath = self.source_relpath + file_name
                link['src'] = file_relpath

                self.image_set.add((relnet_path, absnet_path, file_name))
                self.filename_set.add(file_name)

    def parse_file_info(self, title, page_source):
        '''
        解析文本 并转换为本地文本
        将资源文件网络路径替换为本地路径
        :return:
        '''
        self.title = self.format_filename(title)
        self.content = page_source

        # 设置解析器
        self.soup = BeautifulSoup(self.content, 'lxml')
        if not self.soup:
            raise Exception('初始化BeautifulSoup异常.')
        # 获取网页标题
        if not self.title:
            raise Exception('URL对应网页标题为空:{}'.format(self.url))
        # 网页文件名
        self.filename = self.title + '.html'
        # html存储的相对路径
        self.relpath = '/AppURLs/webpage/{}/'.format(self.url_md5)
        # html存储的绝对路径
        self.abspath = self.root + '\\webpage\\{}\\'.format(self.url_md5)
        # 资源文件存储的绝对路径
        self.source_abspath = self.root + 'webpage\{}\{}_files'.format(self.url_md5, self.title)
        # 相对html的路径
        self.source_relpath = "./{}_files/".format(self.title)
        # 获取网页编码
        self.charset = self.get_encoding()
        # 删除特定标签
        self.remove_labels()
        # 解析css文件地址 并替换原网页代码中的文件地址
        try:
            self.get_style_urls()
        except Exception as e:
            raise Exception('解析获取网页css文件地址异常:{}'.format(e))
        #解析.js文件地址
        try:
            self.get_script_urls()
        except Exception as e:
            raise Exception('解析获取网页css文件地址异常:{}'.format(e))

        #解析图片地址
        try:
            self.get_image_urls()
        except Exception as e:
            raise Exception('解析获取网页image文件地址异常:{}'.format(e))

        self.local_content = self.soup.html
        if not self.local_content:
            raise Exception('解析获取网页内容异常:{}'.format(e))


class URLSourceFactory(object):
    def get_source(self, url, appname=None, root=None):
        """
        工厂方法，获取URL对应网络资源并进行分类和实例化
        :param url: url
        :param appname: url 所属应用程序名称
        :param title: 标题
        :param tablename: url 来源数据库表名
        :param fieldname: url 来源字段名
        :param position: url 来源具体位置
        :param root: 根路径
        :return:
        """

        USER_AGENTS = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 '
            'Mobile/13B143 Safari/601.1]',
            'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/48.0.2564.23 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/48.0.2564.23 Mobile Safari/537.36']

        HEADER = {
            "User-Agent": 'Chrome/48.0.2564.23 Mobile Safari/537.36',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        response = requests.get(url, headers=HEADER, timeout=10)
        headers = response.headers

        content_type = headers.get('Content-Type')
        if content_type.find('text/html') != -1 \
                or content_type.find('xhtml+xml') != -1:
            return HTMLPage(url=url, appname=appname, packet=response, root=root)
        elif content_type.find('image/jpeg') != -1 \
                or content_type.find('image/png') != -1:
            return ImageFile(url=url, appname=appname, packet=response, root=root)
        else:
            return URLSource(url, appname=appname,  root=root)
