
import os
import time
import socket
import json
import threading
import winreg
import redis
from pyjdmallcatcher.monitor import Monitor
from pyjdmallcatcher import config
from common.adb_executor import AdbExecutor


def get_adb_path():
    """
    根据注册表获取adb命令
    :return: str
    """
    adb_path = '"{}platform-tools\\adbcloud.exe"'.format(config.ANDROID_PATH)
    return adb_path


class AVDManager(object):
    adb_path = get_adb_path()
    
    def __init__(self, log, android_path, address='127.0.0.1', port=6666):
        self.device_id = "emulator-5554"
        self.android_path = android_path
        self.log = log
        self.adb = AdbExecutor(get_adb_path(), config.log)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.redis_cli = self._connect_redis
        self.open_emulator()
        time.sleep(20)
        self.connect_emulator(address, port)

    @property
    def _connect_redis(self):
        """
        连接redis服务器,redis作为消息中间件用于和界面程序进行交互
        :return:
        """
        try:
            redis_pool = redis.ConnectionPool(host='127.0.0.1', port=53011,
                                              password='MyXACloudForensicFrom@2017@')
            redis_cl = redis.Redis(connection_pool=redis_pool)
        except Exception as e:
            self.log.error("Connection server failure, error info：%s" % str(e))
            self.avdmanager.close_emulator()
            os._exit(0)
        return redis_cl


    @property
    def net_status(self):
        """
        获取网络状态
        :return:
        """
        status = self.redis_cli.get('NetStatus')
        return status


    def open_emulator(self):
        """
        开启仿真器
        :return:
        """
        if not os.path.exists(self.android_path + "start.bat"):
            self.log.error("Android simulator boot script does not exist.")
            time.sleep(3)
            os._exit(0)

        os.chdir(self.android_path)
        try:
            p = os.popen("start.bat")
        except Exception as e:
            self.log.error("Run script failed. error info:{}".format(e))
            os._exit(1)
        self.log.info('The Android simulation environment start to run.')
        thread = threading.Thread(target=self.monitor, args=())
        thread.start()


    def close_emulator(self):
        """
        关闭仿真器
        :return:
        """
        try:
            self.adb.kill_server()
            self.adb.adb_shell('reboot -p')
            os.system("taskkill /im %s -f" % "qemu-system-i386.exe")
        except Exception as e:
            self.log.error("close android sdk exception:{}".format(e))
        self.log.info("The Android simulation environment has been closed")


    def connect_emulator(self, address, port, timeout=200):
        """
        连接虚拟机
        :return:
        """
        wait_time = 0
        resp = ''
        while True:
            if wait_time*3 > timeout:
                self.log.error("Wait for android emulator ready state timeout. Program exit.")
                self.close_emulator()
                os._exit(1)

            resp = self.adb.adb_shell('getprop cs.inited')
            self.log.info('Android emulator response:{}'.format(resp))
            if resp.find('OK') != -1:
                self.log.info('The android emulator is on.')
                break
            time.sleep(3)
            wait_time += 1
            if wait_time == 3:
                self.adb.connect_server()

        while True:
            try:
                forward_cmd = '{} forward tcp:{} tcp:{}'.format(AVDManager.adb_path, port, port)
                self.log.info(forward_cmd)
                self.adb.adb_forward(port)
                self.socket.connect((address, port))
            except Exception as e:
                self.log.warn("socket connect {}:{} exception, error info:{}".format(address, port, e))
                time.sleep(1)
                continue
            break
        self.log.info('Android emulator all ready.')


    def send_message(self, message):
        """
        发送socket消息
        :param message: str
        :return: None
        """
        except_count = 0
        while except_count<3:
            try:
                self.log.info('[-] socket send a message: {}'.format(message))
                self.socket.sendall(message.encode())
            except Exception as e:
                self.log.error("Sending a message to the server failed:{}. Attempts:{}.".format(e, except_count))
                except_count += 1
                continue
            break


    def recv_message(self, timeout = 300):
        """
        接受socket消息
        :param timeout: 接受消息超时时间
        :return: str
        """
        self.socket.settimeout(timeout)
        try:
            bytestr = self.socket.recv(4096)
            self.log.info('[+] socket recv a message: {}'.format(bytestr.decode()))
        except:
            self.log.error("Socket recv message timeout {}s, program exit.".format(timeout))
            return None
        return bytestr.decode()


    def recv_max_message(self, timeout = 300):
        """
        接受socket消息
        :param timeout: 接受消息超时时间
        :return: str
        """
        msg_bytes = b''
        while True:
            self.socket.settimeout(timeout)
            try:
                bytestr = self.socket.recv(4096)
                msg_bytes += bytestr
                msg_str = msg_bytes.decode()
            except Exception as e:
                self.log.error("Socket recv message exception,program exit. error info ".format(e))
                return ''

            try:
                msg_dict = json.loads(msg_str)
            except:
                continue
            self.log.info('[+] socket recv a message: {}'.format(msg_str))

            return msg_str


    def recv_message_ex(self, timeout = 300):
        """
        接受socket消息扩展
        :param timeout: 接受消息超时时间
        :return: str
        """
        self.socket.settimeout(timeout)

        # recv header
        try:
            bytestr = self.socket.recv(8).decode()
            self.log.info('[+] socket recv message header size: {}'.format(bytestr))
        except:
            self.log.error("Socket recv message header timeout {}s, program exit.".format(timeout))
            return None

        data_size = int(bytestr, 16)
        # recv body
        byte_data = b''
        while True:
            try:
                byte_data += self.socket.recv(data_size)
            except:
                self.log.error("Socket recv message body timeout {}s, program exit.".format(timeout))
                return None
            if len(byte_data) >= data_size:
                break
        return byte_data.decode()


    def monitor(self):
        """
        安卓模拟器进程监控
        :return:
        """
        m = Monitor()
        time.sleep(5)
        while 1:
            if self.net_status == b'2' or self.net_status == '2':
                self.log.error('The network has been disconnected and the program will quit.')
                self.close_emulator()
                break

            if not m.is_alive_proc(pname="qemu-system-i386.exe"):
                self.log.info('进程：qemu-system-i386.exe 已关闭。')
                break
            time.sleep(2)

        self.log.info('android sdk exception, program exit！')

        try:
            if m.is_alive_proc(pname="emulator64-crash-service.exe"):
                os.system("taskkill /im %s -f" % "emulator64-crash-service.exe")
        except Exception as e:
            self.log.info('kill emulator64-crash-service.exe failed.')

        try:
            if m.is_alive_proc(pname="emulator.exe"):
                os.system("taskkill /im %s -f" % "emulator.exe")
        except:
            self.log.info('kill emulator.exe failed.')

        time.sleep(2)
        os._exit(1)
