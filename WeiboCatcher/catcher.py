# -*- coding: utf-8 -*-

# @Function : 微博app版云数据取证模块
# @Time     : 2017/9/30
# @Author   : Zhangjw
# @File     : mblog_app_catcher.py
# @Company  : Meiya Pico

import sys
import os
from WeiboCatcher.config import (
    BIN64_PATH,
    SQL_CREATETABLE,
    APP_NAME,
    REDIS_CONF,
    log
)
sys.path.append(BIN64_PATH)
import pyMyDatabase
import time
import datetime
import json
import re
import redis
import requests
import pathlib

from WeiboCatcher.downloader import Downloader,download_file
from WeiboCatcher.weibo import Weibo
from WeiboCatcher import utils
from WeiboCatcher.progressbar import ProcessBar
from WeiboCatcher.privatemsg import PrivateMsgRequest


class WeiboLogin(object):
    def __init__(self, weiboapi:Weibo, log, debug = False):
        self.weiboapi = weiboapi
        self.log = log
        self.redis_cli = self.redis_conn
        self.debug = debug

    @property
    def redis_conn(self):
        try:
            redis_pool = redis.ConnectionPool(host='127.0.0.1', port=53011, password='MyXACloudForensicFrom@2017@')
            redis_cl = redis.Redis(connection_pool=redis_pool)
        except Exception as e:
            log.error("连接Redis服务器失败.错误信息：%s" % str(e))
        return redis_cl

    def prelogin_feedback(self, success, haspreprocess=0, preprocessdone=0):
        """
        预登陆结果反馈
        # :param logintype: 登陆类型：token/pwd/sms
        :param success: 成功-1/失败-0
        :param haspreprocess: 默认为0
        :param preprocessdone:
        :return:
        """
        self.redis_cli.hset("PreCatchResult:WeiBo:{}".format(self.weiboapi.account), "Success", success)
        self.redis_cli.hset("PreCatchResult:WeiBo:{}".format(self.weiboapi.account), "LoginBy", self.login_type)
        self.redis_cli.hset("PreCatchResult:WeiBo:{}".format(self.weiboapi.account), "HasPreProcess", haspreprocess)
        self.redis_cli.hset("PreCatchResult:WeiBo:{}".format(self.weiboapi.account), "PreProcessDone", preprocessdone)

    def login_by_keywords(self):
        self.login_type = 'token'
        if not self.weiboapi.uid:
            self.log.error("免密登录失败，缺少关键字段uid.")
            time.sleep(5)
            return False
        # 有gsid, uid时 通过app端用户信息获取接口来做登录校验
        try:
            if self.weiboapi.uid and self.weiboapi.gsid:
                user = self.weiboapi.userinfo
        except Exception as e:
            self.log.error("免密登录失败, uid: {}, gsid: {}, system: {},异常信息：{}".format(self.weiboapi.uid, self.weiboapi.gsid, self.weiboapi.system, str(e)))
            return False

        # 只有uid时通过 调用web用户信息获取接口来做登录校验
        try:
            if self.weiboapi.uid and not self.weiboapi.gsid:
                user = self.weiboapi.userinfo
        except Exception as e:
            self.log.error("免密登录失败, uid: %s, gsid: %s, system: %s,异常信息：%s" % self.weiboapi.uid, self.weiboapi.gsid, self.weiboapi.system, str(e))
            return False

        if user and 'nick' in user.keys():
            return True

        return False

    def request_sms_code(self, sms_type:int):
        """
        向前端请求短信验证码
        :return:
        """
        checkcode = ''

        checkmsg = {
            "type": 0,
            # "errno": sms_type,
            "value": self.weiboapi.phone
        }

        if sms_type == 1:
            checkmsg['errno'] = 1
            checkmsg['desc'] = '验证码已发送至{}, 请输入短信验证码。'.format(self.weiboapi.phone)
        elif sms_type == 2 or 3:
            checkmsg['errno'] = 2
            checkmsg['desc'] = '校验失败，请重新输入。'
        elif sms_type == 4:
            checkmsg['errno'] = 3
            checkmsg['desc'] = '验证3次失败，请重新进行取证。'

        self.log.info(checkmsg)
        self.redis_cli.set('WeiBo_Verify_Send', json.dumps(checkmsg))

        retjson = ''
        while True:
            if self.debug:
                print("请输入手机号{}接收到的短信验证码:".format(self.weiboapi.phone))
                checkcode = input()
                return checkcode.strip()
            else:
                retjson = self.redis_cli.get('WeiBo_Verify_Sendback')
                self.log.info(retjson)
                if retjson:
                    self.redis_cli.delete('WeiBo_Verify_Sendback')
                    break
            time.sleep(2)

        checkcode = json.loads(retjson).get('value','').strip()

        return checkcode


    def login_by_sms(self):
        """
        手机验证码登陆
        :return:
        """
        errno = 0
        errmsg = ''
        checkcode = ''
        check_count = 1
        self.login_type = 'sms'
        self.weiboapi.system = 'android'

        try:
            errno, errmsg = self.weiboapi.request_sms()
            self.log.info(errmsg)
        except Exception as e:
            self.log.error("sendsms failure.errorinfo:{}".format(e))
            return False

        if errno != 0:
            # 请求短信验证码失败,
            checkmsg = {
                "type": 0,
                "value": "fail",
                "errno": 3,
            }

            checkmsg['desc'] = errmsg
            self.redis_cli.set('WeiBo_Verify_Send', json.dumps(checkmsg))
            return False
        else:
            while check_count <= 4:
                # 获取短信验证码 并 登陆
                checkcode = self.request_sms_code(check_count)
                if not checkcode:
                    check_count += 1
                    continue

                if not self.weiboapi.submit_smscode(checkcode):
                    self.log.error("SMS checkout failed, please reenter.")
                    check_count += 1
                    continue
                else:
                    return True
        return False


    def login_by_pwd(self):
        """
        账号密码登陆
        :return:
        """
        self.login_type = 'userpass'
        self.weiboapi.system = 'android'
        return self.weiboapi.login_by_userpass()


    def login_control(self):
        """
        登陆控制
        :return:
        """
        if self.weiboapi.uid and self.weiboapi.gsid and self.weiboapi.system:
            if self.login_by_keywords():
                self.log.info("login success by keywords.")
                return True
            else:
                self.log.info("login failure by keywords.")

        if self.weiboapi.username and self.weiboapi.password:
            if self.login_by_pwd():
                self.log.info("login success by password.")
                # 将获取的关键参数回写数据库
                return True
            else:
                self.log.info("login failure by password.")

        if self.weiboapi.phone:
            if self.login_by_sms():
                self.log.info("login success by SMS.")
                # 将获取的关键参数回写数据库
                self.log.info(self.weiboapi.system)
                return True
            else:
                self.log.info("login failure by SMS.")

        if self.weiboapi.uid:
            if self.login_by_keywords():
                self.log.info("login success by uid.")
                return True
            else:
                self.log.info("login failure by uid.")

        return False


