# -*- coding: utf-8 -*-

# @Function : WechatCatcher
# @Time     : 2018/3/15
# @Author   : Zhangjw
# @File     : wcps.py
# @Company  : Meiya Pico

import time
import datetime
import sys, os
import json
import socket

from WechatCatcher import config
from WechatCatcher import utils
from WechatCatcher.utils import sql_format
from WechatCatcher.avdmanage import AVDManager
from WechatCatcher.config import ANDROID_PATH, BIN64_PATH, log, SQL_CREATETABLE
from WechatCatcher.wechat import Wechat
from WechatCatcher.utils import datetime_format,format_fee
from WechatCatcher.progressbar import UnknownProgress
sys.path.append(BIN64_PATH)
import pyMyDatabase


class WechatCatcher(Wechat):
    def __init__(self, log, wechat:Wechat, amf_path, progress):
        self.log = log
        self.wechat = wechat
        self.amf_path = amf_path
        self.pgbar = progress
        self.avdmanager = AVDManager(log, ANDROID_PATH)
        self.sqlconn = self._sqlconn
        self.redis_cli = self.avdmanager.redis_cli
        self.log = log
        self.login_type = ''
        self.bills_count = 0
        self.request_exception_count = 0

    def __del__(self):
        pass

    @property
    def _sqlconn(self):
        try:
            sqlconn = pyMyDatabase.SQLiteDatabase(self.amf_path, True)
        except Exception as e:
            self.avdmanager.close_emulator()
            self.log.error("WechatCatcher connect the sqlite:{} failed. error info:{}".format(self.amf_path, e))
            self.log.info('Program exit.')
            os._exit(1)
        return sqlconn


    def login_by_pwd(self):
        """
        账号密码登陆
        :return: str Or None
        """
        self.login_type = 'pwd'

        reqmsg = {
            'Whoami':'WeChat',
            'CMD':'Startup',
            'StartType':'wid',
        }

        reqmsg['wxid'] = self.wechat.user
        reqmsg['pwd'] = self.wechat.pwd
        reqmsgstr = json.dumps(reqmsg)

        self.avdmanager.send_message(reqmsgstr)
        ansmsg = self.avdmanager.recv_message()
        if not ansmsg:
            return

        ansdict = json.loads(ansmsg)
        self.log.info(ansdict)
        if ansdict.get('Status') == 'succ':
            return ansdict.get('Url', '')
        else:
            return None


    def request_phone_vericode(self, msg_type):
        """
        获取验证码
        :param msg_type:
        :return:
        """
        payload = {
            "type": 0,
            "value": self.wechat.phone
        }

        if msg_type == 1:
            payload['errno'] = 1
            payload['desc'] = '验证码已发送至{}, 请输入短信验证码。'.format(self.wechat.phone)
        elif msg_type == 2 or 3:
            payload['errno'] = 2
            payload['desc'] = '校验失败，请重新输入。'
        elif msg_type == 4:
            payload['errno'] = 3
            payload['desc'] = '校验3次失败，请重新进行取证。'

            self.redis_cli.set('Wechat_Verify_Send', json.dumps(payload))
            time.sleep(0.5)
            self.avdmanager.close_emulator()

        self.redis_cli.set('Wechat_Verify_Send', json.dumps(payload))
        self.log.info(payload)

        while True:
            retjson = self.redis_cli.get('Wechat_Verify_Sendback')
            if retjson:
                checkjson = retjson.decode(encoding="utf-8")
                checkjson.replace("\"","\'")
                self.redis_cli.delete('Wechat_Verify_Sendback')
                break
            time.sleep(2)
        self.log.info(checkjson)
        return json.loads(checkjson).get('value', '').strip()


    def submit_vericode(self, submit_count):
        """
        将短信验证码发送至虚拟机
        :param submit_count:
        :return: str or None
        """
        if config.DEBUG:
            print("请输入短信验证码：")
            vericode = input()
        else:
            vericode = self.request_phone_vericode(submit_count)

        if not vericode:
            return ''

        reqvericode = {
            'Whoami':'WeChat',
            'CMD' : 'SendVericode',
            'country':'zhongguo'
        }

        reqvericode['Vericode'] = vericode
        reqvericode['phone'] = self.wechat.phone
        reqvericodestr = json.dumps(reqvericode)

        self.avdmanager.send_message(reqvericodestr)
        ansmsg = self.avdmanager.recv_message()
        ansdict = json.loads(ansmsg)
        self.log.info(ansdict)
        if ansdict.get('CMD') == 'SendVericodeRet':
            if ansdict.get('Status') == 'succ':
                self.log.info('Phone vericode login succ.')
                return ansdict.get('Url')
            elif ansdict.get('Status') == 'fail':
                self.log.error('Phone vericode login fail.')
        return ''


    def login_sms_confirm(self):
        """
        登录确认
        :return:
        """
        payload = {
            "type": 0,
            "value": self.wechat.phone
        }

        payload['desc'] = "风险提示：用短信验证码登录后，微信官方将会重置此帐号的密码，请确认是否使用短信验证码登录？"

        self.redis_cli.set('Wechat_Event_Send', json.dumps(payload))

        if config.DEBUG:
            while True:
                retjson = self.redis_cli.get('Wechat_Event_Send')
                if retjson:
                    self.redis_cli.delete('Wechat_Event_Send')
                    break

            confirm_value = input()
            payload = {
                "type":0,
                "value":confirm_value
            }
            self.redis_cli.set('Wechat_Event_Sendback', json.dumps(payload))
            time.sleep(0.5)

        while True:
            retjson = self.redis_cli.get('Wechat_Event_Sendback')
            if retjson:
                checkjson = retjson.decode(encoding="utf-8")
                checkjson.replace("\"","\'")
                self.redis_cli.delete('Wechat_Event_Sendback')
                break
            time.sleep(2)
        self.log.info(checkjson)
        confirm_value = json.loads(checkjson).get('value', '').strip()
        if confirm_value == 'Yes':
            return True
        return False


    def login_by_phone(self):
        self.login_type = 'msg'

        reqlogin = {
            'Whoami':'WeChat',
            'CMD':'Startup',
            'StartType':'msg',
            'country':'zhongguo'
        }

        reqlogin['phone'] = self.wechat.phone
        reqloginstr = json.dumps(reqlogin)
        self.avdmanager.send_message(reqloginstr)
        self.log.info("Wait for the message to send the verification code.")
        ansmsg = self.avdmanager.recv_message()

        ansdict = json.loads(ansmsg)
        if ansdict.get('CMD') == 'StartupRet' and ansdict.get('StartType') == 'msg':
            if ansdict.get('Status') == 'fail':
                self.log.error('The request for SMS verification code failed.')
                return ''
            else:
                pass

        self.log.info("Vericode send to phone : {}".format(self.wechat.phone))
        time.sleep(0.2)

        submit_count = 1
        keyword = ''
        while submit_count <= 4:
            keyword = self.submit_vericode(submit_count)
            if not keyword:
                submit_count += 1
                continue
            break
        return keyword


    def login_control(self):
        if utils.is_phone_num(self.wechat.user):
            self.wechat.phone = self.wechat.user

        keyword = ''
        if self.wechat.user and self.wechat.pwd:
            try:
                keyword = self.login_by_pwd()
            except Exception as e:
                self.log.exception('login by pwd exception. error info: {}.'.format(e))
                return

        if keyword:
            return keyword

        # 用户决定是否需要进行短信验证码登录
        if not self.login_sms_confirm():
            return ''

        if self.wechat.phone:
            try:
                keyword = self.login_by_phone()
            except Exception as e:
                self.log.exception('login by phone exception. error info: {}.'.format(e))
                return
        return keyword


    def format_fee(self, fee):
        fee = int(fee) / 100
        return '%.2f' % fee


    def fetch_userinfo(self):
        """
        获取微信用户信息
        当前只保存微信账号 用于界面区分账号进行显示
        :return:
        """
        self.log.info('开始获取微信用户信息。')
        self.create_table('TBL_PRCD_WECHAT_USER_INFO', True)
        sql = '''INSERT INTO "TBL_PRCD_WECHAT_USER_INFO" ("account", "phone" ) VALUES('{}','{}') '''.format(
                self.wechat.user, self.wechat.phone)
        self.sql_execute_try(sql)


    def save_by_list(self, bill_list:list, exportkey:str):
        for bill in bill_list:
            try:
                sql = self.parse_bill(exportkey, bill)
                if sql:
                    self.sql_execute_try(sql)
            except Exception as e:
                self.log.exception('save bills exception. errorinfo:{}'.format(e))
                continue


    def parse_bill(self, exportkey, bill:dict):
        """
        解析账单信息
        :param bill:
        :return:
        """
        timestamp = bill.get('timestamp','')
        trans_id = bill.get('bill_type', '')
        bill_id = bill.get('bill_id', '')
        bill_type = bill.get('bill_type', '')

        sql = self.parse_simple_bill(bill)
        detail_result = self.request_bill_detail(exportkey, timestamp, trans_id, bill_type, bill_id)
        if 'user_roll_detail' in detail_result.keys():
            sql = self.parse_api_bill_detail(bill, detail_result)
            return sql

        if 'header' in detail_result.keys() and 'preview' in detail_result.keys():
            sql = self.parse_web_bill_detail(bill, detail_result)
            return sql

        return sql


    def parse_simple_bill(self, bill:dict):
        """
        解析简要账单信息
        :param bill:
        :return:
        """
        if not isinstance(bill, dict):
            return ''

        # 账单ID
        bill_id = bill.get('bill_id', '')
        # 交易ID
        trans_id = bill.get('trans_id', '')
        # 交易抬头
        title = bill.get('title', '')
        # 时间戳
        timestamp = bill.get('timestamp', '')
        trade_time = datetime_format(timestamp)
        # 交易金额
        fee = bill.get('fee', 0)
        fee = self.format_fee(fee)
        # 金额类型
        fee_type = bill.get('fee_type', '')
        # 收入/支出
        fee_attr = bill.get('fee_attr', '')
        # 当前状态
        current_state = bill.get('current_state', '')
        # 当前状态类型
        current_state_type = bill.get('current_state_type', '')
        # 账单类型
        bill_type = bill.get('bill_type', '')
        # 交易单号
        out_trade_no = bill.get('out_trade_no', '')
        # 总退还费用
        total_refund_fee = bill.get('total_refund_fee', '')
        # 交易分类
        classify_type = bill.get('classify_type', '')
        # 支付银行/零钱
        pay_bank_name = bill.get('pay_bank_name', '')
        # 备注
        remark = bill.get('remark', '')
        # 商品数据
        business_data = bill.get('business_data', '')
        # 充值金额
        charge_fee = bill.get('charge_fee', 0)
        # 付款人备注
        payer_remark = bill.get('payer_remark', '')
        #
        payer_uin = bill.get('payer_uin', '')
        # 付款人微信ID
        payer_name = bill.get('payer_wxid', '')
        # 是否是朋友
        is_friend = bill.get('is_friend', '')

        pay_fee = 0
        pay_time = ''
        # 转账、二维码收付款、微信红包、信用卡还款、扫码支付、向群收款支付
        if bill_type == 1 :
            pay_fee = fee
            pay_time = trade_time

        recv_fee = 0
        recv_time = ''
        receiver_name = ''

        # 微信红包 收取好友红包
        if bill_type == 6 and classify_type == 2:
            recv_fee = fee
            recv_time = trade_time

        # 微信转账 收到转账
        if bill_type == 4 and classify_type == 1:
            recv_fee = fee
            recv_time = trade_time

        # 提款
        if bill_type == 20 and classify_type == 11:
            recv_fee = fee
            recv_time = trade_time

        # 提现金额
        withdraw_fee = 0
        withdraw_apply_time = ''
        # 零钱提现
        if bill_type == 7 and classify_type == 53:
            withdraw_fee = fee
            withdraw_apply_time = trade_time

        # 充值金额
        charge_fee = 0
        charge_time = ''
        # 充值
        if bill_type == 2 and classify_type == 97:
            charge_fee = fee
            charge_time = trade_time

        # 退款金额
        refund_flow_fee = 0
        refund_flow_time = ''
        # 退款（红包退款、商家退款）
        if bill_type == 11 and classify_type == 31:
            refund_flow_fee = fee
            refund_flow_time = trade_time

        sql = '''INSERT INTO "TBL_PRCD_WECHAT_BILL_RECORDS" ("title", "bill_id","current_state","pay_fee",
        "withdraw_fee","charge_fee","recv_fee","classify_type","bill_type","payer_name", 
        "pay_time","recv_time","withdraw_apply_time", 
        "charge_time", "pay_bank_name", "out_trade_no","trans_id","refund_flow_fee", "refund_flow_time", 
        "source_acct") VALUES({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},{})'''

        params = (title, bill_id, current_state, pay_fee, withdraw_fee, charge_fee, recv_fee, classify_type, bill_type,
                  payer_name, pay_time, recv_time, withdraw_apply_time,
                  charge_time, pay_bank_name, out_trade_no, trans_id, refund_flow_fee, refund_flow_time, self.wechat.account)

        return sql_format(sql, params)


    def parse_api_bill_detail(self, bill:dict, detail_result:dict):
        """
        解析api版本接口 账单详情结果
        :param title: 标题
        :param bill_id: 账单id
        :param trans_id: 交易id
        :param timestamp: 时间戳
        :param classify: 分类
        :param detail_result: 账单详情结果集
        :return: sql: str
        """

        title = bill.get('title', '')
        bill_id = bill.get('bill_id', '')
        bill_type = bill.get('bill_type', '')
        trans_id = bill.get('trans_id', '')
        timestamp = bill.get('timestamp','')
        classify_type = bill.get('classify_type', '')

        if not isinstance(detail_result, dict):
            return ''

        user_roll_detail = detail_result.get('user_roll_detail', {})
        # 费用类型
        fee_type = user_roll_detail.get('fee_type', '')

        # 支付人微信id
        payer_wxid = user_roll_detail.get('payer_wxid', '')
        # 支付金额
        pay_fee = user_roll_detail.get('pay_fee', 0)
        pay_fee = self.format_fee(pay_fee)
        # 商品名称
        goods_name = user_roll_detail.get('goods_name', '')
        # 商户简称
        mch_name = user_roll_detail.get('mch_name', '')
        # 当前状态 支付状态
        current_state = user_roll_detail.get('current_state', '')
        # 支付时间
        pay_time = user_roll_detail.get('pay_time', '')
        pay_time = datetime_format(pay_time)
        # 支付方式 零钱/银行名称
        pay_bank_name = user_roll_detail.get('pay_bank_name', '')
        # 交易单号
        out_trade_no = user_roll_detail.get('out_trade_no', '')
        # 转账单号
        trans_id = user_roll_detail.get('trans_id', '')
        # 费用单位
        fee_unit = user_roll_detail.get('fee_unit', '')
        # 商户全称
        mch_full_name = user_roll_detail.get('mch_full_name', '')
        # 接收人姓名
        receiver_name = user_roll_detail.get('receiver_name', '')
        # 转账时间
        transfer_pay_time = user_roll_detail.get('transfer_pay_time', '')
        transfer_pay_time = datetime_format(transfer_pay_time)
        # 转账单号
        transfer_trans_id = user_roll_detail.get('transfer_trans_id', '')
        # 收款方备注
        receiver_remark = user_roll_detail.get('receiver_remark', '')
        # 收钱时间
        transfer_recv_time = user_roll_detail.get('transfer_recv_time', '')
        transfer_recv_time = datetime_format(transfer_recv_time)
        # 接收方微信id
        receiver_wxid = user_roll_detail.get('receiver_wxid', '')
        # 转账说明
        transfer_detail = user_roll_detail.get('transfer_detail', '')
        withdraw_fee = user_roll_detail.get('withdraw_fee', 0)
        withdraw_fee = self.format_fee(withdraw_fee)
        # 提现申请时间
        withdraw_apply_time = user_roll_detail.get('withdraw_apply_time', '')
        withdraw_apply_time = datetime_format(withdraw_apply_time)
        # 提现到账时间
        withdraw_arrive_time = user_roll_detail.get('withdraw_arrive_time', '')
        withdraw_arrive_time = datetime_format(withdraw_arrive_time)
        # 提现银行名称
        withdraw_bank_name = user_roll_detail.get('withdraw_bank_name', '')
        # 提现单号
        withdraw_trans_id = user_roll_detail.get('withdraw_trans_id', '')
        # 实际提现金额
        real_withdraw_fee = user_roll_detail.get('real_withdraw_fee', 0)
        real_withdraw_fee = self.format_fee(real_withdraw_fee)
        # 提现费用
        real_withdraw_charge = user_roll_detail.get('real_withdraw_charge', 0)
        real_withdraw_charge = self.format_fee(real_withdraw_charge)
        # 银行卡尾号
        card_tail = user_roll_detail.get('card_tail', '')
        # 退款金额
        refund_flow_fee = user_roll_detail.get('refund_flow_fee', 0)
        refund_flow_fee = self.format_fee(refund_flow_fee)
        # 退款状态
        refund_flow_status = user_roll_detail.get('refund_flow_status', '')
        # 退款时间
        refund_flow_time = user_roll_detail.get('refund_flow_time', '')
        refund_flow_time = datetime_format(refund_flow_time)
        # 退款银行
        refund_flow_bank_name = user_roll_detail.get('refund_flow_bank_name', '')
        # 退款id
        refund_flow_refund_id = user_roll_detail.get('refund_flow_refund_id', '')
        # 退款交易单号
        refund_flow_out_trade_no = user_roll_detail.get('refund_flow_out_trade_no', '')
        # 原生单号
        jump_refund_flow_origin_id = user_roll_detail.get('jump_refund_flow_origin_id', '')
        # 充值时间
        charge_time = user_roll_detail.get('charge_time', '')
        charge_time = datetime_format(charge_time)
        charge_fee = user_roll_detail.get('charge_fee', 0)
        charge_fee = self.format_fee(charge_fee)
        recv_fee = user_roll_detail.get('recv_fee', 0)
        recv_fee = self.format_fee(recv_fee)
        # 收款时间
        recv_time = user_roll_detail.get('recv_time', '')
        recv_time = datetime_format(recv_time)
        # 交易单号
        out_trade_no = user_roll_detail.get('out_trade_no', '')

        payer_name = self.match_payer_name(title, bill_type, classify_type)
        receiver_name = self.match_receiver_name(title, bill_type, classify_type)

        sql = '''INSERT INTO "TBL_PRCD_WECHAT_BILL_RECORDS" ("title", "bill_id","current_state", "pay_fee","withdraw_fee",
        "charge_fee","recv_fee","classify_type","bill_type","payer_name","receiver_name", "payer_wxid","receiver_wxid","transfer_detail","receiver_remark",
        "goods_name","mch_name","mch_full_name", "pay_time","recv_time","transfer_pay_time", "transfer_recv_time","withdraw_apply_time",
        "withdraw_arrive_time", "charge_time", "pay_bank_name", "withdraw_bank_name","out_trade_no", "trans_id","transfer_trans_id",
        "withdraw_trans_id","real_withdraw_fee","real_withdraw_charge","card_tail","refund_flow_fee", "refund_flow_status",
        "refund_flow_time","refund_flow_bank_name","refund_flow_refund_id","refund_flow_out_trade_no","source_acct") VALUES
        ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},{}, {}, {}, {}, {}, {},{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, 
        {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'''

        params = (title, bill_id, current_state, pay_fee, withdraw_fee, charge_fee, recv_fee, classify_type,
                  bill_type, payer_name, receiver_name, payer_wxid, receiver_wxid,transfer_detail, receiver_remark, goods_name, mch_name,
                  mch_full_name, pay_time, recv_time, transfer_pay_time, transfer_recv_time, withdraw_apply_time,
                  withdraw_arrive_time, charge_time, pay_bank_name, withdraw_bank_name, out_trade_no, trans_id,
                  transfer_trans_id, withdraw_trans_id, real_withdraw_fee, real_withdraw_charge, card_tail,
                  refund_flow_fee, refund_flow_status, refund_flow_time, refund_flow_bank_name, refund_flow_refund_id,
                  refund_flow_out_trade_no, self.wechat.account)

        return sql_format(sql, params)


    def parse_web_bill_detail(self, bill:dict, detail_result:dict):
        """
        解析网页版账单详情
        :param title: 账单抬头
        :param bill_id: 账单id
        :param trans_id: 交易id
        :param timestamp: 时间戳
        :param classify_type: 分类
        :param bill_type: 账单类型
        :param bill_result: 账单结果集
        :return: sql:str
        """

        def make_key_pair(detail_result: dict):
            bill_dict = {}
            preview = detail_result.get('preview', [])
            if not preview:
                return bill_dict

            for part in preview:
                label = part.get('label', {})
                if not label:
                    continue

                label_name = label.get('name', '')
                if not label_name:
                    continue

                value = part.get('value', [])
                if not value:
                    continue

                label_value = ''
                try:
                    label_value = value[0].get('name', '')
                except:
                    pass
                bill_dict[label_name] = label_value
            return bill_dict

        title = bill.get('title', '')
        bill_id = bill.get('bill_id', '')
        bill_type = bill.get('bill_type', '')
        trans_id = bill.get('trans_id', '')
        timestamp = bill.get('timestamp', '')
        classify_type = bill.get('classify_type', '')
        payer_wxid = bill.get('payer_wxid', '')
        out_trade_no = bill.get('out_trade_no', '')
        receiver_wxid = bill.get('receiver_wxid', '')
        header = detail_result.get('header', {})

        payer_name = self.match_payer_name(title, bill_type, classify_type)
        receiver_name = self.match_receiver_name(title, bill_type, classify_type)

        fee = header.get('fee', 0)
        bill_dict = make_key_pair(detail_result)
        current_state = bill_dict.get('当前状态', '')
        pay_time = bill_dict.get('支付时间', '')
        pay_time = datetime_format(pay_time)
        recv_time = bill_dict.get('收款时间', '')
        recv_time = datetime_format(recv_time)
        pay_bank_name = bill_dict.get('支付方式', '')
        out_trade_no = bill_dict.get('交易单号', '')
        mch_id = bill_dict.get('商户单号', '')
        hongbao_detail = bill_dict.get('红包详情', '')
        receiver_remark = bill_dict.get('收款方备注', '')
        transfer_pay_time = bill_dict.get('转账时间', '')
        transfer_pay_time = datetime_format(transfer_pay_time)
        transfer_trans_id = bill_dict.get('转账单号', '')
        goods_name = bill_dict.get('商品', '')
        charge_time = bill_dict.get('充值时间', '')
        charge_time = datetime_format(charge_time)
        mch_full_name = bill_dict.get('商户全称', '')
        good_price = bill_dict.get('原价', 0)
        discounts = bill_dict.get('优惠', '')
        refund_flow_status = bill_dict.get('退款状态', '')
        refund_flow_time = bill_dict.get('退款时间', '')
        refund_flow_time = datetime_format(refund_flow_time)
        refund_flow_bank_name = bill_dict.get('退款方式', '')
        refund_flow_out_trade_no = bill_dict.get('退款单号', '')
        withdraw_fee = bill_dict.get('提现金额', 0)
        service_fee = bill_dict.get('手续费', 0)
        withdraw_apply_time = bill_dict.get('申请时间', '')
        withdraw_apply_time = datetime_format(withdraw_apply_time)
        withdraw_arrive_time = bill_dict.get('到账时间', '')
        withdraw_arrive_time = datetime_format(withdraw_arrive_time)
        withdraw_bank_name = bill_dict.get('提现银行', '')
        withdraw_trans_id = bill_dict.get('提现单号', '')

        pay_fee = 0
        recv_fee = 0
        withdraw_fee = 0
        charge_fee = 0
        refund_flow_fee = 0

        # 转账 扫码支付 群收款 信用卡还款
        if bill_type == 1 :
            pay_fee = fee

        # 微信红包 收取好友红包
        if (bill_type == 6 and classify_type == 2) or \
                (bill_type == 4 and classify_type == 1) or \
                (bill_type == 20 and classify_type == 11) or \
                (bill_type == 4 and classify_type == 3) or \
                (bill_type == 20 and classify_type == 99):
            recv_fee = fee

        # 零钱提现
        if bill_type == 7 and classify_type == 53:
            withdraw_fee = fee

        # 充值
        if bill_type == 2 and classify_type == 97:
            charge_fee = fee

        # 退款（红包退款、商家退款）
        if bill_type == 11 and classify_type == 31:
            refund_flow_fee = fee
            current_state = refund_flow_status

        sql = '''INSERT INTO "TBL_PRCD_WECHAT_BILL_RECORDS" ("title", "bill_id", "current_state", "pay_fee", "withdraw_fee",
                "charge_fee", "recv_fee", "classify_type", "bill_type","payer_name", "payer_wxid", "receiver_name", "receiver_wxid", 
                "receiver_remark", "goods_name", "mch_full_name",  "pay_time","recv_time","transfer_pay_time", "withdraw_apply_time", 
                "withdraw_arrive_time", "charge_time",  "pay_bank_name", "withdraw_bank_name", "out_trade_no","trans_id", 
                "transfer_trans_id","withdraw_trans_id", "refund_flow_fee", "refund_flow_status","refund_flow_time",
                "refund_flow_bank_name", "refund_flow_out_trade_no", "source_acct") VALUES({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, 
                {}, {}, {}, {}, {}, {}, {},{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},{})'''


        params = (title, bill_id, current_state, pay_fee, withdraw_fee, charge_fee, recv_fee, classify_type, bill_type,
                  payer_name, payer_wxid, receiver_name, receiver_wxid, receiver_remark, goods_name, mch_full_name,
                  pay_time, recv_time, transfer_pay_time, withdraw_apply_time, withdraw_arrive_time, charge_time,
                  pay_bank_name, withdraw_bank_name, out_trade_no, trans_id, transfer_trans_id, withdraw_trans_id,
                  refund_flow_fee, refund_flow_status, refund_flow_time, refund_flow_bank_name, refund_flow_out_trade_no, self.wechat.account)

        return sql_format(sql, params)


    def fetch_billing_records(self, exportkey, ticket):
        """
        获取微信账单记录
        :return:
        """
        classify_type = 0
        bills = []
        next_bills = []
        retparams = {}
        percent = 10

        unprogress = UnknownProgress(50, 1000)
        self.log.info('开始获取微信账单信息。')
        self.create_table('TBL_PRCD_WECHAT_BILL_RECORDS', True)
        try:
            errcode, errmsg, bills, retparams = self.wechat.get_firstpage_bills(classify_type, exportkey, ticket)
        except Exception as e:
            self.log.exception('fetch first page bills exception. errorinfo:{}'.format(e))
            self.request_exception_count += 1
            return

        if errcode != 0:
            self.log.error('fetch first page bills exception. errcode:{}, errmsg:{}'.format(errcode, errmsg))
            # self.pgbar.update(100, '{}'.format(errmsg))
            return

        if not bills:
            self.log.info('The first page has no bills.')
            return

        self.bills_count += len(bills)
        percent += unprogress.calc_cur_progress(self.bills_count)
        self.pgbar.update(percent, '交易记录({}条)'.format(self.bills_count))
        print('当前进度：{}，交易记录：{}'.format(percent, self.bills_count))

        self.save_by_list(bills, exportkey)

        if not retparams:
            self.log.info('The second page has no bills records.')
            return

        self.log.info('the second page bills info:{}'.format(retparams))

        while True:
            if self.is_cutoff_time(retparams.get('last_create_time', 0), config.CUT_OFF_TIME):
                self.log.info('The bills for the specified time has been obtained.{}'.format(config.CUT_OFF_TIME))
                return True

            try:
                errcode, errmsg, overflag, next_bills, retparams = self.wechat.get_nextpage_bills(classify_type, exportkey, ticket, retparams)
            except Exception as e:
                self.log.exception('fetch the next bills exception. errorinfo:{}'.format(e))
                self.request_exception_count += 1
                return

            if errcode != 0:
                self.log.error('fetch next page bills exception. errcode:{}, errmsg:{}'.format(errcode, errmsg))
                # self.pgbar.update(100, '{}'.format(errmsg))
                return

            if not next_bills:
                self.log.info('The next page has no bills.')
                return

            self.bills_count += len(next_bills)
            percent = unprogress.calc_cur_progress(self.bills_count) + 20

            self.pgbar.update(percent, '交易记录({}条)'.format(self.bills_count))
            print('当前进度：{}，交易记录：{}'.format(percent, self.bills_count))
            self.save_by_list(next_bills, exportkey)
            last_trans_id = retparams.get('last_trans_id', '')
            if not retparams or not last_trans_id:
                self.log.info('The next page has no bills records.')
                return

            self.log.info('the next page bills info:{}'.format(retparams))
        return True


    def parse_hb_detail(self, hb_info:dict):
        """
        解析红包 并格式化sql语句
        :return:
        """
        # print(hb_info)
        # 发送者昵称
        sender_nick = hb_info.get('sendNick', '')
        # 发送者微信号
        sender_wxid = hb_info.get('sendUserName', '')
        # 发送编号
        send_id = hb_info.get('sendId', '')
        # 红包发出的总金额
        total_amount = hb_info.get('totalAmount', '')
        total_amount = format_fee(total_amount)
        # 红包发出的总个数
        total_num = hb_info.get('totalNum', '')
        # 被领取的总金额
        recv_amount = hb_info.get('recAmount', '')
        recv_amount= format_fee(recv_amount)
        # 被领取的红包总数
        recv_num = hb_info.get('recNum', '')
        status_mess = hb_info.get('statusMess', '')
        # 接收人编号
        receiver_id = hb_info.get('receiveId', '')
        # 祝福语
        wishing = hb_info.get('wishing', '')
        # 当前用户是否是发送者
        is_sender = hb_info.get('isSender', '')
        # 红包头标题
        head_title = hb_info.get('headTitle', '')
        # 零钱去向
        change_words = hb_info.get('changeWording', '')
        # 领取状态
        receive_status = hb_info.get('receiveStatus', '')
        # 红包状态
        hbstatus = hb_info.get('hbStatus', '')
        # 红包类型 ：群发红包 / 一对一红包
        hbtype = hb_info.get('hbType', '')
        hbkind = ''
        can_share = ''

        sql = '''INSERT INTO "TBL_PRCD_WECHAT_HBDETAIL_INFO" 
          ("sendUserNick", "sendUserWxid", "sendId", "recNum", "totalNum", "totalAmount", "amount", "wishing", "isSender", "receiveId",
           "hbType", "hbStatus", "receiveStatus", "statusMess", "headTitle", "canShare", "hbKind", 
           "recAmount", "changeWording") 
           VALUES({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'''

        params = (sender_nick, sender_wxid, send_id, recv_num, total_num, total_amount, recv_amount, wishing, is_sender, receiver_id,
                  hbtype,  hbstatus, receive_status, status_mess, head_title, can_share, hbkind, recv_amount, change_words)

        return sql_format(sql, params)


    def parse_hb_receiver(self, hb_info:dict):
        """
        解析红包接收人信息， 并格式化sql语句
        :return:
        """
        receiver_list = []
        sql_list = []

        receiver_list = hb_info.get('receiven', [])

        send_id = hb_info.get('sendId', '')

        for receiver in receiver_list:
            # 接收者id
            receiver_id = receiver.get('recvId', '')
            # 接收者昵称
            receiver_nick = receiver.get('receivenNick', '')
            # 回复语
            answer = receiver.get('answer', '')
            # 小贴士
            game_tips = receiver.get('gameTips', '')
            # 接收金额
            recv_amount = receiver.get('receiveAmount', '')
            recv_amount = format_fee(recv_amount)
            # 接收时间
            recv_time = datetime_format(receiver.get('receiveTime', ''))
            # 微信id
            username = receiver.get('userName', '')

            sql = '''INSERT INTO "TBL_PRCD_WECHAT_HBRECEIVER_INFO" ("sendId", "receiveAmount", "receiveTime", "answer", 
            "receiveId", "receiveNick", "state", "gameTips","receiveOpenId", "userName") VALUES({},{},{},{},{},{},{},{},{},{})'''

            params = (send_id, recv_amount, recv_time, answer, receiver_id, receiver_nick, '', game_tips, '', username)
            sql_list.append(sql_format(sql, params))

        return sql_list


    def fetch_hb_detail(self):
        """
        获取红包详情
        :return:
        """
        self.log.info('开始获取红包详情。')
        self.create_table('TBL_PRCD_WECHAT_HBDETAIL_INFO', True)
        self.create_table('TBL_PRCD_WECHAT_HBRECEIVER_INFO', True)
        result = self.select_hb_id()
        # 红包总数
        hb_total_count = len(result)
        # 红包详情已记录数目
        hb_done_count = 0
        progress = 70
        try:
            block = 30/hb_total_count
        except:
            pass

        while len(result) > 0:
            ids_5, result = result[0:5], result[5:]
            hb_done_count += len(ids_5)
            progress = progress + block*len(ids_5)
            ids_5_str = ','.join(ids_5)
            reqlogin = {'Whoami': 'WeChat', 'CMD': 'LuckyMoney', 'IDs': ids_5_str, 'status': 'ok'}
            reqloginstr = json.dumps(reqlogin)
            # self.log.info('请求红包信息:{}'.format(reqloginstr))
            self.avdmanager.send_message(reqloginstr)
            msg = self.avdmanager.recv_message_ex()
            if not msg:
                break

            hb_list = json.loads(msg)

            # 数据拼接 还原每个id的数据
            hb_real_list = {}
            # 去重集合
            sendid_filter = set()
            for one in hb_list:
                if isinstance(one, str):
                    one = json.loads(one)
                send_id = one.get('sendId', '')
                if send_id and send_id not in sendid_filter:
                    hb_detail_sql = self.parse_hb_detail(one)
                    self.sql_execute_try(hb_detail_sql)
                    sendid_filter.add(send_id)

                receiver_sql_list = self.parse_hb_receiver(one)
                for receiver_sql in receiver_sql_list:
                    self.sql_execute_try(receiver_sql)

            self.pgbar.update(progress, "红包详情({}/{})".format(hb_done_count, hb_total_count))
            print("当前进度({}) 红包详情({}/{})".format(progress, hb_done_count, hb_total_count))

        reqlogin = {'Whoami': 'WeChat', 'CMD': 'LuckyMoney', 'status': 'over'}
        reqloginstr = json.dumps(reqlogin)
        self.log.info('请求红包结束:{}'.format(reqloginstr))
        self.avdmanager.send_message(reqloginstr)


    def select_hb_id(self):
        if not self.sqlconn.tableExists('TBL_PRCD_WECHAT_BILL_RECORDS'):
            log.error('table "TBL_PRCD_WECHAT_BILL_RECORDS" not exist')
            return

        sql = "select out_trade_no from TBL_PRCD_WECHAT_BILL_RECORDS where classify_type = '2' and (bill_type = '6' or '1')"
        smt = pyMyDatabase.SQLiteStatement(self.sqlconn, sql)

        result = []
        while smt.executeStep():
            out_trade_no = smt.getColumn(0)
            out_trade_no = out_trade_no.getText("") if not out_trade_no.isNull() else None
            result.append(out_trade_no)
        return result


    def create_table(self, tablename, drop_if_exist=True):
        if self.sqlconn.tableExists(tablename):
            self.log.info('table {} already exists'.format(tablename))
            if drop_if_exist:
                self.log.info('drop table:{}.'.format(tablename))
                self.sql_execute_try('DELETE FROM {}'.format(tablename))
        else:
            self.sql_execute_try(config.SQL_CREATETABLE.get(tablename, ''))


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
                    self.log.exception('sql_execute error! errorinfo:%s\r\nsql:%s' % (e, sql), exc_info=e)
                    return False
            break
        return True


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


    def request_bill_detail(self, exportkey, timestamp, trans_id, bill_type, bill_id):
        detail_result = {}
        first = True
        while True:
            try:
                detail_result = self.wechat.get_bill_detail(exportkey, timestamp, trans_id, bill_type, bill_id)
            except Exception as e:
                if first:
                    time.sleep(1)
                    first = False
                    continue
                else:
                    self.log.exception('request bill detail error. error info:{}'.format(e))
                    return

            retcode = detail_result.get('ret_code', '')
            retmsg = detail_result.get('ret_msg', '')
            if retcode != 0 or retmsg == 'CallFindErr':
                if first:
                    time.sleep(1)
                    first = False
                    continue
                else:
                    self.log.error('request bill detail failed. system message:{}'.format(retmsg))
                    return {}
            return detail_result


    def is_cutoff_time(self, input_time, cutoff_time):
        """
        判断是否已经过期
        :param input_time : 十位时间戳
        :param interval_second : 间隔秒数
        :return:
        """

        if cutoff_time == 0:
            return False

        if input_time < 0 or input_time < cutoff_time:
            return True

        return False


    @staticmethod
    def match_payer_name(title: str, bill_type: int, classify_type: int):
        """
        匹配出title中的
        :param title:
        :return:
        """

        # pos = pos_last_char(title, '二维码收款-来自')
        pos = title.find('二维码收款-来自')
        if pos != -1 :
            return title[pos+8:]

        # pos = pos_last_char(title, '微信红包-来自')
        pos = title.find('微信红包-来自')
        if pos != -1 :
            return title[pos+7:]

        # pos = pos_last_char(title, '群收款-来自')
        pos = title.find('群收款-来自')
        if pos != -1 :
            return title[pos+6:]

        # pos = pos_last_char(title, '转账-来自')
        pos = title.find('转账-来自')
        if pos != -1 :
            return title[pos+5:]

        return ''


    @staticmethod
    def match_receiver_name(title: str, bill_type: int, classify_type: int):
        """
        匹配出title中的
        :param title:
        :return:
        """

        # def pos_last_char(sourcestr, substr):
        #     pos = sourcestr.find(substr)
        #     return pos + len(substr)

        if bill_type == 1 and classify_type == 6:
            return title

        # pos = pos_last_char(title, '扫二维码付款-给')
        pos = title.find('扫二维码付款-给')
        if pos != -1 :
            return title[pos+8:]

        # pos = pos_last_char(title, '群收款-转给')
        pos = title.find('群收款-转给')
        if pos != -1:
            return title[pos+6:]

        # pos = pos_last_char(title, '转账-转给')
        pos = title.find('转账-转给')
        if pos != -1 :
            return title[pos+5:]

        return ''







