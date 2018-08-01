# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2018/04/26
# @Author   : Zhangjw
# @File     : progressbar.py
# @Company  : Meiya Pico

import time
import queue
import threading
import os
import redis



class ProgressBar:
    def __init__(self, appname, subappname, total, exist,record_queue, log):
        self._running = True
        self.appname = appname
        self.subappname = subappname
        self.total = total
        self.exist = exist
        self.log = log
        self.record_queue = record_queue
        self.lock = threading.Lock()
        self.init_progress()
        self.redis_cli = self.redis_conn
        self.start()

    def terminate(self):
        self._running = False

    @property
    def redis_conn(self):
        try:
            redis_pool = redis.ConnectionPool(host='127.0.0.1', port=53011, password='MyXACloudForensicFrom@2017@')
            redis_cl = redis.Redis(connection_pool=redis_pool)
        except Exception as e:
            self.log.error("连接Redis服务器失败.错误信息：%s" % str(e))
        return redis_cl

    @property
    def add_count(self):
        self.lock.acquire()
        self.exist += 1
        self.lock.release()

    def run(self):
        percent = int((self.exist * 90)/self.total)
        last_exist = self.exist
        while self._running:
            if self.net_status == b'2':
                self.log.error('The network has been disconnected and the program exit.')
                os._exit(1)

            desc = ""
            if self.exist != 0 and self.exist < self.total:
                desc = '正在获取({}/{})'.format(self.exist, self.total)
            elif self.exist == 0:
                desc = '等待开始'
            elif self.exist == self.total:
                desc = '获取完成({}/{})'.format(self.total, self.total)
            percent = int((self.exist * 90)/self.total)
            if self.exist != last_exist:
                sql = '''
                    UPDATE TBL_PRCD_APP_CATCHEPROGRESS_INFO SET Percent = {},Description = '{}' WHERE AppName = '{}' 
                    AND LoginAccount = '{}' '''.format(percent, desc, self.appname, self.subappname)
                self.log.info('{} : {}'.format(self.subappname, desc))
                self.record_queue.put(sql)
            if self.exist == self.total:
                self.log.info("{} : {}-{} 获取完成.".format(self.subappname, self.exist, self.total))
                break
            last_exist = self.exist
            time.sleep(3)

    @property
    def net_status(self):
        status = self.redis_cli.get('NetStatus')
        return status

    def init_progress(self):
        """
        初始化进度
        :return:
        """
        sql = '''
               INSERT INTO TBL_PRCD_APP_CATCHEPROGRESS_INFO (AppName, LoginAccount, Percent, Description) VALUES('{}', '{}', '{}', '{}') 
               '''.format(self.appname, self.subappname, 0, '等待开始')
        self.record_queue.put(sql)

    def update(self, percent, desc=""):
        sql = '''
               UPDATE TBL_PRCD_APP_CATCHEPROGRESS_INFO SET Percent = {},Description = '{}' WHERE AppName = '{}' 
               AND LoginAccount = '{}' '''.format(percent, desc, self.appname, self.subappname)
        self.record_queue.put(sql)

    def start(self):
        thread = threading.Thread(target=self.run, args=())
        thread.start()



