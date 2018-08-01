# -*- coding: utf-8 -*-

# @Function : 微博app版仿真接口
# @Time     : 2017/9/30
# @Author   : Zhangjw
# @File     : weibo_api.py
# @Company  : Meiya Pico

import requests
from requests.adapters import HTTPAdapter
import re
import json
import hashlib
import random
import time
from WeiboCatcher.utils import try_except, md5_encode
from WeiboCatcher.config import APP_KEY, HTTP_TIMEOUT, MAX_RETRIES

from WeiboCatcher import utils
from requests.adapters import HTTPAdapter
from urllib.parse import quote
MAX_RETRIES = 3

def md5_encode(str):
    '''
    将字符串进行md5加密
    :param str:
    :return: md5str
    '''
    m = hashlib.md5()
    m.update(str.encode("utf8"))
    return m.hexdigest()


def transfer(content):
    if content is None:
        return None
    else:
        string = ""
        for c in content:
            if c == '"':
                string += '\\\"'
            elif c == "'":
                string += "\\\'"
            elif c == "\\":
                string += "\\\\"
            else:
                string += c
        return string


class Weibo(object):

    DEVICE_ID = "a6b9c935a0f7edd8607930696952fa0edf310718"
    DEVICE_NAME = "Huawei-Nexus 6P"
    UA = "Huawei-Nexus%206P__weibo__8.4.3__android__android6.0"
    IMEI = "86798102329162"
    SYSTEM = "android"

    APP_KEY = {
        'iphone': '5Jao51NF1i5PDC91hhI3ID86ucoDtn4C',
        'android': '5l0WXnhiY4pJ794KIJ7Rw5F45VXg9sjo'
    }

    HEADERS = {
        "Host": "api.weibo.cn",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "cronet_rid": "3928638",
        "SNRT": "normal",
        "User-Agent": "Weibo/27222 (iPhone; iOS 9.3; Scale/2.00)",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate"
    }

    def __init__(self,
                 account,
                 username='',
                 password='',
                 phone = '',
                 uid = '',
                 gsid = '',
                 access='',
                 system = 'android'
                 ):
        self.request = self.Requests
        self.account = account
        # 用户账号
        self.username = username
        # 用户密码
        self.password = password
        # 手机号码 默认ipone即可
        self.phone = phone
        # 用户id
        self.uid = uid
        # aid
        self.aid = None
        # gsid 必要参数
        self.gsid = gsid
        # 私信必要参数
        self.access_token = access
        # 手机系统 iphone/android
        self.system = system
        self.appkey = None
        # 关键字s 必要参数
        self.keyword_s = None
        # 关键字i
        self.keyword_i = None
        # 关键字ua
        self.keyword_ua = None
        # 昵称
        self.nick_name = None

        if system and system in APP_KEY.keys():
            self.appkey = APP_KEY[system]
            self.keyword_s = self.get_keyword_s
            
    @property
    def Requests(self):
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=MAX_RETRIES))
        s.mount('https://', HTTPAdapter(max_retries=MAX_RETRIES))
        return s


    @property
    def get_keyword_s(self):
        '''
        获取s的值
        :return:
        '''
        tmpstr = self.uid + self.appkey
        md5sarr = md5_encode(tmpstr)
        s = ''
        if md5sarr:
            s = md5sarr[1] + md5sarr[5] + md5sarr[2] + md5sarr[10] + md5sarr[17]\
                + md5sarr[9] + md5sarr[25] + md5sarr[27]
        return s

    @property
    def get_keyword_s_user(self):
        """
        生成登录时的关键字s
        :return:
        """
        keywords = "5l0WXnhiY4pJ794KIJ7Rw5F45VXg9sjo{}{}1084395010".format(self.username, self.password)
        encrypts = hashlib.sha512(keywords.encode('utf-8')).hexdigest()
        if encrypts:
            s = encrypts[11] + encrypts[17] + encrypts[24] + encrypts[30] + encrypts[33] + encrypts[38] + encrypts[50] + encrypts[61]
        return s

    @property
    def get_keyword_s_sms(self):
        """
        生成短信登录时的关键字s
        :return:
        """
        uid = "1009438211089"
        keywords = "5l0WXnhiY4pJ794KIJ7Rw5F45VXg9sjo{}1084395010".format(uid)
        encrypts = hashlib.sha512(keywords.encode('utf-8')).hexdigest()
        if encrypts:
            s = encrypts[11] + encrypts[17] + encrypts[24] + encrypts[30] + encrypts[33] + encrypts[38] + encrypts[50] + encrypts[61]
        return s

    @property
    def get_keyword_s_uid(self):
        """
        生成登录时的关键字s
        :return:
        """
        keywords = "5l0WXnhiY4pJ794KIJ7Rw5F45VXg9sjo{}1084395010".format(self.uid)
        encrypts = hashlib.sha512(keywords.encode('utf-8')).hexdigest()
        if encrypts:
            s = encrypts[11] + encrypts[17] + encrypts[24] + encrypts[30] + encrypts[33] + encrypts[38] + encrypts[50] + \
                encrypts[61]
        return s


    def request_sms(self):
        """
        向服务器请求短信验证码
        :return:
        """
        # url = "https://api.weibo.cn/2/account/login_sendcode?wm=3333_2001&i=0ce92df&b=1&from=1084393010&c=iphone&networktype=wifi&v_p=60&skin=default&v_f=1&lang=zh_CN&sflag=1&ua=iPhone6,2__weibo__8.4.3__iphone__os9.3&ft=0&aid=01AknwAiCTI2ImDccvytbb1TCVatPE5iPmhisNwpuJSxKZMYg."
        url = "https://api.weibo.cn/2/account/login_sendcode?networktype=wifi&phone_id=0&uicode=10000279&moduleID=701&" \
              "checktoken=&wb_version=3614&getuser=1&c=android&i=33b49c7&s={}&ft=0&ua={}&wm=4209_8001&v_f=2&v_p=60&" \
              "area=&from=1084395010&gsid=_2AkMsSCKmf8NhqwJRmPERz2PgbYx3wgHEieKaFNN9JRMxHRl-wT9jqnQztRV6BuP6MjTOLfI8vHqMpDu3Q-vrQVb7tNge" \
              "&imei={}&lang=zh_CN&skin=default&oldwm=4209_8001&phone={}&sflag=1&luicode=10000058&getcookie=1&getoauth=1".format(self.get_keyword_s_sms, Weibo.UA,
                                                                                                                        self.gsid, Weibo.IMEI, self.phone)

        headers = {
            "Host":"api.weibo.cn",
            "Connection":"keep-alive",
            "Content-Type":"application/x-www-form-urlencoded; charset=utf-8",
            "SNRT" : "normal",
            "User-Agent": Weibo.UA,
            "Accept":"*/*",
            "Accept-Encoding":"gzip, deflate"
        }

        # payload = {
        #     'moduleID' : 'account',
        #     'phone' : self.phone
        # }
        payload = {
            "pwd":"",
            "phone":self.phone,
            "flag":"1",
        }

        resp = requests.post(url, headers=headers, data=payload).json()
        errno = 0
        errmsg = ''

        if not resp.get('sendsms', ''):
            errno = resp.get('errno', 1)
            errmsg = resp.get('errmsg', '')
        return (errno, errmsg)

    def submit_smscode(self, smscode=None):
        """
        提交短信验证码
        :return:
        """

        url = "https://api.weibo.cn/2/account/login?smscode={}&networktype=wifi&uicode=10000062&moduleID=701&" \
              "wb_version=3614&c=android&i=33b49c7&ft=0&ua={}&wm=4209_8001&aid=01Ag5cLy3FoB70YjpXsukfQR0xIpwrpS" \
              "s2EEaBNSyhfRPXHFk.&did=a6b9c935a0f7edd8607930696952fa0e776f866e&v_f=2&v_p=60&from=1084395010&" \
              "imei={}&lang=zh_CN&skin=default&device_id={}&oldwm=4209_8001&phone={}&sflag=1&guestid=1009438211089&" \
              "luicode=10000279".format(smscode, Weibo.UA, Weibo.IMEI, Weibo.DEVICE_ID, self.phone)


        headers = {
            'Host': 'api.weibo.cn',
            'Connection': 'keep-alive',
            'SNRT': 'normal',
            'User-Agent': Weibo.UA,
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate'
        }

        payload = {
            "device_name":Weibo.DEVICE_NAME,
            "getuser":"1",
            "getcookie":"1",
            "getoauth":"1"
        }

        # payload['smscode'] = smscode
        resp = requests.post(url, headers=headers, data=payload).json()

        self.gsid = resp.get('gsid', '')
        self.uid = resp.get('uid', '')
        auth = resp.get('oauth2.0', '')
        if auth:
            self.access_token = auth.get('access_token', '')
        
        if self.gsid and self.uid:
            return True
        return False


    def login_by_userpass(self):
        """
        通过账号密码登录
        :return:
        """
        encrypt_password = utils.encrypt_rsa(self.password)
        url = "https://api.weibo.cn/2/account/login?networktype=wifi&uicode=10000058&moduleID=701&checktoken=390838720ce5ea1e21b53f31fc7f95b8&wb_version=3614&c={}&i=33b49c7&p={}&s={}&u={}&ft=0&ua={}&wm=4209_8001&aid=01Ag5cLy3FoB70YjpXsukfQR0gOaaR9uZBX8MTnTOUlSmVf84.&did=a6b9c935a0f7edd8607930696952fa0edf310718&v_f=2&v_p=60&flag=1&from=1084395010&imei={}&lang=zh_CN&skin=default&device_id={}&oldwm=4209_8001&sflag=1&guestid=1009438211089"
        url = url.format(Weibo.SYSTEM, quote(encrypt_password), self.get_keyword_s_user, self.username, Weibo.UA, Weibo.IMEI, Weibo.DEVICE_ID)

        headers = {'Host': 'api.weibo.cn',
                   'Connection': 'keep-alive',
                   'User-Agent': 'Nexus 6P_6.0_weibo_8.4.3_android',
                   'Content-Length': '60',
                   'Charset': 'UTF-8',
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept-Encoding': 'gzip,deflate'}

        payload = {
            "device_name": Weibo.DEVICE_NAME,
            "getuser": Weibo.DEVICE_ID,
            "getcookie": 1,
            "getoauth": 1,
        }

        resp = self.request.post(url, headers=headers, data=payload).json()
        self.gsid = resp.get('gsid', '')
        self.uid = resp.get('uid', '')

        if self.gsid and self.uid:
            return True
        return False


    def get_api_photos_list(self, since_id):
        '''
        获取照片列表
        :return:
        '''
        #url = "https://api.weibo.cn/2/cardlist?networktype=wifi&extparam=1&uicode=10000011&moduleID=708&wb_version=3534&lcardid=100505_-_WEIBO_INDEX_PROFILE_ALBUM&c=android&i=2600f81&s=b5f2f70b&ft=0&ua=samsung-SM-G955F__weibo__8.0.0__android__android4.4.2&wm=2468_1001&aid=01AjNpMR6YCHpVCU7F8Bh4AOFWil2kLo1S3xGj3hCD0toTV-k.&fid=107803_2327068910&uid=2327068910&v_f=2&v_p=56&from=1080095010&gsid=_2A253SB-EDeTxGeRN6VUR9ibFyjyIHXVSXBRMrDV6PUJbkdANLUfTkWpNU7sMLZDfRKedhTv1w6bohinzIYiNgNar&imsi=460078821524612&lang=zh_CN&lfid=1005052327068910&page=1&skin=default&count=20&oldwm=2468_1001&sflag=1&containerid=107803_2327068910&ignore_inturrpted_error=true&luicode=10000011&need_head_cards=1"
        #url = "https://api.weibo.cn/2/cardlist?networktype=wifi&extparam=1&uicode=10000011&moduleID=708&wb_version=3534&lcardid=100505_-_WEIBO_INDEX_PROFILE_ALBUM&c={}&i=2600f81&s={}&ft=0&wm=2468_1001&aid=01AjNpMR6YCHpVCU7F8Bh4AOFWil2kLo1S3xGj3hCD0toTV-k.&fid=107803_2327068910&uid={}&v_f=2&v_p=56&from=1080095010&gsid={}&imsi=460078821524612&lfid=100505{}&count=20&oldwm=2468_1001&sflag=1&containerid=107803{}&ignore_inturrpted_error=true&since_id={}&luicode=10000011&need_head_cards=1".format(since_id)

        url = "https://api.weibo.cn/2/cardlist?lcardid=100505_-_WEIBO_INDEX_PROFILE_ALBUM&c={}&i=2600f81&s={}&ft=0&wm=2468_1001&aid=01AjNpMR6YCHpVCU7F8Bh4AOFWil2kLo1S3xGj3hCD0toTV-k.&fid=107803_2327068910&uid={}&v_f=2&v_p=56&from=1080095010&gsid={}&imsi=460078821524612&lfid=100505{}&count=20&oldwm=2468_1001&sflag=1&containerid=107803{}&ignore_inturrpted_error=true&since_id={}&luicode=10000011&need_head_cards=1".format(
            self.system, self.keyword_s, self.uid, self.gsid, self.uid, self.uid, since_id)

        response = self.request.get(url,timeout=HTTP_TIMEOUT).json()

        if response['cardlistInfo']['v_p'] != '56':
            return None, None

        photo_list = []
        for card in response['cards']:
            if card['card_type'] == 11:
                photo_list.extend(card['card_group'])

        next_id = response['cardlistInfo']['since_id']
        return photo_list, next_id


    def get_api_dialog_list(self):
        '''
        获取会话列表
        每次请求只获取10条
        获取个人私信列表  和群组列表
        :return:
        '''
        cursor = 0
        count = 10

        header = {
            "Host": "api.weibo.cn",
            "Connection": "keep-alive",
            "User-Agent": "Weibo/10560 (iPhone; iOS 9.3; Scale/2.00)",
            "cronet_rid": "5860793",
            "SNRT": "normal",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate"
        }

        dialog_list = []
        group_dialog_list = []

        while True:
            url = "https://api.weibo.cn/2/direct_messages/user_list?gsid={}&b=1&c={}&networktype=wifi&v_f=1&s={}&sflag=1&ft=0&moduleID=wymessage&cursor={}&count={}&with_page_group=1&with_comment_attitude=1&sendtype=1".format(self.gsid, self.system, self.keyword_s, cursor, count)
            #url = 'https://api.weibo.cn/2/direct_messages/user_list?gsid={}&c={}&s={}&cursor={}&count={}'.format(self.gsid, self.system, self.crypt, cursor, count)
            response = self.request.get(url, headers=header, timeout=HTTP_TIMEOUT)
            if response.status_code != 200:
                return None

            if 'totalNumber' not in response.json().keys():
                break

            if response.json()['totalNumber'] == 0:
                return None

            if response.json()['next_cursor'] == 0 and response.json()['previous_cursor'] != 0:
                break

            if 'user_list' not in response.json():
                break

            if len(response.json()['user_list']) == 0:
                break
            one_page_list = response.json()['user_list']
            for dialog in one_page_list:
                if dialog['user'] and dialog['user']['type'] == 3:
                    group_dialog_list.append(dialog)
                else:
                    dialog_list.append(dialog)
            cursor += count
        return dialog_list, group_dialog_list


    @property
    def userinfo(self):
        """
        获取用户基本资料
        :return:
        """
        url = "https://m.weibo.cn/api/container/getIndex?containerid=230283{}_-_INFO&title=%25E5%259F%25BA%25E6%259C%25AC%25E8%25B5%2584%25E6%2596%2599&luicode=10000011&lfid=230283{}&featurecode=20000320".format(self.uid, self.uid)

        headers = {
            "Host": "m.weibo.cn",
            "Connection": "keep-alive",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Mobile Safari/537.36",
            "Referer": "https://m.weibo.cn/p/index?containerid=2302836407060187_-_INFO&title=%25E5%259F%25BA%25E6%259C%25AC%25E8%25B5%2584%25E6%2596%2599&luicode=10000011&lfid=2302836407060187&featurecode=20000320",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            #"Cookie": "_T_WM=2f3694bb938270a543a5802972d140d1; A^`=1525765887tdc7009252251; SUB=_2A253-Jy4DeRhGeBK61UR9i7NwzuIHXVVAiTwrDV6PUJbkdAKLXHBkW1NR-9p8g9SjjufpPeD9xbseRK4jR8rNmDE; SUHB=0sqBjFQsWN73uH; SCF=Aqh0eGsj12U-2OqSNwq9H07Okgvb3y7YECsmrvSue5RcrSNv2SjKlRe22CglrDH-wVmYZzGgj9V1DdxZygSiXHE.; SSOLoginState=1526525160; H5_INDEX=3; H5_INDEX_TITLE=%E6%88%90%E5%8A%9F_Fight_2018; WEIBOCN_FROM=1110006030; MLOGIN=1; M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D2302836407060187%26featurecode%3D20000320%26fid%3D2302836407060187_-_INFO%26uicode%3D10000011"
        }

        headers['Referer'] = "https://m.weibo.cn/p/index?containerid=230283{}_-_INFO&title=%25E5%259F%25BA%25E6%259C%25AC%25E8%25B5%2584%25E6%2596%2599&luicode=10000011&lfid=230283{}&featurecode=20000320".format(self.uid, self.uid)
        resp = self.request.get(url, headers = headers, timeout=HTTP_TIMEOUT).json()

        if resp.get('ok') != 1:
            return

        userinfo = {}
        item_map = {}
        for card in resp['data']['cards']:
            if card['card_type'] == 11:
                for item in card['card_group']:
                    if item['card_type'] == 41 and 'item_name' in item.keys():
                        name = item['item_name']
                        content = item['item_content']
                        item_map[name] = content
        containerid = resp['data']['cardlistInfo']['containerid']
        userinfo['uid'] = self.uid
        userinfo['nick'] = item_map.get(u'昵称', '')
        userinfo['gender'] = item_map.get(u'性别', '')
        userinfo['address'] = item_map.get(u'所在地', '')
        userinfo['description'] = item_map.get(u'简介', '')
        userinfo['created_at'] = item_map.get(u'注册时间', '')
        userinfo['birthday'] = item_map.get(u'生日', '')
        return userinfo

    def get_weibo_onepage(self, page_no):
        '''
        获取单独某一分页的微博内容--免登陆
        :param uid: 用户id
        :param page_num: 分页页码
        :return:一页微博内容集合
        '''
        weibo_list = []
        count = 0
        url = 'https://m.weibo.cn/api/container/getIndex?containerid=230413{}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page={}'.format(self.uid, page_no)

        response = self.request.get(url,timeout=HTTP_TIMEOUT)
        retjson = response.json()['data']

        if 'page_type' not in retjson['cardlistInfo'].keys():
            return None, None

        for card in retjson['cards']:
            if card['card_type'] == 9:
                mblog = {}
                mblog['mblog_title'] = card.get('title','').replace("'","''")
                mblog['mblog_url'] = card.get('scheme','')
                mblog['mblog_id'] = card.get('mblog').get('id')
                mblog['content'] = card.get('mblog').get('text').replace("'","''")
                mblog['created_at'] = card.get('mblog').get('created_at')
                mblog['source'] = self.account #card.get('mblog').get('source')
                mblog['reposts_count'] = card.get('mblog').get('reposts_count') # 转发数
                mblog['comments_count'] = card.get('mblog').get('comments_count') # 评论数
                mblog['attitudes_count'] = card.get('mblog').get('attitudes_count') # 点赞数
                mblog['more_info_type'] = card.get('mblog').get('more_info_type') # 微博类型
                mblog['from'] = self.uid
                mblog['uid'] = card.get('mblog').get('user').get('id')
                mblog['nick']  = card.get('mblog').get('user').get('screen_name')  # 用户昵称
                mblog['desc'] = card.get('mblog').get('user').get('description').replace("'","''")  # 描述
                mblog['profile_url'] = card.get('mblog').get('user').get('profile_url')  # 用户主页链接
                mblog['profile_image_url'] = card.get('mblog').get('user').get('profile_image_url')  # 用户头像链接

                if 'retweeted_status' in card.get('mblog').keys():
                    mblog['prev_createdat'] = card.get('mblog').get('retweeted_status').get('created_at')  # 前一次创建时间

                    mblog['prev_id'] = card.get('mblog').get('retweeted_status').get('id')  # 上次的微博ID
                    mblog['prev_content'] = card.get('mblog').get('retweeted_status').get('text').replace("'","''")  # 上次的微博内容
                    mblog['prev_source'] = card.get('mblog').get('retweeted_status').get('source')  # 来源

                    if card.get('mblog').get('retweeted_status').get('user') == None:
                        mblog['prev_uid'] = ''
                        mblog['prev_profile_url'] = ''
                        mblog['prev_desc'] = ''
                    else:
                        mblog['prev_uid'] = card.get('mblog').get('retweeted_status').get('id')  # 上次的用户ID
                        mblog['prev_profile_url'] = card.get('mblog').get('retweeted_status').get('user').get('profile_url')  # 上次的主页链接
                        mblog['pre_desc'] = card.get('mblog').get('retweeted_status').get('user').get('description').replace("'","''")  # 上次的用户描述

                weibo_list.append(mblog)
                count += 1
        return count, weibo_list


    @property
    def weibo_amount(self):
        '''
        获取微博分页总数和微博总数
        :param uid:用户id
        :return: 分页数，微博数
        '''
        url = 'https://m.weibo.cn/api/container/getIndex?containerid=230413{}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page=1000'.format(self.uid)

        response = self.request.get(url,timeout=HTTP_TIMEOUT)
        total = response.json()['data']['cardlistInfo']['total']
        if not total:
            total = 0

        total_int = int(total / 10)
        total_real = total / 10
        if total_int < total_real:
            total_int = total_int + 1
        return total_int, total


    @property
    def fans_amount(self):
        '''
        获取粉丝分页总数，粉丝总数
        :param uid: 用户id
        :return: int,int
        '''
        url = 'https://m.weibo.cn/api/container/getSecond?containerid=100505{}_-_FANS'.format(self.uid)
        response = self.request.get(url,timeout=HTTP_TIMEOUT)
        if response.json()['ok'] != 0:
            return (0, 0)

        if response.json()['data']['ok'] != 1:
            return (0, 0)

        total = response.json()['data']['count']
        if not total:
            total = 0
        total_page = response.json()['data']['maxPage']
        return total_page, total


    @property
    def fans_amount_beta(self):
        '''
        获取粉丝分页总数，粉丝总数
        :param uid: 用户id
        :return: int,int
        '''
        url = 'https://m.weibo.cn/api/container/getSecond?containerid=100505{}_-_FANS'.format(self.uid)

        response = self.request.get(url,timeout=HTTP_TIMEOUT)
        if response.json()['ok'] != 1:
            return (0, 0)

        if response.json()['data']['ok'] != 1:
            return (0, 0)

        total = response.json()['data']['count']
        if not total:
            total = 0
        total_page = response.json()['data']['maxPage']
        return total_page, total


    def get_fans_onepage(self, page_no):
        '''
        获取特定分页的粉丝
        :param uid:
        :param page_no:
        :return:
        '''
        fans_url = 'https://m.weibo.cn/api/container/getSecond?containerid=100505{}_-_FANS&page={}'.format(self.uid,
                                                                                                           page_no)
        one_list = []
        total = 0

        response = self.request.get(fans_url,timeout=HTTP_TIMEOUT)
        if response.json()['ok'] != 1:
            return (0, 0)

        if response.json()['data']['ok'] != 1:
            return (0, 0)

        for card in response.json()['data']['cards']:
            user = card['user']
            fans = {}
            #fans['account'] = self.user
            fans['uid'] = user['id']
            fans['nick'] = user['screen_name']
            fans['profile_url'] = user['profile_url'].replace(' ', '')
            fans['profile_image_url'] = user['profile_image_url']
            profile_image_name = '{}.jpg'.format(fans['uid'])
            fans['profile_image_name'] = profile_image_name
            fans['profile_image_path'] = '/WeiBo/picture/{}/friends/{}'.format(self.uid, profile_image_name)

            fans['statuses_count'] = user['statuses_count']
            fans['desc'] = user['description']
            fans['gender'] = user['gender']
            fans['from'] = self.uid

            fans['followers_count'] = user['followers_count']
            fans['follow_count'] = user['follow_count']

            fans['type'] = user['mbtype']  # 微博类型
            fans['rank'] = user['urank']  # 微博等级

            one_list.append(fans)
            total = total + 1

        return total, one_list


    @property
    def follower_amount(self):
        '''
        获取关注者数目
        :param uid:
        :return:
        '''
        url = 'https://m.weibo.cn/api/container/getSecond?containerid=100505{}_-_FOLLOWERS'.format(self.uid)
        response = self.request.get(url,timeout=HTTP_TIMEOUT)
        if response.json()['ok'] != 1:
            return (0, 0)

        if response.json()['data']['ok'] != 1:
            return (0, 0)

        total = response.json()['data']['count']
        if not total:
            total = 0
        total_page = response.json()['data']['maxPage']
        return total_page, total


    def get_follower_onepage(self, page_no):
        '''
        获取特定分页的粉丝
        :param uid:
        :param page_no:
        :return:
        '''
        fans_url = 'https://m.weibo.cn/api/container/getSecond?containerid=100505{}_-_FOLLOWERS&page={}'.format(
            self.uid, page_no)
        one_list = []
        total = 0

        response = self.request.get(fans_url,timeout=HTTP_TIMEOUT)
        if response.json()['ok'] != 1:
            return (0, 0)

        if response.json()['data']['ok'] != 1:
            return (0, 0)

        for card in response.json()['data']['cards']:
            user = card['user']
            fans = {}
            #fans['account'] = self.user
            fans['uid'] = user['id']
            fans['nick'] = user['screen_name']
            fans['profile_url'] = user['profile_url'].replace(' ', '')
            fans['profile_image_url'] = user['profile_image_url']
            profile_image_name = '{}.jpg'.format(fans['uid'])
            fans['profile_image_name'] = profile_image_name
            fans['profile_image_path'] = '/WeiBo/picture/{}/friends/{}'.format(self.uid, profile_image_name)

            fans['statuses_count'] = user['statuses_count']
            fans['desc'] = user['description']
            fans['gender'] = user['gender']
            fans['from'] = self.uid

            fans['followers_count'] = user['followers_count']
            fans['follow_count'] = user['follow_count']

            fans['type'] = user['mbtype']  # 微博类型
            fans['rank'] = user['urank']  # 微博等级

            one_list.append(fans)
            total = total + 1
        return total, one_list


    def get_weibo_comments(self, blog_id):
        i = 1
        list_comment = []
        weibo_url = 'https://m.weibo.cn/api/comments/show?id=%s&page=%s' % (blog_id, str(i))
        response = self.request.get(weibo_url,timeout=HTTP_TIMEOUT).json()
        if response['ok'] != 1:
            return 0, []
        total_num = 0
        max_page = response['max']
        while i <= max_page:
            weibo_url = 'https://m.weibo.cn/api/comments/show?id=%s&page=%s' % (blog_id, str(i))
            response = self.request.get(weibo_url,timeout=HTTP_TIMEOUT).json()
            list_comment.append(response)
            i = i + 1
        return total_num, list_comment


    def weibo_followed(self):
        """

        :return:
        """
        url = "https://api.weibo.cn/2/cardlist?networktype=wifi&uicode=10000011&moduleID=708&wb_version=3614&c={}&i=33b49c7&s={}&ft=0&ua={}&wm=4209_8001&aid=01Ag5cLy3FoB70YjpXsukfQR2cFAGfKeH4rOQlqtrKkOJoRU4.&fid=231093_-_selffollowed&uid=6387480531&v_f=2&v_p=60&from=1084395010&gsid={}&imsi=460110825310084&lang=zh_CN&lfid=1005056387480531_-_new&page={}&skin=default&count=20&oldwm=4209_8001&sflag=1&containerid=231093_-_selffollowed&ignore_inturrpted_error=true&luicode=10000011&need_head_cards=0"

        headers = {
            'Host': 'api.weibo.cn',
            'Connection': 'keep-alive',
            'X-Sessionid': '2ed01afe-786a-4a60-8a49-8b7747d16074',
            'User-Agent': 'Nexus 6P_6.0_weibo_8.4.3_android',
            'X-Validator': '0lMn/bdiqY93A5QwJSJL+04EEWTGjpmqzCV2nHJQprs=',
            'X-Log-Uid': '6387480531',
            'Accept-Encoding': 'gzip, deflate',
        }

        resp = self.request.get(url, timeout=HTTP_TIMEOUT).json()

        return resp

    def weibo_userinfo(self):
        """
        获取用户信息
        :return:
        """
        url = "https://api.weibo.cn/2/users/show?networktype=wifi&uicode=10000013&moduleID=700&wb_version=3614&c={}&" \
              "i=33b49c7&s={}&ft=0&ua={}&wm=4209_8001&aid=01Ag5cLy3FoB70YjpXsukfQR2cFAGfKeH4rOQlqtrKkOJoRU4.&uid={}&" \
              "v_f=2&v_p=60&from=1084395010&gsid={}&lang=zh_CN&lfid=107103000201&skin=default&oldwm=4209_8001&sflag=1&" \
              "luicode=10000011&has_profile=1&is_new_user=1&has_badges=1&has_extend=1" \
              "&has_member=1".format(self.system,self.get_keyword_s_uid, Weibo.UA, self.uid, self.gsid)

        headers = {
            'Host': 'api.weibo.cn',
            'Connection': 'keep-alive',
            # 'X-Sessionid': '25bd1206-b88d-4049-b576-2968b5f1825f',
            'User-Agent': 'Nexus 6P_6.0_weibo_8.4.3_android',
            # 'X-Validator': 'yJbEMsve7M9Q6bco74DEc5/56m4EZETrQwZPGrqaQpw=',
            'X-Log-Uid': self.uid,
            'Accept-Encoding': 'gzip, deflate',
        }

        resp = self.request.get(url, timeout=HTTP_TIMEOUT).json()
        return resp


    def weibo_fans(self, page):
        """
        新浪微博粉丝获取接口

        :return:
        """
        url = "https://api.weibo.cn/2/cardlist?networktype=wifi&uicode=10000011&moduleID=708&wb_version=3614&c={}" \
              "&i=33b49c7&s={}&ft=0&ua={}&wm=4209_8001&aid=01Ag5cLy3FoB70YjpXsukfQR2cFAGfKeH4rOQlqtrKkOJoRU4.&" \
              "fid=231016_-_selffans&uid={}&v_f=2&v_p=60&from=1084395010&gsid={}&imsi=460110825310084&lang=zh_CN&" \
              "lfid=100505{}_-_new&page={}&skin=default&count=20&oldwm=4209_8001&sflag=1&containerid=231016_-_selffans&" \
              "ignore_inturrpted_error=true&luicode=10000011&need_head_cards=0".format(self.system, self.get_keyword_s_uid,
                                                                                Weibo.UA, self.uid, self.gsid, self.uid, page)

        headers = {
            'Host': 'api.weibo.cn',
            'Connection': 'keep-alive',
            # 'X-Sessionid': '25bd1206-b88d-4049-b576-2968b5f1825f',
            'User-Agent': 'Nexus 6P_6.0_weibo_8.4.3_android',
            # 'X-Validator': 'yJbEMsve7M9Q6bco74DEc5/56m4EZETrQwZPGrqaQpw=',
            'X-Log-Uid': self.uid,
            'Accept-Encoding': 'gzip, deflate',
        }

        resp = self.request.get(url, timeout=HTTP_TIMEOUT).json()

        return resp


    def weibo_follower(self, page):
        """
        获取用户关注者信息
        :param page:
        :return:
        """
        url = "https://api.weibo.cn/2/cardlist?networktype=wifi&uicode=10000011&moduleID=708&wb_version=3614&c={}&" \
              "i=33b49c7&s={}&ft=0&ua={}&wm=4209_8001&aid=01Ag5cLy3FoB70YjpXsukfQR2cFAGfKeH4rOQlqtrKkOJoRU4.&" \
              "fid=231093_-_selffollowed&uid={}&v_f=2&v_p=60&from=1084395010&gsid={}&imsi=460110825310084&" \
              "lang=zh_CN&lfid=100505{}_-_new&page={}&skin=default&count=20&oldwm=4209_8001&sflag=1&" \
              "containerid=231093_-_selffollowed&ignore_inturrpted_error=true&luicode=10000011&" \
              "need_head_cards=0".format(self.system, self.get_keyword_s_uid, Weibo.UA, self.uid, self.gsid, self.uid, page)


        headers = {
            'Host': 'api.weibo.cn',
            'Connection': 'keep-alive',
            # 'X-Sessionid': '25bd1206-b88d-4049-b576-2968b5f1825f',
            'User-Agent': 'Nexus 6P_6.0_weibo_8.4.3_android',
            # 'X-Validator': 'yJbEMsve7M9Q6bco74DEc5/56m4EZETrQwZPGrqaQpw=',
            'X-Log-Uid': self.uid,
            'Accept-Encoding': 'gzip, deflate',
        }

        resp = self.request.get(url, timeout=HTTP_TIMEOUT).json()
        return resp


    def weibo_blog(self, page):
        """
        获取用户微博信息
        :param page:
        :return:
        """
        url = "https://api.weibo.cn/2/cardlist?networktype=wifi&uicode=10000011&moduleID=708&wb_version=3614&c={}" \
              "&i=33b49c7&s={}&ft=0&ua={}&wm=4209_8001&aid=01Ag5cLy3FoB70YjpXsukfQR0xIpwrpSs2EEaBNSyhfRPXHFk.&" \
              "fid=230413{}_-_WEIBO_SECOND_PROFILE_WEIBO&uid={}&v_f=2&v_p=60&from=1084395010&gsid={}&" \
              "imsi=460110825310084&lang=zh_CN&lfid=100505{}_-_new&page={}&skin=default&count=20&oldwm=4209_8001&" \
              "sflag=1&containerid=230413{}_-_WEIBO_SECOND_PROFILE_WEIBO&ignore_inturrpted_error=true&" \
              "luicode=10000011&need_head_cards=1".format(self.system, self.get_keyword_s_uid, Weibo.UA,
                                                          self.uid, self.uid, self.gsid, self.uid, page, self.uid)


        headers = {
            'Host': 'api.weibo.cn',
            'Connection': 'keep-alive',
            # 'X-Sessionid': '25bd1206-b88d-4049-b576-2968b5f1825f',
            'User-Agent': 'Nexus 6P_6.0_weibo_8.4.3_android',
            # 'X-Validator': 'yJbEMsve7M9Q6bco74DEc5/56m4EZETrQwZPGrqaQpw=',
            'X-Log-Uid': self.uid,
            'Accept-Encoding': 'gzip, deflate',
        }

        resp = self.request.get(url, timeout=HTTP_TIMEOUT).json()
        return resp



