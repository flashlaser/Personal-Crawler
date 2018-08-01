# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2017/9/30
# @Author   : Zhangjw
# @File     : main.py
# @Company  : Meiya Pico

import time
import sys
import re
import os
import json
import requests
import pathlib
from WeiboCatcher import config
from WeiboCatcher import utils
from WeiboCatcher.config import log, APP_NAME
from WeiboCatcher.authreader import AuthReader
from WeiboCatcher.func_selector import FuncSelector

from WeiboCatcher.task_resume import TaskResume
from WeiboCatcher.weibo import Weibo
from WeiboCatcher.catcher import WeiboLogin, WeiboCatcher


def authread(tablename='TBL_PR_APP_AUTHINFO_CACHE'):
    """
    登录信息读取函数
    :param tablename: 表名（默认读取登陆信息表，只有在预登陆的时候读取CACHE表）
    :return: 账户密码的元组或None
    """
    auth = None
    auth_info_list = []
    try:
        auth = AuthReader(config.APPS_AMF_PATH, APP_NAME, tablename, log)
    except Exception as e:
        log.exception('read sina weibo login info failure. errorinfo:{}'.format(e))
        return
    login_list = auth.select()

    for account, token, login in login_list:
        if token:
            auth_token = json.loads(token.replace('[', '').replace(']', ''))
            if auth_token.get('touristmode', '') == '1':
                auth_token = {}
        else:
            auth_token = {}

        if login:
            login = json.loads(login)
            phone_pat = re.compile('^[0-9][0-9][0-9]{9}$')
            res = re.search(phone_pat, login.get('login'))
            if res:
                login['phone'] = login.get('login')
            else:
                login['phone'] = ''
        else:
            login = {}

        if auth_token or login:
            auth_info_list.append((account, auth_token, login))
    return auth_info_list


def write_session_info(auth_info:dict):
    """
    记录登录信息
    :return:
    """
    json_str = json.dumps(auth_info)
    with open(config.SESSION_SAVE_PATH, 'w+') as f:
        f.write(json_str)


def read_session_info():
    """
    读取登录信息
    :return:
    """
    try:
        with open(config.SESSION_SAVE_PATH, 'r') as file:
            data = file.read()
    except Exception as e:
        return
    return json.loads(data)


def pre_login(dmf_path, debug=False):
    log.info("sina mini blog start logging.")
    if debug:
        config.DEBUG = True

    config.APPS_AMF_PATH = '%s/Appsamf/Apps.amf' % (pathlib.Path(dmf_path).parent.__str__())
    # 预登陆不读取登陆信息表的数据，读取CACHE表的数据进行预登陆
    login_info_list = authread('TBL_PR_APP_AUTHINFO_CACHE')

    log.info(login_info_list)
    auth_info_dict = {}

    for account, auth_token, login_token in login_info_list:
        weibo = Weibo(account=account,
                      username=login_token.get('login', ''),
                      password = login_token.get('password',''),
                      phone=login_token.get('phone'),
                      uid=auth_token.get('uid', ''),
                      gsid=auth_token.get('gsid', ''),
                      system=auth_token.get('system', ''),
                      access=auth_token.get('access', '')
                      )

        signin = WeiboLogin(weibo, log, config.DEBUG)
        if signin.login_control():
            signin.prelogin_feedback(success=1)
            utils.create_temp_path()
            log.info(config.SESSION_SAVE_PATH)
            # 记录登陆信息
            auth_info_dict[weibo.account] = {
                'uid': weibo.uid,
                'system': weibo.system,
                'gsid': weibo.gsid,
                'access': weibo.access_token
            }
        else:
            signin.prelogin_feedback(success=0)

    if auth_info_dict:
        try:
            write_session_info(auth_info_dict)
        except Exception as e:
            log.error("write back authinfo error. errorinfo:{}".format(e))
        log.info('write back:{}'.format(auth_info_dict))

def read_params_list(cmf_path, account):
    paramlist = []
    try:
        paramliststr = FuncSelector(cmf_path, APP_NAME, account).get()
        if not paramliststr:
            log.error("WeiBo {} options null.".format(account))
            return
        paramlist = paramliststr.split('|')
    except Exception as e:
        log.exception("The fetch option data failed.")

    return paramlist

