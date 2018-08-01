# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2018/3/15
# @Author   : Zhangjw
# @File     : main.py
# @Company  : Meiya Pico

import time
import sys
import os
import json
import requests
import pathlib
from pyjdmallcatcher import config
from pyjdmallcatcher import tool
from pyjdmallcatcher.config import log
from pyjdmallcatcher.authreader import AuthReader
from pyjdmallcatcher.progressbar import ProcessBar
from pyjdmallcatcher.jdmall import JDMallApi
from pyjdmallcatcher.jdmallcatcher import JDMallCatcher


UUID = "860075034067059-f0c85053c666"
WHWSWSWWS = "23365dd33c3f244ed96729e5d915f36cc5add978d447c50c0f51582454"
INSTALLEDID = "4073884707724f0394720dce86eafc7f"


def authread(tablename='TBL_PR_APP_AUTHINFO_CACHE'):
    """
    登录信息读取函数
    :param tablename: 表名（默认读取登陆信息表，只有在预登陆的时候读取CACHE表）
    :return: 账户密码的元组或None
    """
    account = ''
    authtoken = {}
    authlogin = {}

    print(config.APPS_AMF_PATH)
    print(config.APP_NAME)

    try:
        auth = AuthReader(config.APPS_AMF_PATH, config.APP_NAME, tablename, log)
        account_list = auth.select()
        if not account_list:
            log.error("No access to useful login information,  program exit")
            return account, authtoken, authlogin
    except Exception as e:
        log.exception('Get login information exception. error info:{}'.format(e))
        return account, authtoken, authtoken

    account = account_list[0][0]
    if account_list[0][1].strip():
        authtoken = json.loads(account_list[0][1])
    if account_list[0][2].strip():
        authlogin = json.loads(account_list[0][2])

    return account, authtoken, authlogin


def start(dmf_path, cmf_path, debug=False):
    if cmf_path:
        # config.DOWNLOAD_PATH = '%s/%s' % (pathlib.Path(cmf_path).parent.__str__(), config.APP_NAME)
        config.CMF_PATH = cmf_path
        config.AMF_FOLDER = '%s/Appsamf/' % (pathlib.Path(cmf_path).parent.__str__())

        if not os.path.exists(config.AMF_FOLDER):
            os.makedirs(config.AMF_FOLDER)

        config.AMF_PATH = '{}\\AppsAmf\\{}.amf'.format(pathlib.Path(cmf_path).parent.__str__(), config.APP_NAME)

        if not os.path.exists(config.AMF_PATH):
            with open(config.AMF_PATH, 'wb+'):
                pass

        config.VERIFY_PICS_FOLDER = '{}\\AppsAmf\\jdmall_temp\\'.format(pathlib.Path(cmf_path).parent.__str__())

    if dmf_path:
        config.APPS_AMF_PATH = '%s/Appsamf/Apps.amf' % (pathlib.Path(dmf_path).parent.__str__())

    if debug:
        config.DEBUG = True

    account, authtoken, authlogin = authread()
    if not authtoken and not authlogin:
        return

    pgbar = ProcessBar(config.AMF_PATH, config.APP_NAME, account)
    pgbar.update(0, "等待开始")

    jdcom = JDMallApi(account, username = authlogin.get('login',''), password = authlogin.get('password',''),pin = authtoken.get('pin',''),
                     uuid = authtoken.get('uuid',UUID), wskey = authtoken.get('wskey',''), whwswswws = authtoken.get('whwswswws',WHWSWSWWS),
                     installtionId = authtoken.get('installtionId',INSTALLEDID))

    catcher = JDMallCatcher(jdcom, pgbar, config.AMF_PATH, log)
    if catcher.login_control():
        if catcher.fetch_user_info():
            catcher.fetch_address_info()
            catcher.fetch_order_info()
            catcher.fetch_order_detail()
            catcher.down.download_wait()
            # 计算总共获取到的数据条数
            table_name_list = [ 'TBL_PRCD_JDCOM_ORDER_DETAIL', 'TBL_PRCD_JDCOM_GOODS_INFO', 'TBL_PRCD_JDCOM_ADDRESS_INFO']
            row_count = tool.get_rowcount(catcher, table_name_list)
            if catcher.request_exception_count != 0:
                pgbar.update(100, "部分获取({}条)".format(row_count + 1), '1')
            else:
                pgbar.update(100, "获取完成({}条)".format(row_count + 1), '0')
        else:
            log.error("fetch wechat userinfo error.")
    else:
        time.sleep(5)
        pgbar.update(100, "因登录失败，此项未获取")

    catcher.avdmanager.close_emulator()
    return



def main(dmf_path, cmf_path, debug = False):
    start(dmf_path, cmf_path, debug)
    os._exit(0)




