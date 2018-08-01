# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2018/5/15
# @Author   : WangLiang
# @File     : adb_executor.py
# @Company  : Meiya Pico


import subprocess
import time
import random
import psutil


class AdbExecutor(object):
    """
    封装adb操作，在adb命令阻塞时进行超时重试
    """
    def __init__(self, path, log):
        self.TIMEOUT = 15
        self.PORT = '53012'
        self.SERVER_NAME = 'adbcloud.exe'
        self.device_id = "emulator-5554"
        self.adb_path = path
        self.log = log
        
    def connect_server(self):
        """
        暂时不使用
        先连接模拟器
        :return:
        """
        cmd = 'wait-for-device connect 127.0.0.1:5554'
        self._execute_cmd(cmd)
        
    def kill_server(self):
        """
        杀掉adb server进程
        :return:
        """
        # 先判断是否存在adb server
        server_id = self._get_adb_server_info()
        if server_id == -1:
            return True
        
        cmd_fail = False
        kill_cmd = '{} -P {} kill-server'.format(self.adb_path, self.PORT)
        child = subprocess.Popen(kill_cmd, stdout=subprocess.PIPE)
        try:
            child.wait(self.TIMEOUT)
        except subprocess.TimeoutExpired:
            self.log.info('Timeout: kill_server timeout')
            cmd_fail = True
            
        if cmd_fail:
            try:
                psutil.Process(server_id).terminate()
            except psutil.NoSuchProcess:
                return False
        
        return True
        
    def _get_adb_server_info(self):
        """
        获取adb server的进程id值
        :return: pid or -1
        """
        for proc in psutil.process_iter():
            try:
                if proc.name().lower() == self.SERVER_NAME:
                    if 'server' in proc.cmdline():
                        return proc.pid
            except psutil.NoSuchProcess:
                continue
            except psutil.AccessDenied:
                continue
        return -1
    
    def _execute_cmd(self, cmd_line, need_return=False):
        """
        执行adb命令
        :param cmd_line: 命令参数
        :return:
        """
        execute_line = '{} -P {} {}'.format(self.adb_path, self.PORT, cmd_line)
        cnt = 3
        while True:
            child = subprocess.Popen(execute_line, stdout=subprocess.PIPE)
            try:
                ret_code = child.wait(self.TIMEOUT)
                if ret_code == 0:
                    break
                else:
                    # execute failed
                    if cnt < 0:
                        return ''
                    else:
                        cnt -= 1
                    time.sleep(random.random() + 2)
            except subprocess.TimeoutExpired:
                self.log.info('Timeout: cmd is "{}" '.format(cmd_line))
                cnt -= 1
                self.kill_server()
                time.sleep(random.random() + 2)
        
        if need_return:
            text = child.stdout.read()
            return text.decode().strip()

    def adb_execute(self, cmd):
        return self._execute_cmd(cmd)
    
    def adb_shell(self, cmd):
        """
        封装adb shell命令
        :param cmd:
        :return:
        """
        shell_cmd = '-s {} shell {}'.format(self.device_id, cmd)
        return self._execute_cmd(shell_cmd, True)

    def adb_forward(self, port):
        """
        封装adb forward命令
        :return:
        """
        forward_cmd = '-s {} forward tcp:{} tcp:{}'.format(self.device_id, port, port)
        self._execute_cmd(forward_cmd)

    def adb_devices(self):
        devices_cmd = 'devices'
        self._execute_cmd(devices_cmd)
