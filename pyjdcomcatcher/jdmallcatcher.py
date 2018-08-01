
# -*- coding: utf-8 -*-

# @Function :
# @Time     : 2018/4/18
# @Author   : Zhangjw
# @File     : jdcomcatcher.py
# @Company  : Meiya Pico
import os
import sys
import json
import time
from pyDes import *
import base64
import socket
import pathlib
import re
from pyjdmallcatcher.avdmanage import AVDManager
from pyjdmallcatcher import config
from pyjdmallcatcher import tool
from pyjdmallcatcher.downloader import Downloader
sys.path.append(config.BIN64_PATH)
import pyMyDatabase

class JDMallCatcher(object):
    def __init__(self, jdcomapi, progress, amf_path, log):
        self.jdcomapi = jdcomapi
        self.avdmanager = AVDManager(log, config.ANDROID_PATH)
        self.redis_cli = self.avdmanager.redis_cli
        self.amf_path = amf_path
        self.progress = progress
        self._conn = self._sqlconn
        self.order_list = []
        self.log = log
        self.root = pathlib.Path(amf_path).parent.parent.__str__()
        self.down = Downloader()
        self.request_exception_count = 0

    def __del__(self):
        pass

    @property
    def _sqlconn(self):
        try:
            sqlconn = pyMyDatabase.SQLiteDatabase(self.amf_path, True)
        except Exception as e:
            self.log.error("WechatCatcher connect the sqlite:{} failed. error info:{}".format(self.amf_path, e))
            self.log.error('Program exit.')
            os._exit(1)
        return sqlconn


    def login_by_tokne(self):
        """
        token 登录 合法性校验
        :return:
        """

        sign = ''
        retcode = -1
        address_list = []
        result = None
        body = 'body={}&'
        body_for_sign = '{}'

        sign_param = {
            'Whoami': 'JD',
            'CMD': 'GetSign',
            'funcid': 'easyBuyGetAddress',
            'uuid': self.jdcomapi.uuid,
            'body': body_for_sign
        }

        payload = json.dumps(sign_param)
        self.avdmanager.send_message(payload)
        ansmsg = self.avdmanager.recv_message()
        sign_dict = json.loads(ansmsg)

        try:
            result = self.jdcomapi.get_address_info(sign_dict.get('sign'))
        except Exception as e:
            self.log.exception("fetch address info error : {}".format(e))
            return False

        retcode = result.get('code', '')
        address_list = result.get('addressList')
        if retcode != "0" or not address_list:
            self.log.error("login by token failed. errorinfo: {}".format(result))
            return False
        return True

    def login_control(self):
        """
        登录控制
        :return:
        """
        if tool.is_phone_num(self.jdcomapi.username):
            self.jdcomapi.phone = self.jdcomapi.username

        if self.jdcomapi.pin and self.jdcomapi.uuid and self.jdcomapi.wskey and \
                self.jdcomapi.whwswswws and self.jdcomapi.installtionId:
            if self.login_by_tokne():
                return True
        else:
            self.log.info("Login information is incomplete or invalid.")

        if self.jdcomapi.username and self.jdcomapi.password:
            if self.login_by_pwd():
                self.log.info("login success by password.")
                return True
            else:
                self.log.info("login failure by password.")

        if self.jdcomapi.phone:
            if self.login_by_phone():
                self.log.info("login success by password.")
                return True

        return False


    def request_sms_code(self):
        """
        请求短信验证码
        :return:
        """

        params = {
            'Whoami': 'JD',
            'CMD': 'LoginFromMsg',
            'phone': self.jdcomapi.phone
        }

        payload = json.dumps(params)
        self.avdmanager.send_message(payload)
        ansmsg = self.avdmanager.recv_message()
        ans_dict = json.loads(ansmsg)
        status = ans_dict.get('status','')
        return status


    def check_sms_code(self, checkcode:str):
        """
        提交 并 校验短信验证码
        :return:
        """
        params = {
            'Whoami': 'JD',
            'CMD': 'GetWskeyFromMsg',
            'vericode': checkcode
        }

        payload = json.dumps(params)
        self.avdmanager.send_message(payload)
        ansmsg = self.avdmanager.recv_message()

        ans_dict = json.loads(ansmsg)

        errno = ans_dict.get('errno', '')

        self.jdcomapi.wskey = ans_dict.get('wskey','')
        self.jdcomapi.pin = self.jdcomapi.format_pin(ans_dict.get('pin',''))

        self.jdcomapi.cookie = "pin={};wskey={};whwswswws={};".format(self.jdcomapi.pin, self.jdcomapi.wskey,
                                                                      self.jdcomapi.whwswswws)
        return errno


    def request_smscode_from_ui(self, sms_type:int):
        """
        从redis读取短信验证码
        :return:
        """
        checkcode = ''

        checkmsg = {
            "type": 0,
            "value": self.jdcomapi.phone
        }

        if sms_type == 1 :
            checkmsg['errno'] = 1
            checkmsg['desc'] = '验证码已发送至{}, 请输入短信验证码。'.format(self.jdcomapi.phone)
        elif sms_type == 2 :
            checkmsg['errno'] = 2
            checkmsg['desc'] = '校验失败，请重新输入。'
        elif sms_type == 3 :
            checkmsg['errno'] = 3
            checkmsg['desc'] = '校验3次失败，请重新进行取证。'

        self.log.info(checkmsg)
        self.redis_cli.set('JingDong_Verify_Send', json.dumps(checkmsg))

        retjson = ''
        while True:
            if config.DEBUG:
                print("请输入手机号{}接收到的短信验证码:".format(self.jdcomapi.phone))
                checkcode = input()
                return checkcode.strip()
            else:
                retjson = self.redis_cli.get('JingDong_Verify_Sendback')
                self.log.info(retjson)
                if retjson:
                    self.redis_cli.delete('JingDong_Verify_Sendback')
                    break
            time.sleep(2)

        checkcode = json.loads(retjson).get('value', '').strip()
        return checkcode


    def verify_operation(self, verify_type:int, verify_source:str, verify_num:int):
        """
        从redis读取短信验证码
        :return:
        """
        checkcode = ''

        checkmsg = {
            "type": verify_type,
            "value": verify_source
        }

        if verify_num == 1:
            checkmsg['errno'] = 1
            checkmsg['desc'] = ''
        elif verify_num == 2 :
            checkmsg['errno'] = 2
            checkmsg['desc'] = '校验失败，请重新输入。'
        elif verify_num == 3:
            checkmsg['errno'] = 3
            checkmsg['desc'] = '校验3次失败，请重新进行取证。'

        self.log.info(checkmsg)
        self.redis_cli.set('JingDong_Verify_Send', json.dumps(checkmsg))

        retjson = ''

        if config.DEBUG:
            print("请输入验证码:")
            checkcode = input()
            self.redis_cli.delete('JingDong_Verify_Send')
            return checkcode.strip()
        else:
            retjson = self.redis_cli.get('JingDong_Verify_Sendback')
            if retjson:
                self.redis_cli.delete('JingDong_Verify_Sendback')

        checkcode = json.loads(retjson).get('value', '').strip()
        return checkcode


    def login_by_phone(self):
        """
        通过短信验证码进行登录
        :return:
        """
        check_count = 1
        errno = ''
        errmsg = ''

        error_msg_dict = {
            '1':'账号不存在',
            '2':'手机号码格式错误',
            '3':'验证码已过期',
            '4':'验证码输入错误',
            '5':'验证码次数达上限',
        }

        errno = self.request_sms_code()
        if errno == '0':
            while check_count <= 3:
                # 获取短信验证码 并 登陆
                checkcode = self.request_smscode_from_ui(check_count)
                if not checkcode:
                    check_count += 1
                    continue

                errno = self.check_sms_code(checkcode)
                if errno != '0':
                    self.log.error("SMS checkout failed, please reenter.")
                    check_count += 1
                    continue
                else:
                    return True

        errmsg = error_msg_dict.get(errno, '未知错误')

        print(errmsg)
        self.progress.update(0, errmsg)
        return False


    def login_by_pwd(self):
        """

        :return:
        """
        error_msg_dict = {
            '1': '账号不存在',
            '2': '图片验证码',
            '3': '密码错误',
            '4': '密码错误次数超过10次，请30分钟后再试',
            '5': '您的账号存在安全风险，请联系客服',
            '6': '图片验证码错误'
        }

        check_count = 1
        login_result = self.login_without_verifycode()

        error_code = login_result.get('errno', '')
        if error_code == '0':
            self.jdcomapi.wskey = login_result.get('wskey', '')
            self.jdcomapi.pin = self.jdcomapi.format_pin(login_result.get('pin', ''))
            self.jdcomapi.cookie = "pin={};wskey={};whwswswws={};".format(self.jdcomapi.pin, self.jdcomapi.wskey,
                                                                          self.jdcomapi.whwswswws)
            return True

        while check_count <= 3:
            if error_code == '6' or error_code == '2':
                encrypt_pic_data = login_result.get('pic', '')
                decrypt_pic_data = base64.b64decode(encrypt_pic_data)
                if not os.path.exists(config.VERIFY_PICS_FOLDER):
                    os.makedirs(config.VERIFY_PICS_FOLDER)

                vericode_pic_path = config.VERIFY_PICS_FOLDER + config.VERIFY_PIC_NAME
                with open(vericode_pic_path, 'wb') as f:
                    f.write(decrypt_pic_data)

                print(vericode_pic_path)

                vericode = self.verify_operation(1, vericode_pic_path, check_count)

                login_result = self.login_with_verifycode(vericode)

                error_code = login_result.get('errno', '')
                if error_code == '0':
                    self.jdcomapi.wskey = login_result.get('wskey', '')
                    self.jdcomapi.pin = self.jdcomapi.format_pin(login_result.get('pin', ''))
                    self.jdcomapi.cookie = "pin={};wskey={};whwswswws={};".format(self.jdcomapi.pin,
                                                                                  self.jdcomapi.wskey,
                                                                                  self.jdcomapi.whwswswws)
                    return True
                else:
                    check_count += 1
                    continue
            break

        self.log.info(error_msg_dict.get(error_code, '未知错误'))
        self.progress.update(0, error_msg_dict.get(error_code, '未知错误'))
        return False


    def login_without_verifycode(self):
        """

        :return:
        """

        sign_param = {
            'Whoami': 'JD',
            'CMD': 'GetWskey',
            'account': self.jdcomapi.username,
            'pwd': self.jdcomapi.password
        }
        try:
            payload = json.dumps(sign_param)
            self.avdmanager.send_message(payload)
            ansmsg = self.avdmanager.recv_max_message()
        except:
            return {}

        return json.loads(ansmsg)


    def login_with_verifycode(self, vericode):
        """

        :return:
        """
        # 提交验证码并登录
        data = {'Whoami': 'JD',
                'CMD': 'GetWskeyWithVericode',
                'account': self.jdcomapi.username,
                'pwd': self.jdcomapi.password,
                'vericode': vericode,
                }
        try:
            payload = json.dumps(data)
            self.avdmanager.send_message(payload)
            ansmsg = self.avdmanager.recv_max_message()
        except:
            return {}

        return json.loads(ansmsg)


    def fetch_user_info(self):
        """
        获取京东用户信息
        :return:
        """
        self.log.info("【用户信息】")
        self.create_table("TBL_PRCD_JDCOM_USER_INFO", True)
        sql = '''INSERT INTO "TBL_PRCD_JDCOM_USER_INFO" ("strAccount") VALUES('{}')'''.format(self.jdcomapi.account)

        if not self.sql_execute_try(sql):
            return False
        self.progress.update(10, '正在获取')
        return True

    def _parse_address_info(self, address):
        """
        解析地址信息并返回sql
        :return:
        """
        if not isinstance(address, dict):
            self.log.error('The data should be dict , so cannot be resolved. {}'.format(type(address)))
            return

        address_id = address.get('id','')
        address_tag = ''
        if 'addressTagMap' in address.keys():
            address_tag = address.get('addressTagMap').get('addressTagName')
        is_default_addr = address.get('addressDefault','')
        user_name = address.get('name', '')
        full_address = address.get('fullAddress', '')
        address_detail = address.get('addressDetail', '')
        mobile = address.get('mobile', '')
        phone = address.get('phone', '')
        payment_id = address.get('paymentId', '')
        coord_type = address.get('coord_type', '')
        longitude = address.get('longitude', '')
        latitude = address.get('latitude', '')

        sql = '''INSERT INTO "TBL_PRCD_JDCOM_ADDRESS_INFO" ("strAddressId", "strAddressTag", "strAddressDefault", 
                "strConsignee", "strRegion", "strAddress", "strMobile", "strPhone", "strPaymentId", "strCoordType", 
                "strLongitude", "strLatitude", "strSrcAccount") VALUES({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
                '''

        params = (address_id, address_tag, is_default_addr, user_name, full_address, address_detail, mobile, phone,
                  payment_id, coord_type, longitude, latitude, self.jdcomapi.account)

        return tool.sql_format(sql, params)

    def fetch_address_info(self):
        """
        获取并保存收货地址信息
        :return:
        """
        self.log.info("【收货地址信息】")
        if not self.create_table('TBL_PRCD_JDCOM_ADDRESS_INFO', True):
            self.log.error("create table failed. tablename: 'TBL_PRCD_JDCOM_ADDRESS_INFO'. ")
            return False

        sign = ''
        retcode = -1
        address_list = []
        result = None
        body = 'body={}&'
        body_for_sign = '{}'

        sign_param = {
            'Whoami':'JD',
            'CMD':'GetSign',
            'funcid' : 'easyBuyGetAddress',
            'uuid' : self.jdcomapi.uuid,
            'body' : body_for_sign
        }

        payload = json.dumps(sign_param)
        self.avdmanager.send_message(payload)
        ansmsg = self.avdmanager.recv_message()
        sign_dict = json.loads(ansmsg)

        try:
            result = self.jdcomapi.get_address_info(sign_dict.get('sign'))
            self.log.info(result)
        except Exception as e:
            self.log.exception("fetch address info error : {}".format(e))
            self.request_exception_count += 1
            return False

        retcode = result.get('code','')
        address_list = result.get('addressList')
        if retcode != "0" or not address_list:
            self.log.error("fetch user address failed. errorinfo: {}".format(result))
            return False

        for address in result.get('addressList'):
            try:
                sql = self._parse_address_info(address)
                self.sql_execute_try(sql)
            except Exception as e:
                self.log.exception("An exception occurs when inserted address data:{}".format(e))
                continue
        self.progress.update(20, '正在获取')
        return True

    def parse_order_info(self, order):
        """
        解析地址信息并返回sql
        :return:
        """
        order_id = order.get('orderId', '')
        order_status = order.get('orderStatus', '')
        submit_time = order.get('dataSubmit', '')
        order_price = order.get('price', '')
        payment_type = order.get('paymentType', '')
        shop_name = order.get('shopName', '')
        branch_id = order.get('idCompanyBranch', '')
        order_type = order.get('orderType', '')
        ware_count = order.get('wareCountMessage', '')
        detail_price = order.get('detailPrice', '')
        list_price = order.get('listPrice', '')

        sql = '''INSERT INTO "TBL_PRCD_JDCOM_ORDER_INFO" ("strOrderId", "strOrderStatus", "strSubmitDate", 
                "strPrice", "strPaymentType", "strShopName", "strBranchId", "strOrderType", "strWareCountMsg",
                "strDetailPrice","strListPrice","strSrcAccount") VALUES({}, {}, {}, {}, {}, {}, {},{}, {},{},{}, {})
              '''

        params=(order_id, order_status, submit_time, order_price,payment_type, shop_name, branch_id, order_type,
                ware_count, detail_price, list_price, self.jdcomapi.account)
        return tool.sql_format(sql, params)

    def order_info(self, page_no = 1):
        """
        订单详情
        :return:
        """
        sign = ''
        result = None
        order_list = []
        page_num = '"{}"'.format(page_no)
        body_for_sign = '{"page":%s,"pagesize":"100","plugin_version":60606}' % page_num
        body = 'body={}&'.format(body_for_sign)

        sign_param = {
            'Whoami':'JD',
            'CMD':'GetSign',
            'funcid' : 'newUserAllOrderList',
            'uuid' : self.jdcomapi.uuid,
            'body' : body_for_sign
        }

        payload = json.dumps(sign_param)

        self.avdmanager.send_message(payload)
        ansmsg = self.avdmanager.recv_message()
        sign_dict = json.loads(ansmsg)
        result = self.jdcomapi.get_order_info(sign_dict.get('sign'), body)
        order_list = result.get('orderList', [])
        return order_list


    def fetch_order_info(self):
        """
        获取订单信息
        :return:
        """
        self.log.info('【商品订单信息】')

        if not self.create_table('TBL_PRCD_JDCOM_ORDER_INFO', True):
            self.log.error("create table failed. tablename: 'TBL_PRCD_JDCOM_ORDER_INFO'. ")
            return

        if not self.create_table('TBL_PRCD_JDCOM_GOODS_INFO', True):
            self.log.error("create table failed. tablename: 'TBL_PRCD_JDCOM_GOODS_INFO'. ")
            return

        page_no = 1
        order_list = []
        sql_list = []
        while True:
            try:
                order_list = self.order_info(page_no)
            except Exception as e:
                self.log.error("requests the {} page order info exception.".format(page_no))
                time.sleep(0.05)
                self.request_exception_count += 1
                page_no += 1
                continue

            if not order_list:
                return False

            self.order_list.extend(order_list)

            for order in order_list:
                try:
                    sql = self.parse_order_info(order)
                    self.sql_execute_try(sql)
                except Exception as e:
                    self.log.exception("An exception occurs when parse order info:{}".format(e))

            page_no += 1

        self.progress.update(50, '正在获取')
        return True


    def order_detail(self, order_id):
        """
        单个订单详情
        :return:
        """
        sign = ''
        result = None

        body_for_sign = '{"from": "OrderList", "plugin_version": 60606}'
        sign_dict = json.loads(body_for_sign)
        sign_dict['isPublish'] = 'true'
        sign_dict['orderId'] = order_id
        body_for_sign = json.dumps(sign_dict)
        body = 'body={}&'.format(body_for_sign)

        sign_param = {
            'Whoami': 'JD',
            'CMD': 'GetSign',
            'funcid': 'orderDetailInfo',
            'uuid': self.jdcomapi.uuid,
            'body': body_for_sign
        }

        payload = json.dumps(sign_param)
        self.avdmanager.send_message(payload)
        ansmsg = self.avdmanager.recv_message()
        sign_dict = json.loads(ansmsg)

        result = self.jdcomapi.get_order_detail(sign_dict.get('sign'), body)

        busdata = {}
        busdata = result.get('busiData')
        return busdata.get('orderInfo', ''), result

    def fetch_order_detail(self):
        """
        获取订单详细信息
        :return:
        """
        self.log.info('【商品订单详情】')

        if not self.create_table('TBL_PRCD_JDCOM_ORDER_DETAIL', True):
            self.log.error("create table failed. tablename: 'TBL_PRCD_JDCOM_ORDER_DETAIL'. ")
            return

        for order in self.order_list:
            sql_list = []
            one_order = {}
            order_id = order.get('orderId', '')
            if not order_id:
                self.log.error("No key 'orderId'.")
                continue

            try:
                one_order, order_info = self.order_detail(order_id)
            except Exception as e:
                self.log.exception("fetch order detail error. orderId:{}, error info:{}".format(order_id, e))
                self.request_exception_count += 1
                continue

            try:
                sql = self.parse_order_detail(one_order)
                self.sql_execute_try(sql)
            except Exception as e:
                self.log.exception("An exception occurs when inserted order info:{}".format(e))

            try:
                sql_list = self.parse_goods_detail(order_info)
            except Exception as e:
                self.log.exception("fetch goods detail error. error info:{}".format(e))

            for isql in sql_list:
                self.sql_execute_try(isql)
            self.progress.update(80, '正在获取')
        return True

    def parse_order_detail(self, order):
        """
        解析订单详细信息
        :return:
        """
        order_id = order.get('orderId', '')
        order_status = order.get('orderStatus', '')
        submit_time = order.get('dataSubmit', '')
        order_price = order.get('price', '')
        payment_type = order.get('paymentType', '')
        shop_name = order.get('shopName', '')
        carrier = order.get('carrier', '')
        discount = order.get('discount', '')
        address = self.decrypt_des(order.get('address', ''))
        customer = self.decrypt_des(order.get('customerName', ''))
        invoice_type = order.get('invoiceType', '')
        invoice_title = order.get('invoiceTitle','')
        invoice_url = order.get('invaoiceDownloadUrl','')
        express_fee = order.get('totalFee', '')
        pay_time_map = order.get('companyTransferMap','')
        pay_time = ''
        if pay_time_map:
            pay_time = pay_time_map.get('accountList')[0]
        mobile = order.get('mobile', '')
        total_price = order.get('detailPrice','')
        invoice_content = order.get('invoiceContent', '')
        invoice_pdf_name = ''
        invoice_pdf_relpath = ''
        invoice_pdf_abspath = ''
        if invoice_url:
            invoice_pdf_name = self.checkNameValid(order_id + '.pdf')
            invoice_pdf_relpath = '/JingDong/Snapshot/{}'.format(invoice_pdf_name)
            invoice_pdf_abspath = self.root + "\\JingDong\\Snapshot\\"
            self.down.add_task(url=invoice_url, path=invoice_pdf_abspath, name=invoice_pdf_name)

        sql = '''INSERT INTO "TBL_PRCD_JDCOM_ORDER_DETAIL" ("strOrderId", "strOrderStatus", "strDataSubmit", 
                "strPrice", "strExpressFee", "strDiscount", "strShouldPay", "strPaymentType", "strPayTime",
                "strShopName","strCustomerName","strMobile", "strAddress", "strCarrier", "strInvoiceType",
                "strInvoiceTitle","strInvoiceContent", "strInvoiceSnapshot", "strSrcAccount") VALUES({}, {},
                 {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
              '''

        params = (order_id, order_status, submit_time, order_price, express_fee, discount, total_price, payment_type,
                  pay_time, shop_name, customer, mobile, address, carrier, invoice_type, invoice_title, invoice_content,
                  invoice_pdf_relpath, self.jdcomapi.account)

        return tool.sql_format(sql, params)


    def parse_goods_info(self, order):
        """
        解析商品信息
        :param goods: order
        :return:
        """
        sql_list = []

        order_id = order.get('orderId', '')
        submit_time = order.get('dataSubmit', '')
        goods_list = order.get('orderMsg').get('wareInfoList')
        for goods in goods_list:
            goods_id = goods.get('wareId', '')
            goods_name = goods.get('wname', '')
            goods_desc = goods.get('adword', '')
            bug_count = goods.get('buyCount', '')
            goods_img_url = goods.get('imageurl', '')
            goods_img_name = self.checkNameValid(goods_name + '.jpg.webp')
            goods_img_relpath = '/JingDong/{}'.format(goods_img_name + '.png')
            goods_img_abspath = self.root + "\\JingDong"

            goods_page_url = "https://item.jd.com/{}.html".format(goods_id)

            sql = '''INSERT INTO "TBL_PRCD_JDCOM_GOODS_INFO" ("strOrderId", "strDate", "strGoodsId", "strGoodsName", 
                     "strGoodsDesc", "strNumber", "strGoodSnapshot", "strGoodsImgURL", "strSrcAccount") 
                     VALUES({}, {}, {}, {}, {}, {}, {}, {}, {})'''

            self.down.add_task( url=goods_img_url, path=goods_img_abspath, name=goods_img_name)
            params = (order_id, submit_time,goods_id, goods_name, goods_desc, bug_count, goods_img_relpath,
                      goods_page_url, self.jdcomapi.account)

            sql_list.append(tool.sql_format(sql, params))
        return sql_list


    def parse_goods_detail(self, order_info):
        """
        解析商品信息
        :param goods: order
        :return:
        """
        sql_list = []
        goods_list = []
        order_id = order_info['busiData']['orderInfo']['orderId']
        # submit_time = order_info.get('dataSubmit', '')
        submit_time = order_info['busiData']['orderInfo']['dataSubmit']
        goods_list = order_info.get('busiData').get('wareInfoList')
        for goods in goods_list:
            goods_id = goods.get('wareId', '')
            goods_name = goods.get('wname', '')
            goods_desc = goods.get('adword', '')
            bug_count = goods.get('buyCount', '')
            jdprice = goods.get('jdPrice', '')
            new_price = goods.get('jdPriceNew', '')
            goods_img_url = goods.get('imageurl', '')
            goods_img_name = self.checkNameValid(goods_name + '.jpg.webp')
            goods_img_relpath = '/JingDong/{}'.format(goods_img_name + '.png')
            goods_img_abspath = self.root + "\\JingDong"
            goods_page_url = "https://item.jd.com/{}.html".format(goods_id)

            sql = '''
            INSERT INTO "TBL_PRCD_JDCOM_GOODS_INFO" ("strOrderId", "strSubmitDate", "strGoodsId", "strGoodsName",
            "strGoodsDesc", "strPrice", "strNewPrice","strNumber", "strGoodSnapshot", "strGoodsImgURL", "strSrcAccount") 
            VALUES({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
            '''

            self.down.add_task( url=goods_img_url, path=goods_img_abspath, name=goods_img_name)
            params = (order_id, submit_time, goods_id, goods_name, goods_desc, jdprice, new_price, bug_count, goods_img_relpath,
                      goods_page_url, self.jdcomapi.account)

            sql_list.append(tool.sql_format(sql, params))
        return sql_list

    # def create_tablecreate_table(self, tablename):
    #     if self._conn.tableExists(tablename):
    #         self.log.info('table {} already exists'.format(tablename))
    #     else:
    #         return self.sql_execute_try(config.SQL_CREATETABLE.get(tablename))
    #     return True

    def create_table(self, tablename, drop_if_exist=False):
        if self._conn.tableExists(tablename):
            self.log.info('table {} already exists'.format(tablename))
            if drop_if_exist:
                self.log.info('drop table:{}.'.format(tablename))
                self.sql_execute_try('DELETE FROM {}'.format(tablename))
        else:
            return self.sql_execute_try(config.SQL_CREATETABLE.get(tablename, ''))
        return True

    def sql_execute_try(self, sql):
        first = True
        while True:
            try:
                self._conn.execute(sql)
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

    def checkNameValid(self, name=None):
        if name is None:
            return
        reg = re.compile(r'[///:*?"<>|/r/n]+')
        valid_name = reg.findall(name)
        if valid_name:
            for nv in valid_name:
                name = name.replace(nv, "_")
        return name

    def decrypt_des(self, encrypt_data):
        """
        DES/ECB/PKCS5Padding 解密
        :return:
        """
        ret = ''
        try:
            data = base64.b64decode(encrypt_data)
            k = triple_des("123456781234567812345678", ECB, "\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
            k.setKey('np!u5chin@adm!n1aaaaaaa2')
            ret = k.decrypt(data)
        except:
            return
        return ret.decode()

    def sql_select(self, sql):
        try:
            oSmt = pyMyDatabase.SQLiteStatement(self._conn, sql)
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


    # def sql_execute_try(self, sql):
    #    first = True
    #    while True:
    #        try:
    #            self._conn.execute(sql)
    #        except Exception as e:
    #            if first:
    #                time.sleep(1)
    #                first = False
    #                continue
    #            else:
    #                self.log.exception('sql_execute error! errorinfo:%s\r\nsql:%s' % (e, sql), exc_info=e)
    #        break



