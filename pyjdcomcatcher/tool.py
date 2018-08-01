# -*- coding: utf-8 -*-

# @Function : 
# @Time     : 2018/1/16
# @Author   : LiPb (Mocha Lee)
# @File     : tool.py
# @Company  : Meiya Pico

import requests
from pyjdmallcatcher import config
import os
import time
import json
import random
import string
import re

def download_file(url, path, filename):
    """
    下载文件函数，目前用于下载订单商品的图片
    :param url: 文件url地址
    :param path: 保存路径
    :param filename: 保存名称
    :return: 保存的全路径
    """
    if not os.path.exists(path):
        os.makedirs(path)
    savepath = '{}/{}'.format(path, filename)
    cnt = 2
    while cnt > 0:
        try:
            r = requests.get(url, stream=True)
            with open(savepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=10240):
                    if chunk:
                        f.write(chunk)
                        f.flush()
            return savepath
        except Exception as e:
            cnt -= 1
            time.sleep(random.random())
    return None


def save_page(page_data, filename):
    """
    将页面原始数据保存起来，以备后续查看或定位问题
    :param page_data: html页面源码
    :param filename: 保存文件名
    :return: 无
    """
    if isinstance(page_data, str):
        page_data = page_data.encode(errors='ignore')

    path = '{}/source_page'.format(config.DOWNLOAD_PATH)
    if not os.path.exists(path):
        os.makedirs(path)
    path = '{}/{}.html'.format(path, filename)
    with open(path, 'wb+') as f:
        f.write(page_data)


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


def get_relpath(abspath):
    """
    根据绝对路径得出相对路径
    :param abspath: 绝对路径
    :return: 相对路径
    """
    if abspath:
        pos = abspath.find(config.APP_NAME)
        if pos != -1:
            return abspath[(pos-1):]
    return abspath


def get_verify_wait(appname, type, value, desc='', errno='0'):
    """
    获取验证码的阻塞函数
    :param appname: 应用名称
    :param type: 验证码类型
    :param value: 写入Redis的值
    :param desc: 其他描述
    :param errno: 错误码
    :return: Redis里写入的返回值
    """
    key = '{}_Verify_Send'.format(appname)
    value = {'type': type, 'value': value, 'errno': errno, 'desc': desc}
    config.log.info('redis info key : {} and value : {}'.format(key, value))
    redis_cl = config.redis_cl
    redis_cl.set(key, json.dumps(value))
    query_key = '{}_Verify_Sendback'.format(appname)
    while True:
        value = redis_cl.get(query_key)
        if value:
            value = json.loads(value).get('value', '')
            redis_cl.delete(query_key)
            return value
        time.sleep(3)


def notify_login_result(appname, type, value, desc='', errno='0'):
    """
    通知界面登录结果
    :param appname:
    :param type:
    :param value:
    :param desc:
    :param errno:
    :return:
    """
    key = '{}_Verify_Send'.format(appname)
    value = {'type': type, 'value': value, 'errno': errno, 'desc': desc}
    config.log.info('redis info key : {} and value : {}'.format(key, value))
    redis_cl = config.redis_cl
    redis_cl.set(key, json.dumps(value))
    

def get_rowcount(taobao):
    """
    根据表明查询该表的数据行数
    :param tablename: TaobaoDataParser实例
    :return: 行数计数
    """
    row_count = 0
    table_list = list(config.SQL_CREATETABLE.keys())
    for table_name in table_list:
        if taobao.table_exist(table_name):
            sql = 'select count(*) from {}'.format(table_name)
            table_count = taobao.sql_select(sql)
            if not table_count:
                continue
            row_count += int(table_count)
        else:
            config.log.info('table {} not exist.'.format(table_name))

    return row_count


def random_string(size=40):
    """
    获取随机字符串
    :param size: 字符串长度
    :return: 随机字符串
    """
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(size))


def save_cookies(cookies, user):
    if not cookies or not user:
        return
    cookies_str = json.dumps(cookies)
    if not os.path.exists(config.SESSION_SAVE_PATH):
        os.makedirs(config.SESSION_SAVE_PATH)
    filename = '{}{}_{}_cookie'.format(config.SESSION_SAVE_PATH, user, config.APP_NAME)
    with open(filename, 'wb+') as f:
        f.write(cookies_str.encode())


def load_cookies(user):
    if not user:
        return None
    filename = '{}{}_{}_cookie'.format(config.SESSION_SAVE_PATH, user, config.APP_NAME)
    if not os.path.exists(filename):
        return None
    try:
        if os.path.getmtime(filename) - time.time() > 600:  # cookie 超过10分钟就不再使用了
            os.remove(filename)
            return None
        else:
            with open(filename, 'rb+') as f:
                data = f.read()
            return json.loads(data.decode())
    except Exception as e:
        config.log.exception('load_cookies errors.', exc_info=e)
        return None


def create_temp_path():
    """
    创建淘宝相关的临时目录
    :return:
    """
    if not os.path.exists(config.TEMP_PATH):
        os.makedirs(config.TEMP_PATH)
    
    if not os.path.exists(config.SESSION_SAVE_PATH):
        os.makedirs(config.SESSION_SAVE_PATH)

def is_phone_num(phone:str):
    """
    判断是否是手机号码
    :param phone: 手机号码
    :return:
    """
    phone_pat = re.compile('^[0-9][0-9][0-9]{9}$')
    res = re.search(phone_pat, phone)
    if not res:
        return False
    return True

def get_rowcount(jdmallcatcher, table_name_list:list):
    row_count = 0
    # table_list = list(config.SQL_CREATETABLE.keys())
    for table_name in table_name_list:
        sql = 'select count(*) from {} where strSrcAccount = "{}"'.format(table_name, jdmallcatcher.jdcomapi.account)
        table_count = jdmallcatcher.sql_select(sql)
        if not table_count:
            continue
        row_count += int(table_count)

    return row_count
