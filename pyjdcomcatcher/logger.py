# -*- coding: utf-8 -*-

# @Function : 日志输出
# @Time     : 2017/9/15
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

        fh = logging.handlers.TimedRotatingFileHandler(self.filepath + '\\' + self.filename, 'D', 1, 30)
        fh.suffix = "%Y%m%d-%H%M.log"
        fh.setLevel(logging.DEBUG)

        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        hostname = os.environ['COMPUTERNAME']

        # 定义handler的输出格式
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [{}] [%(process)s] [%(thread)s] [%(filename)s:%(lineno)d] [pyjdmallcatcher] %(message)s'.format(hostname,))
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        self.addHandler(fh)
        self.addHandler(ch)

