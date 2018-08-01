# !/usr/bin/env python
# encoding: utf-8

# @Author: zhangjw
# @Company: Meiya Pico
# @File: threadpool.py
# @Time: 2018/3/26 10:44
# @Desc:

import queue
import threading
import time

from AppURLsCatcher.config import log


class WorkManager(object):
    def __init__(self, job_name, task_list, thread_num=10):
        self.job_name = job_name
        self.work_queue = queue.Queue()
        self.threads = []
        self.task_list = task_list
        self.__init_work_queue()
        self.__init_thread_pool(thread_num)

    def __init_thread_pool(self, thread_num):
        """ 初始化线程 """
        for i in range(thread_num):
            self.threads.append(Work(self.work_queue))

    def __init_work_queue(self):
        """ 初始化工作队列 """
        for task in self.task_list:
            self.add_job(self.job_name, task)

    def add_job(self, func, args):
        """ 添加一项工作入队 """
        # 任务入队，Queue内部实现了同步机制
        self.work_queue.put((func, args))

    def wait_allcomplete(self):
        """ 等待所有线程运行完毕 """
        for item in self.threads:
            if item.isAlive():
                item.join()

class Work(threading.Thread):
    def __init__(self, work_queue):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.start()

    def run(self):
        while True:
            try:
                #  任务异步出队，Queue内部实现了同步机制
                do, args = self.work_queue.get(block=False)
                try:
                    do(args)
                except Exception as e:
                    log.error('task execute exception. error info:{}'.format(e))
                    continue
                #  通知系统任务完成
                self.work_queue.task_done()
            except Exception as e:
                log.info('task thread exit. info:{}'.format(e))
                break


