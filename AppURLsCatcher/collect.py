# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2017/11/15
# @Author   : Zhangjw
# @File     : collect.py
# @Company  : Meiya Pico

import os
import re
import sys
import time
from AppURLsCatcher.config import BIN64_PATH, log
sys.path.append(BIN64_PATH)
import pyMyDatabase



class URLCollector(object):
    """
    获取需要进行取证的url
    """
    def __init__(self, apps_amf, cmf_path, amf_path, log):
        self.log = log
        self._conn_apps = self._sqlconn(apps_amf)
        self._conn_cmf = self._sqlconn(cmf_path)
        self._conn_amf = self._sqlconn(amf_path)

    def _sqlconn(self, sqlite_path):
        try:
            sqlconn = pyMyDatabase.SQLiteDatabase(sqlite_path, True)
        except Exception as e:
            self.log.exception("Connect sqlite failed, quit. Path:{}, error info:{}".format(sqlite_path, e))
            os._exit(1)
        return sqlconn

    def select_appnames(self):
        """
        获取TBL_APPURL_MANAGER中需要进行取证的APP集合
        :return:
        """
        app_list = []

        if not self._conn_cmf.tableExists("TBL_PRCD_APP_SELECTION_INFO"):
            self.log.info('table TBL_PRCD_APP_SELECTION_INFO is not exist')
            return app_list

        sql = "select DISTINCT LoginAccount from TBL_PRCD_APP_SELECTION_INFO WHERE AppName == 'AppURLs' ORDER BY Id"

        oSmt = pyMyDatabase.SQLiteStatement(self._conn_cmf, sql)
        while oSmt.executeStep():
            appname = self._get_column_value(oSmt.getColumn(0))
            app_list.append(appname)
        return app_list

    def select_all_urls(self, appname):
        """
        获取特定app下需要进行取证的URL
        :return:
        """
        # url_list = []
        url_set = set()
        if not self._conn_apps.tableExists("TBL_APPURL_MANAGER"):
            self.log.info('table TBL_APPURL_MANAGER is not exist.')
            return url_set

        sql = "select sAppName,sUrls from TBL_APPURL_MANAGER WHERE sAppName=='{}'".format(appname)

        oSmt = pyMyDatabase.SQLiteStatement(self._conn_apps, sql)
        while oSmt.executeStep():
            appname = self._get_column_value(oSmt.getColumn(0))
            url = self._get_column_value(oSmt.getColumn(1))
            # url_list.append((appname, url))
            url_set.add((appname, url))
        return url_set


    def select_done_urls(self, appname):
        """
        筛选出已经正常下载的资源集合
        :return:
        """
        # url_list = []
        url_set = set()

        if not self._conn_amf.tableExists("TBL_PRCD_URL_FILE_INFO"):
            self.log.info('table TBL_PRCD_URL_FILE_INFO is not exist.')
            return url_set

        sql = "select AppName,URL from TBL_PRCD_URL_FILE_INFO WHERE AppName=='{}'".format(appname)

        oSmt = pyMyDatabase.SQLiteStatement(self._conn_amf, sql)
        while oSmt.executeStep():
            appname = self._get_column_value(oSmt.getColumn(0))
            url = self._get_column_value(oSmt.getColumn(1))
            # url_list.append((appname, url))
            url_set.add((appname, url))
        return url_set

    def select_exception_urls(self, appname):
        """
        筛选出异常的URL
        :return:
        """
        url_set = set()

        if not self._conn_amf.tableExists("TBL_PRCD_URL_EXCEPTIONS_INFO"):
            self.log.info('table TBL_PRCD_URL_EXCEPTIONS_INFO is not exist.')
            return url_set

        sql = "select AppName,URL from TBL_PRCD_URL_EXCEPTIONS_INFO WHERE AppName=='{}'".format(appname)

        oSmt = pyMyDatabase.SQLiteStatement(self._conn_amf, sql)
        while oSmt.executeStep():
            appname = self._get_column_value(oSmt.getColumn(0))
            url = self._get_column_value(oSmt.getColumn(1))
            url_set.add((appname, url))
        return url_set

    def select_pending_urls(self, appname):
        """
        筛选出待处理的URL
        :return:
        """
        url_pending_set = set()
        url_all_set = self.select_all_urls(appname)
        url_done_set = self.select_done_urls(appname)
        url_exception_set = self.select_exception_urls(appname)
        url_pending_set = url_all_set - url_done_set - url_exception_set
        return url_all_set, url_pending_set

    @staticmethod
    def _get_column_value(column_object):
        if not isinstance(column_object, pyMyDatabase.SQLiteColumn):
            return None
        return column_object.getText("") if not column_object.isNull() else ''














