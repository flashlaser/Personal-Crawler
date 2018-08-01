import requests
from requests.adapters import HTTPAdapter
import urllib

class JDMallApi(object):

    ANDROID_ID = "5bc94cc133059e9d"
    AREA = "27_2376_4343_0"

    HEADERS = {
               'Host': 'api.m.jd.com',
               'User-Agent': 'okhttp/3.4.1',
               'Content-Length': '12',
               'Charset': 'UTF-8',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
               'Cache-Control': 'no-cache',
               'Accept-Encoding': 'gzip,deflate',
               'Connection': 'Keep-Alive'
               }

    def __init__(self, account, username=None, password=None, phone=None, pin=None, uuid=None, wskey=None, whwswswws=None, installtionId=None):
        self.username = username
        self.password = password
        self.phone = ''
        self.uuid = uuid
        self.pin = self.format_pin(pin)
        self.wskey = wskey
        self.whwswswws = whwswswws
        self.installtionId = installtionId
        self.account = account
        self.cookie = "pin={};wskey={};whwswswws={};".format(self.pin, self.wskey, self.whwswswws)
        self.session = self.Session()


    @staticmethod
    def Session():
        """
        配置网络请求session及重试次数
        :return:
        """
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=3))
        s.mount('https://', HTTPAdapter(max_retries=3))
        return s

    def is_chinese(self, uchar):
        """判断一个unicode是否是汉字"""
        if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
            return True
        else:
            return False

    def format_pin(self, words):
        """
        格式化pin字段
        :return:
        """
        if self.is_chinese(words):
            return urllib.parse.quote(words)
        else:
            return words

    def get_userinfo(self):
        """
        获取用户信息
        :return:
        """
        JDMallApi.HEADERS['Cookie'] = self.cookie
        JDMallApi.HEADERS['jdc-backup'] = self.cookie

    def get_address_info(self, sign):
        """
        获取配送地址
        :return:
        """
        func_id = 'easyBuyGetAddress'
        body = 'body={}&'
        url = "https://api.m.jd.com/client.action?functionId={}&clientVersion=6.6.6&" \
              "build=57155&client=android&d_brand=Huawei&d_model=Nexus6P&osVersion=6.0&" \
              "screen=2392*1440&partner=jd-mxz&androidId={}&installtionId={}&lang=zh_CN&" \
              "uuid={}&area={}&networkType=4g&wifiBssid=unknown&{}".format(func_id,
              JDMallApi.ANDROID_ID, self.installtionId, self.uuid, JDMallApi.AREA, sign)

        headers = JDMallApi.HEADERS
        headers['Cookie'] = self.cookie
        headers['jdc-backup'] = self.cookie

        resp = self.session.post(url=url, headers=headers, verify=False, data=body).json()
        return resp

    def get_order_info(self, sign, body):
        """
        获取
        :return:
        """
        func_id = 'newUserAllOrderList'
        url = "https://api.m.jd.com/client.action?functionId={}&clientVersion=6.6.6&" \
              "build=57155&client=android&d_brand=Huawei&d_model=Nexus6P&osVersion=6.0&" \
              "screen=2392*1440&partner=jd-mxz&androidId={}&installtionId={}3&lang=zh_CN&" \
              "uuid={}&area={}&networkType=4g&wifiBssid=unknown&{}".format(func_id,
              JDMallApi.ANDROID_ID, self.installtionId,self.uuid, JDMallApi.AREA, sign)

        headers = JDMallApi.HEADERS
        headers['Cookie'] = self.cookie
        headers['jdc-backup'] = self.cookie
        resp = self.session.post(url=url, headers=headers, verify=False, data=body).json()
        return resp

    def get_order_detail(self, sign, body):
        """
        获取订单详情
        :param sign: 签名
        :param body: 请求包体
        :return:
        """
        func_id = "orderDetailInfo"
        url = "https://api.m.jd.com/client.action?functionId={}&clientVersion=6.6.6&" \
              "build=57155&client=android&d_brand=OnePlus&d_model=ONEPLUSA5000&" \
              "osVersion=7.1.1&screen=1920*1080&partner=jingdong&androidId={}&" \
              "installtionId={}&sdkVersion=25&lang=zh_CN&uuid={}&area={}&networkType=4g&" \
              "wifiBssid=unknown&{}".format(func_id,
                JDMallApi.ANDROID_ID, self.installtionId, self.uuid, JDMallApi.AREA, sign)

        headers = JDMallApi.HEADERS
        headers['Cookie'] = self.cookie
        headers['jdc-backup'] = self.cookie
        resp = self.session.post(url=url, headers=headers, verify=False, data=body).json()
        return resp

