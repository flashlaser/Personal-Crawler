# -*- coding: utf-8 -*-

# @Function : 日志模块
# @Time     : 2017/9/30
# @Author   : Zhangjw
# @File     : logger.py
# @Company  : Meiya Pico
import os
import sys
import time
import logging.handlers

class Logger(logging.Logger):
    def __init__(self, filename=None):
        super(Logger, self).__init__(self)

        self.filename = filename
        self.filepath = os.path.abspath(os.path.dirname(sys.argv[0])) +'\\log'

        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)

        # 创建一个handler，用于写入日志文件   
        #fh = logging.FileHandler(self.filepath + '\\' + self.filename)
        # 创建一个handler，用于写入日志文件 (每天生成1个，保留30天的日志)
        fh = logging.handlers.TimedRotatingFileHandler(self.filepath + '\\' + self.filename, 'D', 1, 30)
        fh.suffix = "%Y%m%d-%H%M.log"
        fh.setLevel(logging.DEBUG)

        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        hostname = os.environ['COMPUTERNAME']

        # 定义handler的输出格式
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [{}] [%(process)s] [%(thread)s] [%(filename)s:%(lineno)d] [WeiboCatcher] %(message)s'.format(hostname,))
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        self.addHandler(fh)
        self.addHandler(ch)


'''
#创建日志记录对象
log = Logger(filename='Weibo.log')
print(log.filepath)
#输出日志
log.info("日志模块消息!");
log.debug("日志模块调试消息!");
log.error("日志模块错误消息!");
log.debug('debug message')  
log.info('info message')  
log.warning('warning message')  
log.error('error message')  
log.critical('critical message') 
'''
