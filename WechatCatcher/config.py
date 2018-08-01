# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2018/3/15
# @Author   : Zhangjw
# @File     : config.py
# @Company  : Meiya Pico

from WechatCatcher.logger import Logger
import os
import sys
import pathlib
log = Logger('Wechat.log')

BIN64_PATH = pathlib.Path(sys.argv[0]).parent.parent.__str__()

# BIN64_PATH = os.path.abspath(os.path.dirname(sys.argv[0])+os.path.sep+"..")
APP_NAME = 'Wechat'

ANDROID_PATH = BIN64_PATH + "\\Tool\\android\\"
DEBUG = False
APPS_AMF_FOLDER = ''
APPS_AMF_PATH = 'Apps.amf'
CMF_PATH = 'AppCloudDB.cmf'
AMF_FOLDER = ''
AMF_PATH = AMF_FOLDER + '{}.amf'.format(APP_NAME)

CUT_OFF_TIME = 0

INTERVAL_DICT = {
	"Month": -1,
    "Quarter": -3,
    "HalfYear": -6,
    "Year": -12,
    "TwoYears": -24,
}

#创建表语句
SQL_CREATETABLE = {
    'TBL_PRCD_WECHAT_BILL_RECORDS':
        '''
        CREATE TABLE "TBL_PRCD_WECHAT_BILL_RECORDS" (
        "Id"  INTEGER  NOT NULL,
        "title"                  TEXT, -- 交易标题            
        "current_state"            TEXT, -- 当前状态
        "pay_fee"                  TEXT	DEFAULT '0', -- 付款金额
        "recv_fee"                 TEXT DEFAULT '0', -- 收款金额
        "charge_fee"               TEXT DEFAULT '0', -- 零钱充值金额
        "withdraw_fee"             TEXT DEFAULT '0', -- 出账金额
        "real_withdraw_fee"		   TEXT DEFAULT '0', -- 实际提现金额
        "refund_flow_fee"		   TEXT DEFAULT '0', -- 退款金额
        "classify_type"            TEXT, -- 交易类型
        "bill_type"                TEXT, -- 账单类型   
        "payer_name"               TEXT, -- 支付人昵称
        "payer_wxid"               TEXT, -- 支付人微信ID
        "receiver_name"            TEXT, -- 收款人昵称
        "receiver_wxid"            TEXT, -- 收款人微信ID
        "pay_bank_name"            TEXT, -- 支付方式
		"receiver_remark"          TEXT, -- 收款方备注
        "transfer_detail"          TEXT, -- 转账说明
        "goods_name"               TEXT, -- 商品
        "mch_name"                 TEXT, -- 商户简称
        "mch_full_name"            TEXT, -- 商户全称
        "pay_time"                 TEXT, -- 支付时间
        "recv_time"                TEXT, -- 收款时间
        "transfer_pay_time"        TEXT, -- 转账时间
        "transfer_recv_time"       TEXT, -- 收钱时间
        "withdraw_apply_time"      TEXT, -- 提现申请时间
        "withdraw_arrive_time"     TEXT, -- 提现到账时间
        "charge_time"              TEXT, -- 充值时间
        "withdraw_bank_name"       TEXT, -- 提现银行
        "bill_id"                  TEXT, -- 账单ID
        "trans_id"                 TEXT, -- 交易单号
        "out_trade_no"             TEXT, -- 商户单号
        "transfer_trans_id"        TEXT, -- 转账单号
        "withdraw_trans_id"        TEXT, -- 提现单号
        "real_withdraw_charge"     TEXT, -- 提现费用
        "card_tail"				   TEXT, -- 银行卡尾号
        "refund_flow_status"	   TEXT, -- 退款状态
        "refund_flow_time"		   TEXT, -- 退款时间
        "refund_flow_bank_name"    TEXT, -- 退款银行
        "refund_flow_refund_id"    TEXT, --	退款id
        "refund_flow_out_trade_no" TEXT, -- 退款交易单号
        "source_acct"              TEXT, -- 来源账号
        "other"				       TEXT,
        PRIMARY KEY ("id" ASC)
        )
        ''',
    'TBL_PRCD_WECHAT_USER_INFO':
        '''
        CREATE TABLE "TBL_PRCD_WECHAT_USER_INFO" (
        "Id"  INTEGER  NOT NULL,
        "account"                 TEXT, -- 微信ID
        "phone"                   TEXT, -- 手机号码
        "wxid"                    TEXT, -- 用户ID（唯一）
        "nick"                    TEXT, -- 昵称
        "gender"                  TEXT, -- 性别
        "portrait"                TEXT, -- 头像
        "wechat_id"               TEXT, -- 微信号
        "qrcode"                  TEXT, -- 二维码本地存储地址
        "address"                 TEXT, -- 地址
        "desc"                    TEXT, -- 个性签名
        "other"                   TEXT,
        PRIMARY KEY ("id" ASC)
        )
        ''',
    'TBL_PRCD_WECHAT_HBDETAIL_INFO':
        '''
        CREATE TABLE "TBL_PRCD_WECHAT_HBDETAIL_INFO" (
        "Id"  INTEGER  NOT NULL,
        "sendUserNick" 	TEXT,
        "sendUserWxid"  TEXT,
        "sendId"  TEXT,
        "recNum"  TEXT,
        "totalNum"  TEXT,
        "totalAmount"  TEXT,
        "amount"  TEXT,
        "wishing"  TEXT,
        "isSender"  TEXT,
        "receiveId"  TEXT,
        "hbType"  TEXT,
        "hbStatus"  TEXT,
        "receiveStatus"  TEXT,
        "statusMess"  TEXT,
        "headTitle"  TEXT,
        "canShare"  TEXT,
        "hbKind"  TEXT,
        "recAmount"  TEXT,
        "changeWording"  TEXT,
        PRIMARY KEY ("Id" ASC)
        )
        ''',
    'TBL_PRCD_WECHAT_HBRECEIVER_INFO':
        '''
        CREATE TABLE "TBL_PRCD_WECHAT_HBRECEIVER_INFO" (
        "Id"  INTEGER  NOT NULL,
        "sendId"  TEXT,
        "receiveAmount"  TEXT,
        "receiveTime"  	TEXT,
        "answer"  		TEXT,
        "receiveId"  	TEXT,
        "receiveNick"  TEXT,
        "state"  	TEXT,
        "gameTips"  TEXT,
        "receiveOpenId"  TEXT,
        "userName"  TEXT,
        PRIMARY KEY ("Id" ASC)
        )
        '''
}


BILL_TYPES = [
	{
		"classify_key": 2,
		"classify_name": "红包"
	},
	{
		"classify_key": 1,
		"classify_name": "转账"
	},
	{
		"classify_key": 5,
		"classify_name": "群收款"
	},
	{
		"classify_key": 3,
		"classify_name": "二维码收付款"
	},
	{
		"classify_key": 6,
		"classify_name": "商户消费"
	},
	{
		"classify_key": 4,
		"classify_name": "充值提现"
	},
	{
		"classify_key": 9,
		"classify_name": "信用卡还款"
	},
	{
		"classify_key": 10,
		"classify_name": "有退款"
	}]

# 优化列表
# 0. 断网之后， 程序检测到网络异常退出取证且虚拟机退出
# 1. 将手机取证那边获取到的用户信息补充至云取证数据用户信息表
# 2.
# 3.





