# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2018/3/15
# @Author   : Zhangjw
# @File     : config.py
# @Company  : Meiya Pico

import os
import sys
import pathlib
from pyjdmallcatcher.logger import Logger

log = Logger('JingDong.log')

BIN64_PATH = pathlib.Path(sys.argv[0]).parent.parent.__str__()
DEBUG = False

APP_NAME = 'JingDong'
AMF_NAME = '{}.amf'.format(APP_NAME)

CMF_PATH = 'AppCloudDB.cmf'
APPS_AMF_PATH = 'Apps.amf'
AMF_FOLDER = ''
APPS_AMF_FOLDER = ''
AMF_PATH = AMF_FOLDER + '{}.amf'.format(APP_NAME)
ANDROID_PATH = BIN64_PATH + "\\Tool\\android\\"
VERIFY_PICS_FOLDER = ''
VERIFY_PIC_NAME = 'security_code.jpg'

#创建表语句
SQL_CREATETABLE = {
    "TBL_PRCD_JDCOM_USER_INFO":
        '''
        CREATE TABLE "TBL_PRCD_JDCOM_USER_INFO" (
        "id"  INTEGER NOT NULL,
        "strModifyTime"  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        "strUserName"  TEXT,
        "strAvatar"  TEXT,
        "strAccount"  TEXT,
        "strPassword"  TEXT,
        "strUserId"  TEXT,
        "strPhone"  TEXT,
        "strMail"  TEXT,
        "strOther"  TEXT,
        PRIMARY KEY ("id" ASC)
        )
        ''',
    "TBL_PRCD_JDCOM_ORDER_INFO":
        '''
        CREATE TABLE "TBL_PRCD_JDCOM_ORDER_INFO" (
        "id"  INTEGER NOT NULL,
        "strModifyTime"     TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        "strOrderId"            TEXT,      -- 订单ID
        --"strOrderStatusId"      TEXT,    -- 订单状态ID
        "strOrderStatus"        TEXT,      -- 订单状态名称     
        "strSubmitDate"         TEXT,      -- 订单提交时间                
        "strPrice"              TEXT,      -- 订单总价
        "strPaymentType"        TEXT,      -- 支付类型
        "strShopName"           TEXT,      -- 商家名称
        "strBranchId"           TEXT,      -- 分店铺id
        "strOrderType"          TEXT,      -- 订单类型
        "strWareCountMsg"       TEXT,      -- 商品数量信息
        "strDetailPrice"        TEXT,      -- 详细价格
        "strListPrice"          TEXT,      -- 标示价格
        "strSrcAccount"         TEXT,
        "strOther"              TEXT,
        PRIMARY KEY ("id" ASC)
        )
        ''',
    "TBL_PRCD_JDCOM_GOODS_INFO":
        '''
        CREATE TABLE "TBL_PRCD_JDCOM_GOODS_INFO" (
        "id"  INTEGER NOT NULL,
        "strModifyTime"    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        "strOrderId"       TEXT,          -- 订单ID
        "strSubmitDate"     TEXT,         -- 购买时间
        "strGoodsId"        TEXT,          -- 商品ID
        "strGoodsName"      TEXT,          -- 商品名称
        "strGoodsDesc"     TEXT,          -- 商品描述 
        "strPrice"         TEXT,         -- 购买价格
        "strNewPrice"      TEXT,         -- 最新价格
        "strNumber"        TEXT,          -- 购买数量
        "strGoodSnapshot"  TEXT,          -- 商品快照
        "strGoodsImgURL"  TEXT,          -- 商品快照链接
        "strSrcAccount"    TEXT,          -- 来源账号
        "strOther"         TEXT,
        PRIMARY KEY ("id" ASC)
        )
        ''',
    "TBL_PRCD_JDCOM_ORDER_DETAIL":
        '''
        CREATE TABLE "TBL_PRCD_JDCOM_ORDER_DETAIL" (
        "id"  INTEGER NOT NULL,
        "strModifyTime"       TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        "strOrderId"          TEXT,           -- 订单ID
        "strOrderStatus"      TEXT,           -- 订单状态
        "strDataSubmit"       TEXT,           -- 提交状态
        "strPrice"            TEXT,           -- 商品总额
        "strExpressFee"       TEXT,           -- 运费
        "strDiscount"         TEXT,           -- 折扣
        "strShouldPay"        TEXT,           -- 订单总额
        "strPaymentType"      TEXT,           -- 支付方式 
        "strPayTime"          TEXT,           -- 支付时间
        --"strMessage"       TEXT,            -- 商家消息
        "strShopName"         TEXT,           -- 商家名称
        --"strCancleOrder"   TEXT,            -- 是否取消的订单
        "strCustomerName"     TEXT,           -- 收货人姓名
        "strMobile"           TEXT,           -- 手机号码
        "strAddress"          TEXT,           -- 收货地址
        "strCarrier"          TEXT,           -- 配送方式
        "strInvoiceType"      TEXT,           -- 发票类型
        "strInvoiceTitle"     TEXT,           -- 发票抬头
        "strInvoiceContent"   TEXT,           -- 发票内容
        "strInvoiceSnapshot"   TEXT,           -- 电子发票快照
        "strSrcAccount"       TEXT,           -- 来源账号
        "strOther"            TEXT,
        PRIMARY KEY ("id" ASC)
        )
        ''',
    "TBL_PRCD_JDCOM_ADDRESS_INFO":
        '''
        CREATE TABLE "TBL_PRCD_JDCOM_ADDRESS_INFO" (
        "id"  INTEGER NOT NULL,
        "strModifyTime"  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        "strAddressId"        TEXT,        -- 地址id
        "strAddressTag"       TEXT,        -- 地址标签   家/公司/学校
        "strAddressDefault"   TEXT,        -- 是否默认地址
        "strConsignee"        TEXT,        -- 收件人姓名
        "strRegion"           TEXT,        -- 地区
        "strAddress"          TEXT,        -- 详细地址
        "strMobile"           TEXT,        -- 手机号码
        "strPhone"            TEXT,        -- 联系电话
        "strPaymentId"        TEXT,        -- 支付方式id
        "strCoordType"        TEXT,        -- 坐标类型
        "strLongitude"        TEXT,        -- 经度
        "strLatitude"         TEXT,        -- 纬度
        "strSrcAccount"       TEXT,        -- 来源账号
        PRIMARY KEY ("id" ASC)
        )
        '''
}


# 优化记录
# 0. 优化程序文件、对象命名
# 1. 添加断网检测
# 2.
#
