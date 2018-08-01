# -*- coding: utf-8 -*-

# @Function : 配置文件
# @Time     : 2017/9/30
# @Author   : Zhangjw
# @File     : config.py
# @Company  : Meiya Pico

import random
import pathlib
from WeiboCatcher.logger import Logger
import os
import sys

log = Logger('Weibo.log')

BIN64_PATH = os.path.abspath(os.path.dirname(sys.argv[0])+os.path.sep+"..")
# BIN64_PATH = "D:\Program Files\CloudForensic\CloudSupport\Bin64"
APP_NAME = 'WeiBo'
TEMP_PATH = pathlib.Path(sys.argv[0]).parent.__str__() + '/weibo_temp/'
SESSION_SAVE_PATH = TEMP_PATH +'session.json'
APPS_AMF_PATH = 'Apps.amf'
HTTP_TIMEOUT = 5
MAX_RETRIES = 3
DEBUG = False

FIRST_FORENSIC_FLAG = True

USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 '
    'Mobile/13B143 Safari/601.1]',
    'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/48.0.2564.23 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/48.0.2564.23 Mobile Safari/537.36']

HEARDERS = {
    'User_Agent': random.choice(USER_AGENTS),
    'Referer': 'https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=http%3A%2F%2Fm.weibo.cn%2F',
    'Origin': 'https://passport.weibo.cn',
    'Host': 'passport.weibo.cn'
}

POST_DATA = {
    'username': '',
    'password': '',
    'savestate': '1',
    'ec': '0',
    'pagerefer': 'https://passport.weibo.cn/signin/welcome?entry=mweibo&r=http%3A%2F%2Fm.weibo.cn%2F&wm=3349&vt=4',
    'entry': 'mweibo'
}

APP_KEY = {
    'iphone': '5Jao51NF1i5PDC91hhI3ID86ucoDtn4C',
    'android': '5l0WXnhiY4pJ794KIJ7Rw5F45VXg9sjo'
}

REDIS_CONF = {
    "ip":"localhost",
    "port":53011,
    "pwd":"MyXACloudForensicFrom@2017@"
}


