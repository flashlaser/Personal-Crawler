# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2018/3/15
# @Author   : Zhangjw
# @File     : main.py
# @Company  : Meiya Pico

import time
import sys
import os
import re
import traceback
import json
import requests
import pathlib
import arrow

from WechatCatcher import utils
from WechatCatcher import config
from WechatCatcher.config import log, APP_NAME, ANDROID_PATH
from WechatCatcher.authreader import AuthReader
from WechatCatcher.progressbar import ProcessBar
from WechatCatcher.func_selector import FuncSelector
from WechatCatcher.wcps import WechatCatcher
from WechatCatcher.wechat import Wechat


def authread(tablename="TBL_PR_APP_AUTHINFO_CACHE"):
    """
    读取用户信息表
    :param tablename: 表名
    :return:
    """
    authlogin = {}
    account = ''

    try:
        auth = AuthReader(config.APPS_AMF_PATH, APP_NAME, tablename, log)
        account_list = auth.select()
        if not account_list:
            log.error("No access to useful login information,  program exit")
            return account,authlogin
    except Exception as e:
        log.error('Get login information exception, program exit. error info:{}'.format(e))
        return account,authlogin

    log.info(account_list)

    account = account_list[0][0]
    authlogin = json.loads(account_list[0][2])

    return account, authlogin


def read_params_list(cmf_path, account):
    paramlist = []
    try:
        selector = FuncSelector(cmf_path, config.APP_NAME, account)
        paramliststr, interval = selector.get()
        paramlist = paramliststr.split('|')
    except Exception as e:
        log.exception("The fetch option data failed：{}".format(e))

    return set(paramlist), interval


def start(dmf_path, cmf_path, debug = False):
    if cmf_path:
        config.CMF_PATH = cmf_path
        config.AMF_FOLDER = '%s/Appsamf/' % (pathlib.Path(dmf_path).parent.__str__())

        if not os.path.exists(config.AMF_FOLDER):
            os.makedirs(config.AMF_FOLDER)

        config.APPS_AMF_FOLDER = '%s/Appsamf/' % (pathlib.Path(dmf_path).parent.__str__())

        config.APPS_AMF_PATH = config.APPS_AMF_FOLDER + config.APPS_AMF_PATH

        config.AMF_PATH = '{}/AppsAmf/{}.amf'.format(pathlib.Path(cmf_path).parent.__str__(), config.APP_NAME)
        if not os.path.exists(config.AMF_PATH):
            with open(config.AMF_PATH, 'wb+'):
                pass

    if debug:
        config.DEBUG = True

    account,logininfo = authread()
    if not account or not logininfo:
        log.info('There is no valid login information.')
        return

    # 查询需要取证的勾选项和取证时间段
    paramsset, interval_key = read_params_list(cmf_path, account)
    # 计算取证截止时间
    format_months = config.INTERVAL_DICT.get(interval_key,0)
    print(format_months)
    if format_months != 0:
        now_time = arrow.now()
        print(now_time)
        print(format_months)
        config.CUT_OFF_TIME = now_time.shift(months=format_months).timestamp
        print(config.CUT_OFF_TIME)
        # config.CUT_OFF_TIME = now_time.timestamp

    pgbar = ProcessBar(config.AMF_PATH, APP_NAME, account)
    pgbar.update(0, "等待开始")
    wechat  = Wechat( log = log, account=account, user=logininfo.get('login'), pwd=logininfo.get('password'))
    catcher = WechatCatcher(log,  wechat, config.AMF_PATH, pgbar)

    keyword = catcher.login_control()
    if keyword:
        exportkey, ticket = catcher.wechat.data_parser(keyword)
        # 微信用户信息
        catcher.fetch_userinfo()
        # 获取微信交易记录
        catcher.fetch_billing_records(exportkey, ticket)
        time.sleep(2)
        # 获取红包详情
        if 'hb_detail' in paramsset:
            catcher.fetch_hb_detail()

        table_name_list = ['TBL_PRCD_WECHAT_BILL_RECORDS', 'TBL_PRCD_WECHAT_HBDETAIL_INFO']
        row_count = utils.get_rowcount(catcher, table_name_list)

        if catcher.request_exception_count != 0:
            pgbar.update(100, "部分获取({}条)".format(row_count + 1), '1')
        else:
            pgbar.update(100, "获取完成({}条)".format(row_count + 1), '0')
    else:
        pgbar.update(100, "因登录失败，此项未获取")

    catcher.avdmanager.close_emulator()
    return

def main(dmf_path, cmf_path, debug = False):
    start(dmf_path, cmf_path, debug)
    os._exit(0)











