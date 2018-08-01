# -*- coding: utf-8 -*-

# @Function : 将已下载URL信息和异常URL写入数据库
# @Time     : 2017/10/13
# @Author   : zhangjw
# @File     : record.py
# @Company  : Meiya Pico

import sys
import os
import time
import threading
import queue
from AppURLsCatcher.config import BIN64_PATH, TBCREATE_SQL
from AppURLsCatcher import config
sys.path.append(BIN64_PATH)

import pyMyDatabase

class URLRecord(object):
    '''只管操作数据库'''
    def __init__(self, sqlitepath, log):
        # SQL语句缓冲队列
        self.record_queue = queue.Queue()
        self.log = log
        # 数据库链接
        self.sqlconn = self.connect_sqlite(sqlitepath)
        time.sleep(1)
        self.run()

    def __del__(self):
        pass


    def connect_sqlite(self, sqlitepath):
        try:
            conn = pyMyDatabase.SQLiteDatabase(sqlitepath, True)
        except Exception as e:
            self.log.error("Connect sqlite [{}] failed. error info:{}".format(sqlitepath, e))
            os._exit(1)
        return conn


    def create_table(self, tablename, drop_if_exist=False):
        if self.sqlconn.tableExists(tablename):
            self.log.info('table {} already exists'.format(tablename))
            if drop_if_exist:
                self.log.info('drop table:{}.'.format(tablename))
                self.sql_execute_try('DELETE FROM {}'.format(tablename))
                self.sql_execute_try(TBCREATE_SQL.get(tablename, ''))
        else:
            self.sql_execute_try(TBCREATE_SQL.get(tablename, ''))


    def record(self,sql):
        self.sql_execute_try(sql)


    def work(self):
        while True:
            source = self.record_queue.get()
            if isinstance(source, tuple):
                self.record(source[1])
            else:
                self.record(source)
            continue

    def run(self):
        if config.FIRST_FORENSIC_FLAG:
            self.create_table('TBL_PRCD_APP_CATCHEPROGRESS_INFO', True)
            config.FIRST_FORENSIC_FLAG = False
        else:
            self.create_table('TBL_PRCD_APP_CATCHEPROGRESS_INFO')
        self.create_table('TBL_PRCD_URL_EXCEPTIONS_INFO')
        self.create_table('TBL_PRCD_URL_FILE_INFO')
        thread = threading.Thread(target=self.work, args=())
        thread.start()

    def sql_execute_try(self, sql):
        first = True
        while True:
            try:
                self.sqlconn.execute(sql)
            except Exception as e:
                if first:
                    time.sleep(1)
                    first = False
                    continue
                else:
                    self.log.exception('sql_execute error! errorinfo:%s\r\nsql:%s' % (e, sql), exc_info=e)
                    return False
            break
        return True