#创建表语句
SQL_CREATETABLE = {
    'TBL_PRCD_WEIBO_USERINFO':
        '''
        CREATE TABLE "TBL_PRCD_WEIBO_USERINFO" (
        "Id"  INTEGER  NOT NULL,
        "ModifyTime"  TEXT(32) NOT NULL DEFAULT (datetime('now','localtime')),
        "strWeiboAccountNum"   TEXT, --账号
        "strWeiboNickName"     TEXT, --昵称
        "strWeiboAlias"        TEXT, --
        "strPhotoPath"         TEXT, --头像存储本地路径
        "strWeiboPhotoUrl"     TEXT, --头像URL
        "strWeiboAccountID"    TEXT, --账号ID
        "strWeiboFaceURL"      TEXT, --主页URL
        "strWeiboGender"       TEXT, --性别
        "strWeiboBirthday"     TEXT, --生日
        "strWeiboIsVIP"        TEXT, --是否VIP
        "strWeiboAge"          TEXT, --年龄
        "strWeiboCountry"      TEXT, --国家
        "strWeiboProvince"     TEXT, --省
        "strWeiboCity"         TEXT, -- 市
        "strWeiboMsnNum"       TEXT, --MSN
        "strWeiboQQNum"        TEXT, --QQ
        "strWeiboBlog"         TEXT, --博客地址
        "strWeiboEmail"        TEXT, --email
        "strWeiboBio"          TEXT, --
        "strWeiboType"         TEXT, --类型
        "strCreateAt"   	   TEXT, --注册时间
        "strRealName"          TEXT, --真实姓名
        "strOrient"			   TEXT, --性取向
        "strEmotion"		   TEXT, --感情状况
        "strBloodType"		   TEXT, --血型
        "strUserDesc" 		   TEXT, --个人描述、简介
        "strSunRank"		   TEXT, --微博等级
        "strSchool"			   TEXT, --学校名称
        "strDepartment"		   TEXT, --院系						
        "strCompany"		   TEXT, --公司名称
        "strJob"			   TEXT, --部分或职位
        "strPerLabel"		   TEXT, --个人标签		  
        "strPostalCode"		   TEXT, --邮政编码
        "strMobilePhone"	   TEXT, --手机号
        "strLandline"		   TEXT, --座机号码
        "strAttNum"			   TEXT, --关注数
        "strBlogNum"		   TEXT, --微博数
        "strFansNum"		   TEXT, --粉丝数
        "other"				   TEXT,
        PRIMARY KEY ("id" ASC)
        )
        ''',
    'TBL_PRCD_WEIBO_PRIVATEMSG_INFO':
        '''
        CREATE TABLE "TBL_PRCD_WEIBO_PRIVATEMSG_INFO"(
        id INTEGER NOT NULL,
        strWeiboMsgId        TEXT,	--私信ID
        strWeiboSenderAccid  TEXT,  --发送者账户ID
        strWeiboSender       TEXT,  --发送者账号名
        strWeiboSenderNick   TEXT,  --发送者昵称
        strSenderImage       TEXT,  --发送者头像本地路径
        strWeiboPMPortrait   TEXT,  --头像
        strWeiboReceiverAccid TEXT, --接收者账户ID
        strWeiboReceiver     TEXT,  --接收者账号
        strWeiboReceiverNick TEXT,  --接收者昵称
        strWeiboParentAuthorPm TEXT, --接收私信者用户名
        strReceiverImage      TEXT,  --接收者头像本地路径
        strWeiboContent      TEXT,   --私信内容
        strWeiboSendTime     TEXT,   --发送时间
        strWeiboSessionID    TEXT,   --会话ID
        strWeiboReadFlag     TEXT,   --已读标志
        strWeiboType         TEXT,   --私信类型
        strWeiboAttachmentFid TEXT,  --附件ID
        strWeiboAttachmentName TEXT, --附件名
        strWeiboAttachmentCtime TEXT,--附件创建时间
        strWeiboAttachmentType TEXT, --附件类型
        strWeiboAttachmentSize TEXT, --附件大小
        strWeiboAttachmentUrl TEXT,  --附件链接
        strWeiboAttachmentThumbnail TEXT, --附件缩略图
        strWeiboAttachmentLocalPath TEXT, --附件本地存储地址
        strWeiboLongitude    TEXT, --经度
        strWeiboLatitude     TEXT, --纬度
        strIsDelete          TEXT, 
        strSource            TEXT,
        strSrcAccount        TEXT, --来源账号
        strWeiboSoftType        TEXT,
        strSoftTypeID        TEXT,
        "BookMark" 'TEXT' default 0,
        "FrscReport" 'TEXT' default 0,
        PRIMARY KEY ("id" ASC)
        );
        ''',
    'TBL_PRCD_WEIBO_FOLLOW_INFO':
    '''
    CREATE TABLE "TBL_PRCD_WEIBO_FOLLOW_INFO"(
    id INTEGER NOT NULL,
    strWeiboNickname     TEXT, --昵称
    strWeiboUserName     TEXT, --用户名
    strPhotoPath         TEXT, --用户头像本地存储地址
    strWeiboFaceURL      TEXT, --主页链接
    strWeiboChineseName  TEXT, --中文名称
    strWeiboAccountID    TEXT, --账户ID
    strUserDesc          TEXT, --用户自我描述
    strStatusCount       TEXT, --发布微博数
    strWeiboFollowerAmount TEXT,  --听众数目
    strWeiboFollowingAmount TEXT, --收听人数
    strWeiboGender       TEXT, --性别
    strWeiboIsFollower   TEXT, --是否是听众
    strWeiboIsFollowed   TEXT, --是否被收听
    strWeiboIsForbbiden  TEXT, --是否被拉黑
    strWeiboIsVIP        TEXT, --是否VIP
    strWeiboUID          TEXT, --用户ID
    strWeiboVip          TEXT, --VIP
    strWeiboAccountNum   TEXT, --账号
    strWeiboName         TEXT, --名称
    strWeiboTime         TEXT, --联系时间
    strWeiBoFllowType    TEXT, --好友类型
    strIsDelete          TEXT, --已删除
    strSrcAccount        TEXT, --来源账号
    strPageURL           TEXT, --主页链接
    strWeiboRank         TEXT, --微博等级
    strWeiboSoftType     TEXT, --
    strSoftTypeID        TEXT, --
    "BookMark" 'TEXT' default 0,
    "FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    ''',
    'TBL_PRCD_WEIBO_FANS_INFO':
    '''
    CREATE TABLE "TBL_PRCD_WEIBO_FANS_INFO"(
    id INTEGER NOT NULL,
    strWeiboNickname     TEXT, --昵称
    strWeiboUserName     TEXT, --用户名
    strPhotoPath         TEXT, --头像本地存储路径
    strWeiboFaceURL      TEXT, --主页链接
    strWeiboChineseName  TEXT, --中文名称
    strWeiboAccountID    TEXT, --账户ID
    strUserDesc          TEXT, --用户自我描述
    strStatusCount       TEXT, --发布微博数
    strWeiboFollowerAmount TEXT, --听众数目
    strWeiboFollowingAmount TEXT, --收听人数
    strWeiboGender       TEXT, --性别
    strWeiboIsFollower   TEXT, --是否是听众
    strWeiboIsFollowed   TEXT, --是否被收听
    strWeiboIsForbbiden  TEXT, --是否被拉黑
    strWeiboIsVIP        TEXT, --是否VIP
    strWeiboUID          TEXT, --用户ID
    strWeiboVip          TEXT, --VIP
    strWeiboAccountNum   TEXT, --账号
    strWeiboName         TEXT, --名称
    strWeiboTime         TEXT, --联系时间
    strWeiBoFllowType    TEXT, --好友类型
    strIsDelete          TEXT, --已删除
    strSrcAccount        TEXT, --来源账号
    strPageURL           TEXT, --主页链接
    strWeiboRank         TEXT, --微博等级
    strWeiboSoftType     TEXT, 
    strSoftTypeID        TEXT, 
    "BookMark" 'TEXT' default 0,
    "FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    ''',
    'TBL_PRCD_WEIBO_BLOGINFO':
    '''
    CREATE TABLE "TBL_PRCD_WEIBO_BLOGINFO"(
	id INTEGER NOT NULL,
	strWeiboSessionID      TEXT,
	strWeiboContent        TEXT,
	strWeiboSendTime       TEXT,
	strWeiboSenderAccid    TEXT,
	strWeiboSenderNick     TEXT,
	strWeiboPMPortrait     TEXT,
	strWeiboReceiverAccid  TEXT,
	strWeiboReceiverNick   TEXT,
	strWeiboParentAuthorPm TEXT,
	strWeiboType           TEXT,
	strSource              TEXT, --发布平台
	strTitle               TEXT, --微博标题
	strWeiboAttachmentName TEXT, -- 微博图片\视频地址
	strWeiboAttachmentCtime  TEXT,
	strWeiboAttachmentType   TEXT,
	strWeiboAttachmentSize   TEXT,
	strWeiboAttachmentUrl    TEXT,
	strWeiboAttachmentLocalPath TEXT, -- 原微博图片\视频地址
	strWeiboLongitude    TEXT,
	strWeiboLatitude     TEXT,
	strWeiboLocation     TEXT,
	strWeiboAttiCount    TEXT,
	strWeiboForwardCount TEXT,
	strWeiboCommentCount TEXT,
	strToolType          TEXT,
	strToolName          TEXT,
	strPrevCreatedAt      TEXT,
	strPrevMblogID        TEXT,
	strPrevContent        TEXT,
	strPrevSource         TEXT,
	strPrevUID            TEXT,
	strIsDelete          TEXT,
	strSrcAccount        TEXT,
	strWeiboSoftType     TEXT,
	strSoftTypeID        TEXT,
    "BookMark" 'TEXT' default 0,
    "FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    ''',
    'TBL_PRCD_WEIBO_GROUP_INFO':
    '''
    CREATE TABLE "TBL_PRCD_WEIBO_GROUP_INFO"(
	id INTEGER NOT NULL,
	strGroupID         TEXT, --群组id
	strGroupName       TEXT, --群组名称
	strGroupImage      TEXT, --群组头像路径
	strMemberCount     TEXT, --成员数目
	strOwnerID         TEXT, --拥有者uid
	strOwnerNick       TEXT, --拥有者昵称
	strUpdateTime      TEXT, --更新时间
	strIsDelete        TEXT, --
	strSrcAccount      TEXT, --来源账号uid
	strSoftTypeID      TEXT,
	"BookMark" 'TEXT' default 0,
	"FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    ''',
    'TBL_PRCD_WEIBO_GROUP_MEMBER_INFO':
    '''
    CREATE TABLE "TBL_PRCD_WEIBO_GROUP_MEMBER_INFO"(
    id INTEGER NOT NULL,
    strMemberID        TEXT, --成员uid
    strMemberPicture   TEXT, --群成员头像路径
    strMemberNick      TEXT, --成员昵称
    strJoinTime        TEXT, --入群时间
    strGroupID         TEXT, --群组id
    strIsDelete        TEXT, 
    strSrcAccount      TEXT,
    strSoftTypeID      TEXT,
    "BookMark" 'TEXT' default 0,
    "FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    ''',
    'TBL_PRCD_WEIBO_GROUP_MESSAGE_INFO':
    '''
    CREATE TABLE "TBL_PRCD_WEIBO_GROUP_MESSAGE_INFO"(
    id INTEGER NOT NULL,
    strMsgID           TEXT,--消息ID
    strContent         TEXT,--消息内容
    strTime            TEXT,--时间
    strSenderID        TEXT,--发送者ID
    strSenderNick      TEXT,--发送者昵称
    strSenderPortrait  TEXT,--发送者头像链接
    strRecevierID      TEXT,--接收者ID
    strRecevierName    TEXT,--接收者名称
    strMsgType         TEXT,--消息类型
    strAttachID        TEXT,--附件ID
    strAttachName      TEXT,--附件名称
    strAttachPath      TEXT,--附件路径
    strAttachSize      TEXT,--附件大小
    strAttachUrl       TEXT,--附件URL
    strLongitude       TEXT,--附件经度
    strLatitude        TEXT,--附件纬度
    strGroupID         TEXT,--群组id
    strIsDelete        TEXT,
    strSrcAccount      TEXT,
    strSoftTypeID      TEXT,
    "BookMark" 'TEXT' default 0,
    "FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    ''',
'TBL_PRCD_WEIBO_PHOTO_INFO':
    '''
    --照片信息表
    CREATE TABLE "TBL_PRCD_WEIBO_PHOTO_INFO"(
    id INTEGER NOT NULL,
    PhotoID          TEXT,   --照片ID
    PhotoURL         TEXT,   --链接地址 
    LocalPath        TEXT,   --本地存储地址
    MblogID          TEXT,   --所属微博ID
    MblogText        TEXT,   --所属微博文字内容
    AlbumID          TEXT,   --所属相册ID
    AlbumName        TEXT,   --所属相册名称
    strSrcAccount      TEXT, --来源账号
    "BookMark" 'TEXT' default 0,
    "FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    '''
}


