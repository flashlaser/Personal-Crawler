# -*- coding: utf-8 -*-

# @Function : 微信、虚拟机、微信交易记录的一些封装操作
# @Time     : 2018/3/15
# @Author   : Zhangjw
# @File     : wechat.py
# @Company  : Meiya Pico

import requests
from requests.adapters import HTTPAdapter
import re
from copy import copy

from WechatCatcher.utils import (
    datetime_format,
    sql_format
)



class Wechat(object):
    def __init__(self, log, account, user=None, pwd=None):
        self.account = account
        self.user = user
        self.pwd = pwd
        self.phone = ''
        self.session = self.Session()
        self.log = log
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 6P Build/MDB08K; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/44.0.2403.117 Mobile Safari/537.36 MicroMessenger/6.6.3.1260(0x26060336) NetType/WIFI Language/zh_CN'
        }

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


    def __del__(self):
        pass

    def format_fee(self, fee):
        fee = int(fee) / 100
        return '%.2f' % fee

    def data_parser(self, data):
        """
        解析关键参数 exportkey 和 pass_ticket
        :param data:
        :return:
        """
        pat = '(.*?)exportkey=(.*?)&pass_ticket=(.*?)$'
        res = re.findall(pat, data)
        if res:
            _, new_key, ticket = res[0]
            return new_key, ticket
        return None

    def page_frame(self, key, ticket):
        """
        获取交易记录状态
        :param key: 关键字exportkey
        :param ticket: 关键字pass_ticket
        :return:
        """
        try:
            resp = self.session.get(
                url='https://wx.tenpay.com/userroll/readtemplate?t=userroll/index_tmpl&exportkey={}&pass_ticket={}'.format(
                    key, ticket),
                headers=self.headers
            )
        except Exception as e:
            self.log.error("page_frame status error:{}".format(e))
            return

        return resp.status_code


    def get_firstpage_bills(self,classify_type, key, ticket):
        """
        获取第一页bills
        :return:
        """
        self.page_frame(key, ticket)

        bills = []
        retparams = {}

        url = 'https://wx.tenpay.com/userroll/userrolllist?count=20&sort_type=1&classify_type={}&exportkey={}'.format(classify_type, key)

        self.headers.update({
            'Accept': '*/*',
            'X-Requested-With': 'com.tencent.mm',
            'Referer': 'https://wx.tenpay.com/userroll/readtemplate?t=userroll/index_tmpl&exportkey={}&pass_ticket={}'.format(key, ticket)
        })

        resp = self.session.get(url, headers=self.headers, verify=False).json()

        errcode =  resp.get('ret_code', 1)
        errmsg = resp.get('ret_msg', 'No Error Message.')
        bills = resp.get('record', [])
        # 获取分页的关键参数
        retparams['last_create_time'] = resp.get('last_create_time', '')
        retparams['last_bill_id'] = resp.get('last_bill_id', '')
        retparams['last_bill_type'] = resp.get('last_bill_type', '')
        retparams['last_trans_id'] = resp.get('last_trans_id', '')

        return errcode, errmsg, bills, retparams


    def get_nextpage_bills(self, classify_type, key, ticket, last_bill_params:dict):
        """
        获取下一页的交易记录
        :param classify_type: 交易记录类型 0-全部
        :param key: 关键参数
        :param ticket: 关键票据
        :param last_bill_params: 下一页的参数集
        :return: tuple
        """
        last_create_time = last_bill_params.get('last_create_time', '')
        last_bill_type = last_bill_params.get('last_bill_type', '')
        last_trans_id = last_bill_params.get('last_trans_id', '')
        last_bill_id = last_bill_params.get('last_bill_id', '')

        next_url = "https://wx.tenpay.com/userroll/userrolllist?exportkey={}&count=20&sort_type=1&start_time={}&" \
                    "last_bill_type={}&last_trans_id={}&last_create_time={}&classify_type" \
                    "={}".format(key, last_create_time, last_bill_type, last_trans_id, last_create_time, classify_type)

        if last_bill_id:
            next_url += '&last_bill_id={}'.format(last_bill_id)

        headers = copy(self.headers)
        headers.update({
            'Referer': 'https://wx.tenpay.com/?classify_type={}'.format(classify_type),
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,en-US;q=0.8'
        })
        response = self.session.get(url=next_url, headers=self.headers, verify=False).json()


        next_bills = []
        errcode = response.get('ret_code', 1)
        errmsg = response.get('ret_msg', 'No Error Message.')
        next_bills = response.get('record', [])
        over_flag = response.get('is_over', False)

        last_bill_params['last_create_time'] = response.get('last_create_time', '')
        last_bill_params['last_bill_id'] = response.get('last_bill_id', '')
        last_bill_params['last_bill_type'] = response.get('last_bill_type', '')
        last_bill_params['last_trans_id'] = response.get('last_trans_id', '')

        return errcode, errmsg, over_flag, next_bills, last_bill_params


    def get_bill_detail(self, exportkey, timestamp, trans_id, bill_type, bill_id):
        """
        获取账单详情
        :param exportkey: 关键字
        :param timestamp: 账单时间 时间戳
        :param trans_id: 交易id
        :param bill_type: 账单类型
        :param bill_id:  账单id
        :return:
        """

        url = 'https://wx.tenpay.com/userroll/userrolldetail?exportkey={}&create_time={}&trans_id={}&bill_type={}'.format(
            exportkey, timestamp, trans_id, bill_type)

        if bill_id:
            url += '&bill_id={}'.format(bill_id)

        resp = self.session.get(url=url, headers=self.headers, verify=False).json()

        return resp


















