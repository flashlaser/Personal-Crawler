# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2017/11/15
# @Author   : Zhangjw
# @File     : main.py
# @Company  : Meiya Pico

import os
import time
import queue
import sys
import pathlib

from AppURLsCatcher.config import (
        APP_NAME,
        AppURLsConf,
        log
)

from AppURLsCatcher.catcher import AppURLsCatcher
from AppURLsCatcher.collect import URLCollector
from AppURLsCatcher.record import URLRecord

def main(dmf_path, cmf_path):
    # 判断cmf是否存在
    if not os.path.exists(cmf_path):
        log.error("File path does not exist, cmf_path:{}".format(cmf_path))
        sys.exit(1)

    cmf_folder = pathlib.Path(cmf_path).parent.__str__()

    # 构造amf路径 并创建
    amf_folder = pathlib.Path(cmf_path).parent.__str__() + '\\AppsAmf\\'
    if not os.path.exists(amf_folder):
        os.makedirs(amf_folder)

    amf_path = amf_folder + 'AppURLs.amf'
    if not os.path.exists(amf_path):
        try:
            with open(amf_path, 'wb+'):
                pass
        except Exception as e:
            log.error('failure to create a file， errorinfo：{}'.format(e))
            sys.exit(1)

    apps_amf = pathlib.Path(dmf_path).parent.__str__() + '\\AppsAmf\\AppUrls.amf'
    collect = URLCollector(apps_amf, cmf_path, amf_path, log)
    app_list = collect.select_appnames()
    if not app_list:
        log.error("There is no url to prove it.")
        sys.exit(1)

    cfg = AppURLsConf()
    record = URLRecord(amf_path, log)

    for appname in app_list:
        try:
            all_sources, pending_sources = collect.select_pending_urls(appname)
            appurls = AppURLsCatcher(appname=APP_NAME, subappname=appname, all_sources=all_sources,
                                     pending_sources=pending_sources, save_path=cmf_folder,record=record,
                                     config = cfg, log=log)
            appurls.progress.update(100, "获取完成({}条)".format(appurls.progress.exist))
        except Exception as e:
            log.exception("App [{}] Forensic exception. error info:{}".format(appname, e))
            continue

    time.sleep(5)
    os._exit(0)