def main(dmf_path=None, cmf_path=None, debug = False):
    log.info('start fetch sina weibo cloud data.')
    if cmf_path:
        config.APPS_AMF_PATH = '%s/Appsamf/Apps.amf' % (pathlib.Path(dmf_path).parent.__str__())
        config.AMF_PATH = '{}/AppsAmf/{}.amf'.format(pathlib.Path(cmf_path).parent.__str__(), config.APP_NAME)
        if not os.path.exists(config.AMF_PATH):
            with open(config.AMF_PATH, 'w'):
                pass
    if debug:
        config.DEBUG = True

    login_info_list = authread(tablename='TBL_PR_APP_AUTHINFO')
    log.info('read authinfo from sqlite:{}'.format(login_info_list))

    token_dict = read_session_info()
    log.info('read authinfo from session.json:{}'.format(token_dict))
    if not token_dict:
        log.error("No useful login information is available.")
        return

    for account, token, login in login_info_list:
        log.info('account:{}, token:{}, login:{}'.format(account, token, login))
        progress = 0
        paramlist = read_params_list(cmf_path, account)
        if not paramlist:
            log.error('There are no options to get. account:{}'.format(account))
            continue

        account_info = token_dict.get(account, '')
        log.info(account_info)
        if not account_info:
            continue

        weibo = Weibo(account=account, uid=account_info.get('uid', ''), gsid=account_info.get('gsid', ''), system=account_info.get('system', ''), access=account_info.get('access', ''))
        wbcatcher = WeiboCatcher(weiboapi=weibo, amf_path=config.AMF_PATH, log=log)
        wbcatcher.pgbar.update(progress, "等待开始")

        func_dict_iphone = {
            'userinfo' : wbcatcher.submit_userinfo,
            # 'userinfo' : wbcatcher.fetch_weibo_userinfo,
            'fans' : wbcatcher.submit_fans_info,
            # 'fans': wbcatcher.fetch_weibo_fans,
            'follower' : wbcatcher.submit_follower_info,
            # 'follower' : wbcatcher.fetch_weibo_follower,
            "bloginfo" : wbcatcher.submit_bloginfo,
            # "bloginfo": wbcatcher.fetch_weibo_bloginfo,
            "message" : wbcatcher.submit_api_dialog_list,
            "album" : wbcatcher.submit_api_photos_info,
            "groupinfo" : wbcatcher.submit_api_group_members
        }

        func_table_dict = {
            #'userinfo' : ['TBL_PRCD_WEIBO_USERINFO'],
            'fans' : ['TBL_PRCD_WEIBO_FANS_INFO'],
            'follower' : ['TBL_PRCD_WEIBO_FOLLOW_INFO'],
            'bloginfo' : ['TBL_PRCD_WEIBO_BLOGINFO'],
            'message' : ['TBL_PRCD_WEIBO_PRIVATEMSG_INFO'],
            'album' : ['TBL_PRCD_WEIBO_PHOTO_INFO'],
            'groupinfo' : ['TBL_PRCD_WEIBO_GROUP_INFO', 'TBL_PRCD_WEIBO_GROUP_MEMBER_INFO', 'TBL_PRCD_WEIBO_GROUP_MESSAGE_INFO']
        }

        func_dict_android = {
            'userinfo' : wbcatcher.fetch_weibo_userinfo,
            #'fans' : wbcatcher.submit_fans_info,
            'fans': wbcatcher.fetch_weibo_fans,
            #'follower' : wbcatcher.submit_follower_info,
            'follower' : wbcatcher.fetch_weibo_follower,
            # "bloginfo" : wbcatcher.submit_bloginfo,
            "bloginfo": wbcatcher.fetch_weibo_bloginfo,
            "message" : wbcatcher.submit_api_dialog_list,
            "album" : wbcatcher.submit_api_photos_info,
            "groupinfo" : wbcatcher.submit_api_group_members
        }

        func_dict = {}

        if not weibo.gsid and weibo.uid:
            func_dict = func_dict_iphone
            default_params = ['userinfo', 'fans', 'follower', 'bloginfo']
            paramlist = list(set(default_params).intersection(set(paramlist)))

        if weibo.gsid and weibo.uid and weibo.system=='android':
            func_dict = func_dict_android

        if weibo.gsid and weibo.uid and weibo.system=='iphone':
            func_dict = func_dict_iphone

        if config.DEBUG:
            default_params = ['userinfo', 'fans', 'follower', 'bloginfo']
            paramlist = list(set(default_params).intersection(set(paramlist)))

        log.info('params:{}'.format(paramlist))

        # 免密获取微博信息
        block_per_option = 90 / len(paramlist)
        task_resume_inst = TaskResume(config.AMF_PATH, tuple(paramlist), log)
        task_resume_inst.init_progress(weibo.uid)

        for func_name in paramlist:
            if func_name:
                log.info(func_name)
                if not task_resume_inst.is_done(weibo.uid, func_name):
                    func = func_dict.get(func_name)
                    if callable(func):
                        try:
                            func()
                            progress += block_per_option
                        except Exception as e:
                            task_resume_inst.update(weibo.uid, func_name, 2)
                            log.exception("execute function:{} exception. {}".format(func_name, e))
                            continue
                        task_resume_inst.update(weibo.uid, func_name, 1)
                        wbcatcher.pgbar.update(int(progress), "正在获取")
                        print('正在获取：{}'.format(int(progress)))
        # 计算当前账号已取到的数据条数
        table_name_list = []
        for func in paramlist:
            table_name_list.extend(func_table_dict.get(func, []))
        row_count = utils.get_rowcount(wbcatcher, table_name_list)
        print("获取完成({}条)".format(row_count + 1))
        wbcatcher.pgbar.update(100, "获取完成({}条)".format(row_count + 1), finish='0')
    os._exit(0)