SQL_CREATETABLE_BETA = {
'TBL_PRCD_WEIBO_ALBUM_INFO':
    '''
    --创建相册专辑信息信息表
    CREATE TABLE "TBL_PRCD_WEIBO_ALBUM_INFO"(
    id INTEGER NOT NULL,
    AlbumName        TEXT, --相册名称
    AlbumID          TEXT, --专辑ID containerid 
    AlbumType        TEXT, --相册类型
    AlbumCover        TEXT, --相册封面链接
    CoverPath         TEXT, --封面本地存储地址
    Total             TEXT, --相册中的内容数目
    UpdateTime        TEXT, --最后更新时间
    strSrcAccount      TEXT, -- 来源账号
    strSoftTypeID      TEXT, 
    "BookMark" 'TEXT' default 0,
    "FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    ''',
'TBL_PRCD_VISITED_RECENTLY':
    '''
    --经常访问/最近访问 用户列表
    CREATE TABLE "TBL_PRCD_VISITED_RECENTLY"(
    id INTEGER NOT NULL,
    UserID            TEXT,   -- 用户ID
    UserName          TEXT,   -- 用户名称 
    PhotoURL          TEXT,   -- 用户头像地址
    PhotoLocal        TEXT,   -- 头像存储的本地路径
    LocalPath         TEXT,   -- 本地存储地址
    PageURL           TEXT,   -- 主页路径
    Description       TEXT,   
    strSrcAccount     TEXT,   -- 来源账号
    "BookMark" 'TEXT' default 0,
    "FrscReport" 'TEXT' default 0,
    PRIMARY KEY ("id" ASC)
    );
    '''
}