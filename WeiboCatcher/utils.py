# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2017/9/30
# @Author   : Zhangjw
# @File     : utils.py
# @Company  : Meiya Pico

import hashlib
import random
import time
import functools
import re
import os

from WeiboCatcher.config import log, SQL_CREATETABLE
from WeiboCatcher import config
from Cryptodome import Random
from Cryptodome.Hash import SHA
from Cryptodome.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Cryptodome.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Cryptodome.PublicKey import RSA
import base64

def md5_encode(str):
    '''
    将字符串进行md5加密
    :param str:
    :return: md5str
    '''
    m = hashlib.md5()
    m.update(str.encode("utf8"))
    return m.hexdigest()

def time_local(timestamp):
    if len(str(timestamp)) == 13:
        timestamp = timestamp/1000
    #转换成localtime
    time_local = time.localtime(timestamp)
    #转换成新的时间格式(2016-05-05 20:28:54)
    dt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
    return dt

def table_creater_del(tablename):
    '''
    创建表装饰器，在相应应用抓取前创建表
    :param tablename:要创建的表名
    :return:返回装饰函数
    '''

    def decorator(func):
        '''
        创建表的具体装饰函数
        :param func:调用函数
        :return:返回具体的包装函数
        '''

        def wrapper(self):
            # self.set_trans()
            if self.sqlconn.tableExists(tablename):
                self.sqlconn.execute('DROP TABLE %s' % tablename)
                self.sqlconn.execute(SQL_CREATETABLE[tablename])
            else:
                self.sqlconn.execute(SQL_CREATETABLE[tablename])
            # self.sqltrans.commit()
            return func(self)
        return wrapper
    return decorator


def table_creater(tablename):
    '''
    创建表装饰器，在相应应用抓取前创建表
    :param tablename:要创建的表名
    :return:返回装饰函数
    '''

    def decorator(func):
        def wrapper(self):
            # self.set_trans()
            if not self.sqlconn.tableExists(tablename):
                self.sqlconn.execute(SQL_CREATETABLE[tablename])
            # self.sqltrans.commit()
            return func(self)
        return wrapper
    return decorator


def try_catch(origin_func):
    def wrapper(*args, **kwargs):
        try:
            u = origin_func(*args, **kwargs)
            return u
        except Exception as e:
            log.error('函数:{} 执行异常, 异常信息: {}'.format(origin_func.__name__, str(e)))
    return wrapper


def try_except(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    def wrapper(*args, **kwargs):

        try:
            return function(*args, **kwargs)
        except Exception as e:
            # log the exception
            err = "There was an exception in "
            err += function.__name__
            err += ":{}".format(e)
            log.exception(err)
            pass

    return wrapper


def check_option(option, options = set()):
    """
    装饰器实现条件判断
    """
    def decorator(func):

        def wrapper():
            if option in options:
                return func()
            else:
                pass

        return wrapper

    return decorator


def clean_label(str):
    dr = re.compile(r'<[^>]+>', re.S)
    dd = dr.sub('', html)
    return dd


def sql_format(sql, *params):
    '''
    对SQL进行统一格式化，适应现有数据库操作函数
    :sql :参数未格式化的sql字符串
    :params :相关参数
    :return:返回格式化的sql字符串
    '''
    new_param = []
    for item in params[0]:
        if isinstance(item, str):
            item = item.replace('\'', '\'\'')
        new_param.append(item)
    sql = sql.replace("{}", "'{}'")
    sql = sql.format(*(tuple(new_param)))
    return sql.replace("'None'", "NULL")

def encrypt_rsa(decrypt_data):
    """
    加密和解密
    Master使用Ghost的公钥对内容进行rsa 加密
    :param decrypt_data:
    :return:
    """
    key_path = config.BIN64_PATH + '\Config\ghost-public.pem'
    print(key_path)
    with open(key_path) as f:
        key = f.read()
        rsakey = RSA.importKey(key)
        cipher = Cipher_pkcs1_v1_5.new(rsakey)
        cipher_text = base64.b64encode(cipher.encrypt(decrypt_data.encode()))
    return cipher_text.decode()


def decrypt_rsa(encrypt_data):
    """
    Ghost使用自己的私钥对内容进行rsa 解密
    :return:
    """
    with open('ghost-private.pem') as f:
        key = f.read()
        rsakey = RSA.importKey(key)
        cipher = Cipher_pkcs1_v1_5.new(rsakey)
        text = cipher.decrypt(base64.b64decode(encrypt_data), None)
    return text.decode()


def create_temp_path():
    """
    创建微博相关的临时目录
    :return:
    """
    if not os.path.exists(config.TEMP_PATH):
        os.makedirs(config.TEMP_PATH)


def time_format(timestr:str):
    """
    格式化时间
    :param timestr: 形如：'Wed Jan 03 17:32:51 +0800 2018'
    :return: 形如：2018-01-03 17:32:51
    """
    # a = 'Wed Jan 03 17:32:51 +0800 2018'
    try:
        struct_time = time.strptime(timestr, '%a %b %d %H:%M:%S %z %Y')
        x = time.localtime(time.mktime(struct_time))
    except:
        return timestr
    return time.strftime('%Y-%m-%d %H:%M:%S', x)


def get_rowcount(weibocatcher, table_name_list:list):
    row_count = 0
    # table_list = list(config.SQL_CREATETABLE.keys())
    for table_name in table_name_list:
        sql = 'select count(*) from {} where strSrcAccount = "{}"'.format(table_name, weibocatcher.weiboapi.uid)
        table_count = weibocatcher.sql_select(sql)
        if not table_count:
            continue
        row_count += int(table_count)

    return row_count