class WeiboCatcher(object):
    def __init__(self, log,
                       weiboapi ,
                       amf_path = None
                 ):
        # amf文件路径
        self.weiboapi = weiboapi
        self.login_type = ''
        self.amf_path = amf_path
        # 下载选项
        self.log = log
        self._oTrans = None
        self.redis_cli = self.redis_conn
        # 图片下载器
        self.download = Downloader()
        self.record_count = 0
        self._oDb = pyMyDatabase.SQLiteDatabase(self.amf_path, True)
        self.download_dir = pathlib.Path(self.amf_path).parent.parent.__str__()
        self.pgbar = ProcessBar(self.amf_path, APP_NAME, self.weiboapi.account)
        # 用户名称
        self.nick_name = ''

    def __del__(self):
        '''
        析构函数 关闭连接
        :return:
        '''
        self.sqlconn.close()

    @property
    def redis_conn(self):
        try:
            redis_pool = redis.ConnectionPool(host='127.0.0.1', port=53011, password='MyXACloudForensicFrom@2017@')
            redis_cl = redis.Redis(connection_pool=redis_pool)
        except Exception as e:
            log.error("连接Redis服务器失败.错误信息：%s" % str(e))
        return redis_cl

    @property
    def sqlconn(self):
        return self._oDb

    def parse_weibo_userinfo(self, userinfo):
        """
        解析新浪微博用户信息数据
        :return:
        """
        uid = userinfo.get('idstr', '')
        screen_name = userinfo.get('screen_name', '')
        self.nick_name = screen_name
        province = userinfo.get('province', '')
        city = userinfo.get('city', '')
        address = province + ' ' + city
        description = userinfo.get('description', '')
        blog_url = userinfo.get('url', '')
        gender = userinfo.get('gender', '')
        followers_count = userinfo.get('followers_count', '')
        friends_count = userinfo.get('friends_count', '')
        statuses_count = userinfo.get('statuses_count', '')
        favourites_count = userinfo.get('favourites_count', '')
        created_at = userinfo.get('created_at', '')
        created_at = utils.time_format(created_at)
        # 头像图片url
        profile_image_url = userinfo.get('profile_image_url', '').replace(' ','')
        # 大号头像url
        avatar_large = userinfo.get('avatar_large', '').replace(' ','')

        profile_image_name = uid + '.jpg'
        profile_image_relpath = "/WeiBo/picture/{}/friends/{}".format(self.weiboapi.uid, profile_image_name)
        profile_image_path = self.download_dir + "/WeiBo/picture/{}/friends/".format(self.weiboapi.uid)

        self.download.add_task(url=avatar_large, path=profile_image_path, name=profile_image_name)

        profile_url = 'https://m.weibo.cn/u/{}'.format(uid)

        sql = '''INSERT INTO "TBL_PRCD_WEIBO_USERINFO" ("strWeiboNickName", "strWeiboAccountNum", "strWeiboAccountID",
                "strWeiboGender","strUserDesc","strPhotoPath","strWeiboFaceURL","strWeiboCity","strWeiboBlog","strCreateAt",
                "strSunRank","strAttNum","strBlogNum","strFansNum") VALUES({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'''

        params = (screen_name, self.weiboapi.username, self.weiboapi.uid, gender, description, profile_image_relpath, profile_url,
                  address, blog_url, created_at, '', friends_count, statuses_count, followers_count)

        return utils.sql_format(sql, params)


    def fetch_weibo_userinfo(self):
        """
        获取新浪微博用户数据
        :return:
        """

        self.log.info("【用户信息】")
        self.create_table('TBL_PRCD_WEIBO_USERINFO', False)

        userinfo = {}
        try:
            userinfo = self.weiboapi.weibo_userinfo()
        except Exception as e:
            self.log.exception("fetch weibo userinfo exception. errorinfo:{}".format(e))

        if userinfo:
            sql = self.parse_weibo_userinfo(userinfo)
        else:
            sql = sql = '''INSERT INTO "TBL_PRCD_WEIBO_USERINFO" ("strWeiboAccountNum", "strWeiboAccountID") VALUES({}, {})'''
            params = (self.weiboapi.username, self.weiboapi.uid)
            sql = utils.sql_format(sql, params)

        self.sql_execute_try(sql)

    def parse_weibo_fans(self, fans):
        """
        解析粉丝信息
        :return:
        """
        desc = fans.get('desc1','')

        user = {}
        user = fans.get('user', {})

        uid = user.get('id', '')
        screen_name = user.get('screen_name', '')
        # 头像图片url
        profile_image_url = user.get('profile_image_url', '').replace(' ','')
        # 大号头像url
        avatar_large = user.get('avatar_large', '').replace(' ','')
        followers_count = user.get('followers_count', '')
        friends_count = user.get('friends_count', '')
        status_count = user.get('status_count', '')

        profile_image_name = str(uid) + '.jpg'
        profile_image_relpath = "/WeiBo/picture/{}/friends/{}".format(self.weiboapi.uid, profile_image_name)
        profile_image_path = self.download_dir + "/WeiBo/picture/{}/friends/".format(self.weiboapi.uid)
        self.download.add_task(url=avatar_large, path=profile_image_path, name=profile_image_name)

        profile_url = 'https://m.weibo.cn/u/{}'.format(uid)

        sql = '''
                INSERT INTO "TBL_PRCD_WEIBO_FANS_INFO" ("strWeiboNickname","strPhotoPath","strWeiboFaceURL","strPageURL","strUserDesc", "strStatusCount", 
                "strWeiboFollowerAmount","strWeiboFollowingAmount","strWeiboUID","strWeiboRank", "strSrcAccount") VALUES 
                ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
                '''

        params = (screen_name, profile_image_relpath, profile_url, profile_url, desc, status_count, followers_count, friends_count, uid, '', self.weiboapi.uid )

        return utils.sql_format(sql, params)

    def fetch_weibo_fans(self):
        """
        获取用户粉丝列表
        :return:
        """
        self.log.info("【粉丝信息】")
        self.create_table('TBL_PRCD_WEIBO_FANS_INFO', False)

        page = 1
        break_flag = False
        while not break_flag:
            try:
                result = self.weiboapi.weibo_fans(page)
            except Exception as e:
                self.log.exception('request weibo fans infomation exception. errorinfo:{}'.format(e))

            card_list = []
            try:
                card_list = result.get('cards', [])
            except:
                break

            if not card_list:
                break

            for card in card_list:
                if card.get('card_type','') == 11 and card.get('itemid', '') == '1031031008_':
                    fans_list = []
                    fans_list = card.get('card_group', [])
                    if not fans_list:
                        break_flag = True

                    for fans in fans_list:
                        try:
                            sql = self.parse_weibo_fans(fans)
                            self.sql_execute_try(sql)
                        except Exception as e:
                            self.log.exception('parse weibo fans info exception. errinfo:{}'.format(e))
                            continue
            page += 1
        self.download.download_wait()


    def parse_weibo_follower(self, fans):
        """
        解析粉丝信息
        :return:
        """
        desc = fans.get('desc1', '')

        user = {}
        user = fans.get('user', {})

        uid = user.get('id', '')
        screen_name = user.get('screen_name', '')
        # 头像图片url
        profile_image_url = user.get('profile_image_url', '').replace(' ', '')
        # 大号头像url
        avatar_large = user.get('avatar_large', '').replace(' ', '')
        followers_count = user.get('followers_count', '')
        friends_count = user.get('friends_count', '')
        status_count = user.get('status_count', '')

        profile_image_name = str(uid) + '.jpg'
        profile_image_relpath = "/WeiBo/picture/{}/friends/{}".format(self.weiboapi.uid, profile_image_name)
        profile_image_path = self.download_dir + "/WeiBo/picture/{}/friends/".format(self.weiboapi.uid)

        self.download.add_task(url=avatar_large, path=profile_image_path, name=profile_image_name)

        profile_url = 'https://m.weibo.cn/u/{}'.format(uid)

        sql = '''
              INSERT INTO "TBL_PRCD_WEIBO_FOLLOW_INFO" ("strWeiboNickname", "strPhotoPath", "strWeiboFaceURL","strPageURL","strUserDesc",
              "strStatusCount","strWeiboFollowerAmount","strWeiboFollowingAmount","strWeiboUID","strWeiboRank", "strSrcAccount")
               VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}) 
               '''

        params = (screen_name, profile_image_relpath, profile_url, profile_url, desc, status_count, followers_count, friends_count, uid, '',
        self.weiboapi.uid)

        return utils.sql_format(sql, params)

    def fetch_weibo_follower(self):
        """
        获取用户粉丝列表
        :return:
        """

        self.log.info("【关注者信息】")
        self.create_table('TBL_PRCD_WEIBO_FOLLOW_INFO', False)

        page = 1
        while True:
            try:
                result = self.weiboapi.weibo_follower(page)
            except Exception as e:
                self.log.exception('request weibo fans infomation exception. errorinfo:{}'.format(e))

            card_list = []
            try:
                card_list = result.get('cards', [])
            except:
                break

            if not card_list:
                break

            for card in card_list:
                if card.get('card_type','') == 11 and card.get('itemid', '') == '2310930026_1_ _':
                    follower_list = []
                    follower_list = card.get('card_group', [])
                    if not follower_list:
                        break_flag = True

                    for follower in follower_list:
                        try:
                            sql = self.parse_weibo_follower(follower)
                            self.sql_execute_try(sql)
                        except Exception as e:
                            self.log.exception('parse weibo fans info exception. errinfo:{}'.format(e))
                            continue
            page += 1
        self.download.download_wait()


    def parse_weibo_mblog(self, mblog:dict):
        """
        解析微博数据
        :return:
        """

        mblog_id = mblog.get('id', '')
        content = mblog.get('text', '')
        source = mblog.get('source', '')
        created_at = mblog.get('created_at', '')
        created_at = utils.time_format(created_at)
        reposts_count = mblog.get('reposts_count', '')
        comments_count = mblog.get('comments_count', '')
        attitudes_count = mblog.get('attitudes_count', '')

        sender_user = mblog.get('user', {})
        sender_nick = sender_user.get('screen_name', '')

        pics_dict = {}
        pics_dict = mblog.get('pic_infos', {})

        attachments_name = ''

        for key, value in pics_dict.items():
            large_pic = value.get('large', {})
            large_url = large_pic.get('url','').replace(' ','')
            large_name = key + '.jpg'
            large_abspath = self.download_dir + "/WeiBo/picture/{}/photos/".format(self.weiboapi.uid)
            large_relpath = '/WeiBo/picture/{}/photos/{}'.format(self.weiboapi.uid, large_name)
            self.download.add_task(url=large_url, path=large_abspath, name=large_name)
            attachments_name += '\"{}\";'.format(large_relpath)

        retweeted_status = {}
        retweeted_status = mblog.get('retweeted_status', {})
        prev_created_at = retweeted_status.get('created_at', '')
        prev_created_at = utils.time_format(prev_created_at)
        prev_mblog_id = retweeted_status.get('id', '')
        prev_content = retweeted_status.get('text', '')
        prev_sender_user = retweeted_status.get('user', {})
        prev_sender_nick = prev_sender_user.get('screen_name', '')
        prev_sender_uid = prev_sender_user.get('idstr', '')
        prev_source = retweeted_status.get('source', '')
        prev_picture_dict = []
        prev_picture_dict = retweeted_status.get('pic_infos', {})
        prev_attachments_name = ''

        for key, value in prev_picture_dict.items():
            large_pic = value.get('large', {})
            large_url = large_pic.get('url','').replace(' ','')
            large_name = key + '.jpg'
            large_abspath = self.download_dir + "/WeiBo/picture/{}/photos/".format(self.weiboapi.uid)
            large_relpath = '/WeiBo/picture/{}/photos/{}'.format(self.weiboapi.uid, large_name)
            self.download.add_task(url=large_url, path=large_abspath, name=large_name)
            prev_attachments_name += '\"{}\";'.format(large_relpath)


        sql = '''INSERT INTO "TBL_PRCD_WEIBO_BLOGINFO" ("strWeiboSessionID","strWeiboContent","strWeiboAttachmentName",
                 "strWeiboAttachmentLocalPath","strWeiboSendTime","strSrcAccount","strWeiboSenderNick","strSource",
                 "strWeiboAttiCount","strWeiboForwardCount","strWeiboCommentCount",
                 "strPrevCreatedAt","strPrevMblogID","strPrevContent","strPrevUID","strPrevSource") VALUES
                 ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
            '''

        params = (mblog_id, content, attachments_name, prev_attachments_name,created_at, self.weiboapi.uid, sender_nick,
                  source, attitudes_count, reposts_count, comments_count, prev_created_at, prev_mblog_id,
                  prev_content, prev_sender_uid, prev_source)

        return utils.sql_format(sql, params)


    def fetch_weibo_bloginfo(self):
        """
        获取用户发布的微博信息
        :return:
        """

        self.log.info("【新浪为微博数据】")
        self.create_table('TBL_PRCD_WEIBO_BLOGINFO', False)

        page = 1
        while True:
            try:
                result = self.weiboapi.weibo_blog(page)
            except Exception as e:
                self.log.exception('request weibo fans infomation exception. errorinfo:{}'.format(e))

            card_list = []
            try:
                card_list = result.get('cards', [])
            except:
                break

            if not card_list:
                break

            mblog_list = []
            for card in card_list:
                if card.get('card_type','') == 9:
                    mblog = {}
                    mblog = card.get('mblog', {})
                    if mblog:
                        mblog_list.append(mblog)
                        try:
                            sql = self.parse_weibo_mblog(mblog)
                            self.sql_execute_try(sql)
                        except Exception as e:
                            self.log.exception('parse weibo fans info exception. errinfo:{}'.format(e))
                            continue

            if len(mblog_list) == 0:
                break
            page += 1
        self.download.download_wait()

    def submit_userinfo(self):
        '''
        @获取【用户信息】并提交至数据库
        :return:
        '''
        self.log.info("【用户信息】")
        self.create_table('TBL_PRCD_WEIBO_USERINFO', False)

        user = self.weiboapi.userinfo
        self.nick_name = user.get('nick', '')
        if not user:
            sql = '''INSERT INTO "TBL_PRCD_WEIBO_USERINFO" ("strWeiboAccountNum", "strWeiboAccountID") VALUES({}, {})'''

            params = (self.weiboapi.username, self.weiboapi.uid,)

            self.sql_execute_try(utils.sql_format(sql, params))
            return


        sql = '''INSERT INTO "TBL_PRCD_WEIBO_USERINFO" ("strWeiboNickName", "strWeiboAccountNum", "strWeiboAccountID",
        "strWeiboGender","strUserDesc","strPhotoPath","strWeiboFaceURL","strWeiboCity","strWeiboBlog","strCreateAt",
        "strSunRank","strAttNum","strBlogNum","strFansNum") VALUES({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'''

        params = (user.get('nick',''), self.weiboapi.username, user.get('uid',''), user.get('gender',''),
                  user.get('description',''), user.get('profile_image_path',''), user.get('profile_url',''),
                  user.get('address',''), user.get('blog',''),user.get('created_at',''), user.get('urank', ''),
                  user.get('follow_count',''), user.get('statuses_count',''), user.get('followers_count',''))

        self.sql_execute_try(utils.sql_format(sql, params))

    def submit_bloginfo(self):
        '''
        @获取并提交微博信息
        :param page_space: 一次获取并提交的分页数,page_sapce=None 一次性提交
        :return:
        '''
        self.log.info("【微博信息】")
        self.create_table('TBL_PRCD_WEIBO_BLOGINFO', False)

        sql = '''INSERT INTO "TBL_PRCD_WEIBO_BLOGINFO" ("strWeiboSessionID","strWeiboContent","strWeiboSendTime","strSrcAccount",
                "strWeiboSenderNick","strSource","strWeiboAttiCount","strWeiboForwardCount","strWeiboCommentCount",
                "strPrevCreatedAt","strPrevMblogID","strPrevContent","strPrevUID","strPrevSource") VALUES
                ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
                '''

        page_total, blog_total = self.weiboapi.weibo_amount
        page_list = []

        for page in range(1, page_total + 1):
            count, one_list = self.weiboapi.get_weibo_onepage(page)
            for mblog in one_list:
                try:
                    params = (mblog.get('mblog_id', ''), mblog.get('content', ''), mblog.get('created_at', ''),
                              mblog.get('from', ''),
                              mblog.get('nick', ''), self.weiboapi.account, mblog.get('attitudes_count', ''),
                              mblog.get('reposts_count', ''),
                              mblog.get('comments_count', ''), mblog.get('prev_createdat', ''),
                              mblog.get('prev_id', ''), mblog.get('prev_content', ''),
                              mblog.get('prev_uid', ''), mblog.get('prev_source', ''))
                    self.sql_execute_try(utils.sql_format(sql, params))
                except Exception as e:
                    self.log.error("获取用户【微博信息】异常. {}\r\n 错误信息:{}".format(str(mblog), e))
                    continue

    def submit_fans_info(self):
        """
        @获取【粉丝】信息并提交至数据库
        :return:
        """
        self.log.info("【粉丝信息】")
        self.create_table('TBL_PRCD_WEIBO_FANS_INFO', False)

        sql = '''
        INSERT INTO "TBL_PRCD_WEIBO_FANS_INFO" ("strWeiboNickname","strPhotoPath","strPageURL","strUserDesc", "strStatusCount", 
        "strWeiboFollowerAmount","strWeiboFollowingAmount","strWeiboUID","strWeiboRank", "strSrcAccount") VALUES 
        ({}, {}, {}, {}, {}, {}, {}, {}, {}, {})
        '''
        page_total, fans_total = self.weiboapi.fans_amount_beta
        for page in range(1, page_total + 1):
            count, one_list = self.weiboapi.get_fans_onepage(page)
            for fans in one_list:
                try:
                    profile_image_path = self.download_dir + "/WeiBo/picture/{}/friends/".format(self.weiboapi.uid)
                    self.download.add_task(url=fans['profile_image_url'], path=profile_image_path, name=fans['profile_image_name'])

                    params = (fans['nick'], fans['profile_image_path'], fans['profile_url'], fans['desc'],
                              fans['statuses_count'], fans['followers_count'], fans['follow_count'],
                              fans['uid'], fans['rank'], self.weiboapi.uid)

                    self.sql_execute_try(utils.sql_format(sql, params))
                except Exception as e:
                    self.log.error("获取用户【粉丝信息】异常. {}\r\n 错误信息:{}".format(str(fans), e))
                    continue
        self.download.download_wait()

    def submit_follower_info(self):
        '''
        @获取【粉丝】信息并提交至数据库
        :return:
        '''
        self.log.info("【在关注者信息】")
        self.create_table('TBL_PRCD_WEIBO_FOLLOW_INFO', False)

        sql = '''
            INSERT INTO "TBL_PRCD_WEIBO_FOLLOW_INFO" ("strWeiboNickname","strPhotoPath","strPageURL","strUserDesc",
            "strStatusCount","strWeiboFollowerAmount","strWeiboFollowingAmount","strWeiboUID","strWeiboRank", "strSrcAccount")
             VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}) 
             '''
        page_total, follow_total = self.weiboapi.follower_amount
        for page in range(1, page_total + 1):
            count, one_list = self.weiboapi.get_follower_onepage(page)
            for fans in one_list:
                try:
                    profile_image_path = self.download_dir + "/WeiBo/picture/{}/friends/".format(self.weiboapi.uid)
                    self.download.add_task(url=fans.get('profile_image_url', ''), path=profile_image_path,
                                           name=fans.get('profile_image_name',''))
                    params = (fans['nick'], fans['profile_image_path'], fans['profile_url'],
                              fans['desc'], fans['statuses_count'], fans['followers_count'],
                              fans['follow_count'], fans['uid'], fans['rank'], self.weiboapi.uid)

                    self.sql_execute_try(utils.sql_format(sql, params))
                except Exception as e:
                    self.log.error("获取用户【粉丝信息】异常. {}\r\n 错误信息:{}".format(str(fans), e))
                    continue
        self.download.download_wait()

    def submit_api_dialog_list(self):
        '''
        获取【会话列表】并提交至数据库
        :return:
        '''
        self.log.info("【私信列表】")
        self.create_table('TBL_PRCD_WEIBO_PRIVATEMSG_INFO', False)
        pmr = PrivateMsgRequest()

        dialog_list, group_dialog_list = self.weiboapi.get_api_dialog_list()
        access_token = self.weiboapi.access_token
        for dialog in dialog_list:
            uid = dialog['user']
            msg = []
            has_private_msg = pmr.get_private_msg(uid, msg, access_token)
            if has_private_msg and len(msg) > 0:
                # compose name dict
                name_dict = {
                    self.weiboapi.uid: self.nick_name,
                    str(uid.get('id')): uid.get('name')
                }
                # compose portrait dict
                sender_id = dialog['direct_message']['sender_id']
                recipient_id = dialog['direct_message']['recipient_id']
                sender_img_name = '{}.jpg'.format(sender_id)
                sender_image_path = '/WeiBo/picture/{}/friends/{}'.format(self.weiboapi.uid, sender_img_name)
                sender_image_abspath = self.download_dir + "/WeiBo/picture/{}/friends/".format(self.weiboapi.uid)

                if not os.path.exists(sender_image_abspath):
                    sender_img_url = dialog.get('user').get('avatar_large')
                    self.download.add_task(url=sender_img_url, path=sender_image_abspath, name=sender_img_name)
                
                recipient_img_name = '{}.jpg'.format(recipient_id)
                recipient_image_path = '/WeiBo/picture/{}/friends/{}'.format(self.weiboapi.uid, recipient_img_name)
                
                portrait_dict = {str(sender_id): sender_image_path,
                                 str(recipient_id): recipient_image_path}
                # parse info
                self.parse_dialog_info_new(msg, name_dict, portrait_dict)
            else:
                self.parse_dialog_info_old(dialog)
    
    def parse_dialog_info_new(self, msgs, name_dict, portrait_dict):
        """
        新逆向出的私信解析
        :param msgs:
        :param name_dict:
        :param portrait_dict:
        :return:
        """
        if not isinstance(msgs, list):
            return
        
        for info in msgs:
            if not isinstance(info, dict):
                continue
            msg_id = info.get('mid')
            msg_time = info.get('time')
            time_format = datetime.datetime.utcfromtimestamp(msg_time)
            created_at = time_format.strftime('%Y-%m-%d %H:%M:%S')
            sender_id = str(info.get('from'))
            sender_screen_name = name_dict.get(sender_id)
            sender_image_path = portrait_dict.get(sender_id)
            recipient_id = str(info.get('to'))
            recipient_screen_name = name_dict.get(recipient_id)
            recipient_image_path = portrait_dict.get(recipient_id)
            content = info.get('content')

            # attach info
            src_account = self.weiboapi.uid
            attach_id = ''
            attach_name = ''
            attach_url = ''

            sql = '''INSERT INTO "TBL_PRCD_WEIBO_PRIVATEMSG_INFO" ("strWeiboMsgId","strWeiboContent","strWeiboSenderAccid",
            "strWeiboSenderNick", "strSenderImage", "strWeiboReceiverAccid","strWeiboReceiverNick","strReceiverImage",
            "strWeiboSendTime","strWeiboAttachmentFid", "strWeiboAttachmentName","strWeiboAttachmentUrl","strSrcAccount")
            VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'''
            params = (msg_id, content, sender_id, sender_screen_name, sender_image_path, recipient_id, recipient_screen_name,
            recipient_image_path, created_at, attach_id, attach_name, attach_url, src_account)

            self.sql_execute_try(utils.sql_format(sql, params))
    
    def parse_dialog_info_old(self, dialog):
        """
        老的私信数据解析
        :param dialog:
        :return:
        """
        message_id = dialog['direct_message']['id']
        create_time = dialog['direct_message']['created_at']
        time_format = datetime.datetime.strptime(create_time,'%a %b %d %H:%M:%S %z %Y')
        pos = str(time_format).find('+')
        created_at = str(time_format)[0:pos]
        sender_id = dialog['direct_message']['sender_id']
        recipient_id = dialog['direct_message']['recipient_id']
        sender_screen_name = dialog['direct_message']['sender_screen_name']
        recipient_screen_name = dialog['direct_message']['recipient_screen_name']
        content = dialog['direct_message']['text']
        content = content.replace('\"', ' ')

        sender_img_name = '{}.jpg'.format(sender_id)
        sender_image_path = '/WeiBo/picture/{}/friends/{}'.format(self.weiboapi.uid, sender_img_name)
        sender_img_url = dialog.get('user').get('avatar_large')
        sender_image_abspath = self.download_dir + "/WeiBo/picture/{}/friends/".format(self.weiboapi.uid)

        recipient_img_name = '{}.jpg'.format(recipient_id)
        recipient_image_path = '/WeiBo/picture/{}/friends/{}'.format(self.weiboapi.uid, recipient_img_name)

        src_account = self.weiboapi.uid
        attach_id = ''
        attach_name = ''
        attach_url = ''

        if 'page_info' in dialog['direct_message']:
            attach_id = dialog['direct_message']['page_info']['page_id']
            attach_name = dialog['direct_message']['page_info']['page_title']
            attach_name = attach_name.replace('\"', ' ')
            attach_url = dialog['direct_message']['url_struct'][0]['url_type_pic']

        self.download.add_task(url=sender_img_url, path=sender_image_abspath, name=sender_img_name)

        sql = '''INSERT INTO "TBL_PRCD_WEIBO_PRIVATEMSG_INFO" ("strWeiboMsgId","strWeiboContent","strWeiboSenderAccid",
        "strWeiboSenderNick", "strSenderImage", "strWeiboReceiverAccid","strWeiboReceiverNick","strReceiverImage",
        "strWeiboSendTime","strWeiboAttachmentFid", "strWeiboAttachmentName","strWeiboAttachmentUrl","strSrcAccount")
        VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'''
        params = (message_id, content, sender_id, sender_screen_name, sender_image_path, recipient_id, recipient_screen_name,
                  recipient_image_path, created_at, attach_id, attach_name, attach_url, src_account)

        self.sql_execute_try(utils.sql_format(sql, params))

    def submit_api_group_members(self):
        '''
            获取群组会话信息 及群组成员信息  群组消息
        '''
        self.log.info("【群组信息】")
        self.create_table('TBL_PRCD_WEIBO_GROUP_INFO', False)
        self.create_table('TBL_PRCD_WEIBO_GROUP_MEMBER_INFO', False)
        self.create_table('TBL_PRCD_WEIBO_GROUP_MESSAGE_INFO', False)

        pmr = PrivateMsgRequest()
        dialog_list, group_dialog_list = self.weiboapi.get_api_dialog_list()
        access_token = self.weiboapi.access_token
        # 保存群组信息
        for dialog in group_dialog_list:
            group_id = dialog['user']['id']
            group_name = dialog['user']['name']
            group_picture = dialog['user']['profile_image_url']
            group_picture_name = str(group_id)+'.jpg'
            group_picture_relapath = '/WeiBo/picture/{}/groups/{}'.format(self.weiboapi.uid, group_picture_name)
            group_picture_abspath = self.download_dir + '/WeiBo/picture/{}/groups/'.format(self.weiboapi.uid)
            self.download.add_task(url=group_picture, path=group_picture_abspath, name=group_picture_name)
            creator = dialog['user']['creator']
            member_count = dialog['user']['member_count']
            join_time = dialog['user']['join_time']
            join_time= utils.time_local(join_time)
            update_time = dialog['user']['lastChangeTime']
            update_time = utils.time_local(update_time)
            user_map = {}
            for member in dialog['user']['member_users']:
                print(member)
                if not isinstance(member, dict):
                    continue
                member_id = member.get('idstr','')
                member_name = member.get('name', '')
                # user_map[member_id] = member_name
                user_map.setdefault(member_id, member_name)
                member_picture = member['profile_image_url']
                member_picture_name = str(member_id) + '.jpg'
                member_picture_relpath = '/WeiBo/picture/{}/groups/{}'.format(self.weiboapi.uid, member_picture_name)
                member_picture_abspath = self.download_dir + '/WeiBo/picture/{}/groups/'.format(self.weiboapi.uid)
                self.download.add_task(url=member_picture, path=member_picture_abspath, name=member_picture_name)
    
                sql = '''INSERT INTO "TBL_PRCD_WEIBO_GROUP_MEMBER_INFO" 
                    ("strMemberID","strMemberNick","strMemberPicture","strJoinTime","strGroupID","strSrcAccount") 
                    VALUES("{}","{}","{}","{}","{}","{}")'''.format(member_id, member_name, member_picture_relpath, join_time, group_id, self.weiboapi.uid)
                self.sql_execute_try(sql)

            sql = '''INSERT INTO TBL_PRCD_WEIBO_GROUP_INFO ("strGroupID","strGroupName","strGroupImage","strMemberCount",
                "strOwnerID","strOwnerNick","strUpdateTime","strSrcAccount") VALUES("{}","{}","{}","{}","{}","{}","{}","{}")'''.\
                format(group_id, group_name, group_picture_relapath, member_count, creator, user_map.get(creator, ''), update_time, self.weiboapi.uid)
            self.sql_execute_try(sql)

            msg = []
            has_msg = pmr.get_group_msg(group_id, msg, access_token)
            if has_msg:
                self.parse_group_private_msg_new(msg, user_map, dialog)
            else:
                self.parse_group_private_msg_old(dialog)
            
        self.download.download_wait()
        
    def parse_group_private_msg_new(self, msgs, user_map, dialog):
        """
        群组聊天信息
        :param msgs:
        :param user_map:
        :param dialog:
        :return:
        """
        if not isinstance(msgs, list):
            return

        group_id = dialog['user']['id']
        recipient_id = dialog['direct_message']['recipient_id']
        recipient_screen_name = dialog['direct_message']['recipient_screen_name']

        for info in msgs:
            if not isinstance(info, dict):
                continue

            message_id = info.get('mid')
            message_type = str(info.get('type'))
            message_content = info.get('content')
            if message_content.find('"') != -1:
                message_content = message_content.replace('"', "'")
            msg_time = info.get('time')
            time_format = datetime.datetime.utcfromtimestamp(msg_time)
            created_at = time_format.strftime('%Y-%m-%d %H:%M:%S')
            sender_id = str(info.get('from'))
            sender_screen_name = user_map.get(sender_id)
            sender_protrait_path = '/WeiBo/picture/{}/friends/{}.jpg'.format(self.weiboapi.uid, sender_id)

            sql = '''
                  INSERT INTO "TBL_PRCD_WEIBO_GROUP_MESSAGE_INFO" ("strMsgID","strContent","strTime","strSenderID","strSenderNick",
                  "strSenderPortrait","strRecevierID", "strRecevierName","strMsgType","strGroupID","strSrcAccount") VALUES
                  ("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")
                  '''.format(message_id, message_content, created_at, sender_id, sender_screen_name,
                             sender_protrait_path,
                             recipient_id, recipient_screen_name, message_type, group_id, self.weiboapi.uid)

            self.sql_execute_try(sql)
        
    def parse_group_private_msg_old(self, dialog):
        """
        老的群组私信
        :param dialog:
        :return:
        """
        group_id = dialog['user']['id']
        message_id = dialog['direct_message']['id']
        message_content = dialog['direct_message']['text']
        create_time = dialog['direct_message']['created_at']
        time_format = datetime.datetime.strptime(create_time, '%a %b %d %H:%M:%S %z %Y')
        pos = str(time_format).find('+')
        created_at = str(time_format)[0:pos]
        sender_id = dialog['direct_message']['sender_id']
        sender_screen_name = dialog['direct_message']['sender_screen_name']
        recipient_id = dialog['direct_message']['recipient_id']
        recipient_screen_name = dialog['direct_message']['recipient_screen_name']
        message_type = dialog['direct_message']['group_chat_message_type']
    
        sender_image_name = str(sender_id) + '.jpg'
        sender_protrait_path = '/WeiBo/picture/{}/friends/{}'.format(self.weiboapi.uid, sender_image_name)
    
        sql = '''
              INSERT INTO "TBL_PRCD_WEIBO_GROUP_MESSAGE_INFO" ("strMsgID","strContent","strTime","strSenderID","strSenderNick",
              "strSenderPortrait","strRecevierID", "strRecevierName","strMsgType","strGroupID","strSrcAccount") VALUES
              ("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")
              '''.format(message_id, message_content, created_at, sender_id, sender_screen_name, sender_protrait_path,
                         recipient_id, recipient_screen_name, message_type, group_id, self.weiboapi.uid)
    
        self.sql_execute_try(sql)

    def submit_api_photos_info(self):
        '''
        获取相册照片
        :return:
        '''
        self.log.info("【照片列表】")
        self.create_table('TBL_PRCD_WEIBO_PHOTO_INFO', False)

        since_id = 0
        while True:
            card_list, next_id = self.weiboapi.get_api_photos_list(since_id)
            for card in card_list:
                if card['card_type'] == 47:
                    for pic in card['pics']:
                        if 'pic_id' in pic:
                            pic_id = pic['pic_id']
                            pic_url = pic['pic_big']
                            blog_id = pic['mblog']['id']
                            blog_text = pic['mblog']['text']
                            pic_name = str(pic_id) + '.jpg'
                            pic_path = '/WeiBo/picture/{}/photos/{}'.format(self.weiboapi.uid, pic_name)
                            pic_abspath = self.download_dir + '/WeiBo/picture/{}/photos/'.format(self.weiboapi.uid)

                            try:
                                download_file(pic_url, pic_abspath, pic_name)
                            except Exception as e:
                                self.log.error("照片下载你失败:[{}] {}".format(pic_url, e))
                                continue
                            sql = '''INSERT INTO "TBL_PRCD_WEIBO_PHOTO_INFO" ("PhotoID","PhotoURL","LocalPath","MblogID","MblogText","strSrcAccount") 
                                    VALUES({}, {}, {}, {}, {}, {})'''
                            params = (pic_id, pic_url, pic_path, blog_id, blog_text, self.weiboapi.uid)
                            self.sql_execute_try(utils.sql_format(sql, params))

            if next_id == 0:
                break
            since_id = next_id
        self.download.download_wait()

    def create_table(self, tablename, drop_if_exist=False):
        if self.sqlconn.tableExists(tablename):
            log.info('table {} already exists'.format(tablename))
            if drop_if_exist:
                log.info('drop table:{}.'.format(tablename))
                self.sql_execute_try('DELETE FROM {}'.format(tablename))
        else:
            self.sql_execute_try(SQL_CREATETABLE.get(tablename, ''))


    def sql_select(self, sql):
        try:
            oSmt = pyMyDatabase.SQLiteStatement(self.sqlconn, sql)
            if oSmt.executeStep():
                paramlist = oSmt.getColumn(0)
                if not paramlist.isNull():
                    paramlist = paramlist.getText("")
                else:
                    paramlist = None
                return paramlist
            return None
        except Exception as e:
            self.log.exception('sql select error. sql:{}'.format(sql), exc_info=e)
            return None


    def sql_execute_try(self, sql):
        first = True
        while True:
            try:
                self.sqlconn.execute(sql)
            except Exception as e:
                if first:
                    time.sleep(1)
                    first = False
                    continue
                else:
                    log.exception('sql_execute error! errorinfo:%s\r\nsql:%s' % (e,sql), exc_info = e)
            self.record_count += 1
            break










