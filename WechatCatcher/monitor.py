# -*- coding: utf-8 -*-

# @Function : 进程监控、进程信息获取模块
# @Time     : 2018/3/15
# @Author   : Zhangjw
# @File     : monitor.py
# @Company  : Meiya Pico

import psutil
from subprocess import PIPE
import configparser

import json
import time
import os
import sys

CONF_PATH = os.path.abspath(os.path.dirname(sys.argv[0])) + '/config/wechat_conf.ini'


class Monitor:
    monitor_process = False
    daemon_process = False
    proc_monitor_interval = 5
    getprocinfotimespan = 3
    conf_proc_name = []
    proc_conf_list = []

    def __init__(self):
        pass
        # self.read_conf()

    def read_conf(self):
        """ 读取进程信息配置文件 """
        try:
            config = configparser.ConfigParser()
            config.read(CONF_PATH)  # 读取ini配置文件
            self.conf_proc_name.append(config.get("PROCESS", "proc1"))
            self.conf_proc_name.append(config.get("PROCESS", "proc2"))
            self.conf_proc_name.append(config.get("PROCESS", "proc3"))
            self.proc_monitor_interval = config.get("DEFAULT", "ProcMonitorInterval")
        except Exception as e:
            print(e)

    @property
    def all_process(self):
        """ 获取当前全部进程集合 """
        allproc = {p for p in psutil.process_iter()}
        return allproc

    def load_process(self):
        allprocess = set()
        finprocessloop = 1
        try:
            for pname in self.conf_proc_name:
                for p in self.all_process:
                    if p.name() == pname:
                        self.proc_conf_list.append(p)
                        continue
        except Exception as e:
            raise Exception('获取当前所有进程信息失败.')

    def proc_status(self, pid=None, pname=None):
        """ 进程状态 """
        process = psutil.Process(pid)
        return process.status()

    def is_alive_proc(self,
                      proc=None,
                      pname=None,
                      pid=None):
        """根据进程名称或进程ID判断此进程是否存活"""
        if proc in self.all_process and proc.is_running():
            return True

        if pid:
            for p in self.all_process:
                try:
                    if pid == p.pid:
                        return True
                except Exception as e:
                    continue

        if pname:  # 需再对进程状态添加判断
            for p in self.all_process:
                try:
                    if pname == p.name():
                        return True
                except psutil.NoSuchProcess:
                    continue
        return False

    def get_proc_info(self, proc):
        '''
        获取进程信息
        :return:
        '''
        try:
            procinfo = {}

            procinfo['id'] = proc.pid
            procinfo['name'] = proc.name()
            procinfo['num_threads'] = proc.num_threads()
            procinfo['num_handles'] = proc.num_handles()
            procinfo['threads'] = proc.threads()
            procinfo['connections'] = proc.connections()
            procinfo['memory_percent'] = proc.memory_percent()
            procinfo['memory_info'] = proc.memory_info()
            procinfo['cpu_affinity'] = proc.cpu_affinity()
            procinfo['cpu_times'] = proc.cpu_times()
            procinfo['p_cpu_percent'] = proc.cpu_percent(interval=self.proc_monitor_interval)
            procinfo['t_cpu_percent'] = psutil.cpu_percent(interval=self.proc_monitor_interval)
            procinfo['cpu_count_real'] = psutil.cpu_count()
            procinfo['cpu_count_logical'] = psutil.cpu_count(logical=False)

            cpu_count_real = procinfo['cpu_count_real']
            cpu_count_logical = procinfo['cpu_count_logical']
            p_cpu_percent = procinfo['p_cpu_percent']
            t_cpu_percent = procinfo['t_cpu_percent']
            return (True, p_cpu_percent, t_cpu_percent, cpu_count_real, cpu_count_logical)

        except Exception as e:
            print(e)
            return (False, 0, 0, 0, 0)

        def startup(self, exepath):
            """开启进程"""
            commands = []
            try:
                if os.path.exists(exepath):
                    p = psutil.Popen(commands, stdout=PIPE)
            except Exception as e:
                print(e)

        def termination(self, proc=None, pname=None, pid=None):
            '''终止进程'''
            try:
                if proc in self.all_process:
                    proc.terminal()
                    os.system("taskkill /PID %s", proc.pid)
                    return True

                if pname:
                    for process in self.all_process:
                        if pname == process.name():
                            os.system("taskkill /PID %s", process.pid)
                            return True
                if pid:
                    for process in self.all_process:
                        if pid == process.pid:
                            os.system("taskkill /PID %s", pid)
                            return True
            except Exception as e:
                print('exception failed')
                return False

        def loop_controll(self):
            while 1:
                try:
                    # 获取配置文件中配置的所有进程
                    for process in self.proc_conf_list:
                        # 是否存活
                        if self.is_alive_proc(proc=process):
                            continue
                    # 进程挂掉则拉起
                    time.sleep(self.getprocinfospantime)
                except Exception as e:
                    print('loopControl.while :%s', e)
