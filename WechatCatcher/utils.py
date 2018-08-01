# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2018/3/15
# @Author   : Zhangjw
# @File     : utils.py
# @Company  : Meiya Pico

import time
import re

def datetime_format(datetime):
    if isinstance(datetime, int):
        datetime = str(datetime)
    if len(datetime) == 13:
        datetime = int(datetime) // 1000
    elif len(datetime) == 10:
        datetime = int(datetime)
    else:
        return datetime

    datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(datetime))
    return datetime

def try_except(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    #functools.wraps(function)
    def wrapper(*args, **kwargs):

        try:
            return function(*args, **kwargs)
        except Exception as e:
            # log the exception
            err = "There was an exception in "
            err += function.__name__
            err += ":{}".format(e)
            #log.error(err)
            print(err)
            pass
    return wrapper

def table_creater(tablename):
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


def format_fee(fee):
    """
    格式化金额 分 -> 元
    :param fee:
    :return:
    """
    fee = int(fee) / 100
    return '%.2f' % fee


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


def get_rowcount(wechatcatcher, table_name_list:list):
    row_count = 0
    # table_list = list(config.SQL_CREATETABLE.keys())
    for table_name in table_name_list:
        sql = 'select count(*) from {} '.format(table_name)
        table_count = wechatcatcher.sql_select(sql)
        if not table_count:
            continue
        row_count += int(table_count)

    return row_count
