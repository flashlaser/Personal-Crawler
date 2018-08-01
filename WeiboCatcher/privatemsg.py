# -*- coding: utf-8 -*-


import six
import socket
import gzip
import time
import json
from WeiboCatcher.config import log


class PrivateMsgRequest:
    def __init__(self):
        self.tidTag = 0
        # self.tid = 1531357833004
        self.tid = int(time.time() * 1000) #这个时间戳随便一个毫秒级的就可以
        self.gdidTag = 2
        self.gdid = '826e0492fe11efd1f355'.encode()  #本地/data/data/com.sina.weibo/shared_prefs/sina_push_pref.xml中name=key.gwid，换了一个发现没有问题
        self.gsidTag = 3
        self.gsid = '_2A252QQr888RxGeBN41UV-C7JyD2IHXVTVxk0rDV6PUJbkdAKLRX2kWpNRBobhTa2bolXqLLQvsqcsGIm4DsIKp-j'.encode() #之前取过，可以获取,换了好几个发现都可以用
        self.access_tokenTag = 4
        self.access_token = ''  #每个账号一个，/data/data/com.sina.weibo/databases/sina_weibo/
        self.typeTag = 5
        self.type = 5
        self.protoTag = 6
        self.proto = 35
        self.flagTag = 9
        self.flag = 0
        self.captcha_infoTag = 11
        self.captcha_info = "null"
        self.optionsTag = 14
        self.options = "null"
        self.auxiliariesTag = 15
        self.requestIdTag = 21
        self.requestId = "a0bc83f6-d553-4723-94c4-18e3ca05f374"  #随意
        self.traceidTag = 24
        self.traceid = "-7906411804155011080"  #随意
        self.idTag = 25
        self.id = "-7906411814164011080"  #随意
        self.parentidTag = 26
        self.parentid = ""
        self.isSampledTag = 27
        self.isSampled = "false"
        self.accecpt_content_typesTag = 0
        self.accecpt_content_types = [1, ]
        self.languageTag = 8
        self.language = 0
        self.platformTag = 9
        self.platform = 0
        self.user_agentTag = 10
        self.user_agent = "Xiaomi-MI 3W__weibo__8.7.0__android__android6.0.1"
        self.frommTag = 11
        self.fromm = "1087095010"
        self.wmTag = 12
        self.wm = "20005_0002"
        self.vpTag = 13
        self.vp = 62    #随意多少
        self.bArr = b''
        self.UIDTag = 0
        self.UID = 0
        self.max_midTag = 1
        self.max_mid = 0
        self.countTag = 2
        self.count = 20
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def get_private_msg(self, user, msg, access_token):
        if not isinstance(user, dict):
            return False
        
        if user.get('profile_url') is None or user.get('id') is None:
            return False
        
        id_str = 'u/' + user.get('idstr')
        profile_url = user.get('profile_url')
        if id_str != profile_url:
            return False
        
        # connect server
        if not self.connect_server():
            log.info('connect socket server failed')
            return False
        
        self.UID = user.get('id')
        self.max_mid = 0
        self.type = 5
        self.proto = 35
        self.max_midTag = 2
        self.countTag = 3
        self.access_token = access_token.encode()
        while True:
            self.bArr = b''
            self.compose_request_data()
            re = self.request_data()
            if len(re) > 38:
                re = re[38:]
            else:
                break
            index = re.find(b'\x1f\x8b')
            if index != -1:
                re = re[index:]
                re = gzip.decompress(re)
            
            try:
                re = re.decode()
                re = json.loads(re)
            except json.JSONDecodeError:
                break
            messages = re.get('messages')
            if messages is None or len(messages) == 0:
                break
            else:
                msg.extend(messages)
                self.max_mid = messages[-1].get('mid')
        return True
        
    def get_group_msg(self, msg_id, msg, access_token):
        if not isinstance(msg_id, int):
            return False
        
        # connect server
        if not self.connect_server():
            log.info('connect socket server failed')
            return False
        
        self.UID = msg_id
        self.max_mid = 0
        self.type = 6
        self.proto = 34
        self.max_midTag = 1
        self.countTag = 2
        self.access_token = access_token.encode()

        while True:
            self.bArr = b''
            self.compose_request_data()
            re = self.request_data()
            if len(re) > 38:
                re = re[38:]
            else:
                break
            index = re.find(b'\x1f\x8b')
            if index != -1:
                re = re[index:]
                re = gzip.decompress(re)
            
            try:
                re = re.decode()
                re = json.loads(re)
            except json.JSONDecodeError:
                break
            messages = re.get('messages')
            if messages is None or len(messages) == 0:
                break
            else:
                msg.extend(messages)
                self.max_mid = messages[0].get('mid')
        return True
    
    def connect_server(self):
        try:
            host = socket.gethostbyname('api.im.weibo.cn')
            address = (host, 8080)
        except Exception:
            address = ('api.im.weibo.cn', 8080)
            
        cnt = 1
        while cnt < 3:
            connect_ret = self.soc.connect_ex(address)
            if connect_ret == 0 or connect_ret == 10056:
                return True
            else:
                cnt += 1
                time.sleep(1)
        else:
            return False
           
    def close_server(self):
        self.soc.close()
    
    def request_data(self):
        try:
            self.soc.send(self.bArr)
            r = self.soc.recv(102400)
            return r
        except Exception as e:
            log.exception('get private msg error', exc_info=e)
            return ''
        
    def compose_request_data(self):
        header_size = self.get_header_size()
        body_size = self.computeSize_body()
        total_size = self.computeInt32SizeNoTag(header_size) + header_size + self.computeInt32SizeNoTag(body_size) + body_size
        self.writeFixed32NoTag(total_size)
        self.writeInt32NoTag(header_size)
        self.writestr()
        self.writeInt32NoTag(body_size)
        self.writeRequestId(self.UIDTag, self.UID)
        self.writeMax_mid(self.max_midTag, self.max_mid)
        self.writecount(self.countTag, self.count)

    def get_header_size(self):
        TidSize = self.computeSize_E(self.tidTag, self.tid)
        GdidSize = self.computeSize_B(self.gdidTag, self.gdid)
        GsidSize = self.computeSize_B(self.gsidTag, self.gsid)
        Access_Token = self.computeSize_B(self.access_tokenTag, self.access_token)
        Type = self.computeSize_D(self.typeTag, self.type)
        Proto = self.computeSize_D(self.protoTag, self.proto)
        flag = self.computeSize_D1(self.flagTag, self.flag)
        Captcha_info = self.computeSize_F(self.captcha_infoTag, self.captcha_info)
        Options = self.computeSize_F(self.optionsTag, self.options)
        RequestId = self.computeSize_F(self.requestIdTag, self.requestId)
        Traceid = self.computeSize_F(self.traceidTag, self.traceid)
        Id = self.computeSize_F(self.idTag, self.id)
        Parentid = self.computeSize_F(self.parentidTag, self.parentid)
        IsSampled = self.computeSize_F(self.isSampledTag, self.isSampled)
        auxiliaries = self.computeTagSize(self.auxiliariesTag)

        totalSize = TidSize + GdidSize + GsidSize + Access_Token + \
                    Type + Proto + flag + Captcha_info + Options + \
                    RequestId + Traceid + Id + Parentid + IsSampled + \
                    auxiliaries

        Accecpt_content_types = self.computeSize_C(self.accecpt_content_typesTag, self.accecpt_content_types)
        Language = self.computeSize_D(self.languageTag, self.language)
        Platform = self.computeSize_D(self.platformTag, self.platform)
        User_agent = self.computeSize_F(self.user_agentTag, self.user_agent)
        Fromm = self.computeSize_F(self.frommTag, self.fromm)
        WM = self.computeSize_F(self.wmTag, self.wm)
        VP = self.computeSize_D(self.vpTag, self.vp)
        self.len = Accecpt_content_types + Language + Platform + User_agent + Fromm + WM + VP
        return totalSize + self.computeInt32SizeNoTag(self.len) + self.len

    def computeSize_E(self, Tag, value):
        return self.computeInt64Size(Tag, value)

    def computeSize_B(self, Tag, value):
        return self.computeByteArraySize(Tag, value)

    def computeSize_C(self, Tag, value):
        return self.computeInt32ArraySize(Tag, value)

    def computeSize_D(self, Tag, value):
        return self.computeInt32Size(Tag, value)

    def computeSize_D1(self, Tag, value):
        return 0

    def computeSize_F(self, Tag, value):
        if value == "null":
            return 0
        else:
            return self.computeStringSize(Tag, value)

    def computeSize_body(self):
        UIDlen = self.computeInt64Size(self.UIDTag, self.UID)
        max_idlen = self.computeInt64Size(self.max_midTag, self.max_mid)
        countlen = self.computeInt32Size(self.countTag, self.count)
        # sendtypelen = self.computeInt32Size(self.sendtypeTag, self.sendtype)
        return UIDlen + max_idlen +countlen

    def computeInt32Size(self, Tag, value):
        return self.computeTagSize(Tag) + self.computeInt32SizeNoTag(value)

    def computeInt64Size(self, Tag, Value):
        return self.computeTagSize(Tag) + self.computeInt64SizeNoTag(Value)

    def computeByteArraySize(self, Tag, bArr):
        return self.computeTagSize(Tag) + self.computeByteArraySizeNoTag(bArr)

    def computeInt32ArraySize(self, Tag , iArr):
        len = self.computeInt32ArraySizeNoTag(iArr)
        return self.computeTagSize(Tag) + self.computeInt32SizeNoTag(len) + len

    def computeStringSize(self, Tag, str):
        return self.computeTagSize(Tag) + self.computeStringSizeNoTag(str)

    def computeTagSize(self, Tag):
        Tag = self.makeTag(Tag, 0)
        return self.computeRawVarint32Size(Tag)

    def computeInt32SizeNoTag(self, Value):
        return self.computeRawVarint32Size(Value)

    def computeInt64SizeNoTag(self, Value):
        return self.computeRawVarint64Size(Value)

    def computeInt32ArraySizeNoTag(self, iArr):
        totalSize = 0
        for v in iArr:
            totalSize += self.computeRawVarint32Size(v)
        return totalSize + self.computeRawVarint32Size(0)

    def computeByteArraySizeNoTag(self, bArr):
        return self.computeRawVarint32Size(len(bArr)) + len(bArr)

    def computeStringSizeNoTag(self, str):
        return self.computeRawVarint32Size(len(str)) + len(str)

    def computeRawVarint32Size(self, value):
        if (value & -128) == 0:
            return 1
        if (value & -16384) == 0:
            return 2
        if (-2097152 & value) == 0:
            return 3
        if (-268435456 & value) == 0:
            return 4
        else:
            return 5

    def computeRawVarint64Size(self, value):
        if (-128 & value) == 0:
            return 1
        if (-16384 & value) == 0:
            return 2
        if (-2097152 & value) == 0:
            return 3
        if (-268435456 & value) == 0:
            return 4
        if (-34359738368 & value) == 0:
            return 5
        if (-4398046511104 & value) == 0:
            return 6
        if (-562949953421312 & value) == 0:
            return 7
        if (-72057594037927936 & value) == 0:
            return 8
        if (-9223372036854775808 & value) == 0:
            return 9
        else:
            return 10

    def makeTag(self, fieldNumber, wireType):
        return (fieldNumber << 3) | wireType

    def writeFixed32NoTag(self, i):
        self.writeRawLittleEndian32(i)

    def writeRawLittleEndian32(self, i):
        self.writeRawByte(six.int2byte(i & 255))
        self.writeRawByte(six.int2byte((i >> 8) & 255))
        self.writeRawByte(six.int2byte((i >> 16) & 255))
        self.writeRawByte(six.int2byte((i >> 24) & 255))

    def writeRawByte(self, byte):
        self.bArr += byte

    def writeRawVarint32(self, i):
        while (i & -128) != 0:
            self.writeRawByte(six.int2byte((i & 127) | 128))
            i >>= 7
        self.writeRawByte(six.int2byte(i))

    def writeRawVarint64(self, value):
        while (-128 & value) != 0:
            self.writeRawByte((value & 127) | 128)
            value >>= 7
        self.writeRawByte(value)

    def writeInt32NoTag(self, i):
        self.writeRawVarint32(i)

    def writeInt32(self, tag, value):
        self.writeTag(tag, 0)
        self.writeInt32NoTag(value)

    def writeInt64(self, tag , value):
        self.writeTag(tag, 0)
        self.writeInt64NoTag(value)

    def writeInt32Array(self, tag, value):
        self.writeTag(tag, 3)
        self.writeInt32ArrayNoTag(value)

    def writeByteArray(self, tag, bArr):
        self.writeTag(tag, 1)
        self.writeByteArrayNoTag(bArr)

    def writeString(self, tag, value):
        self.writeTag(tag, 1)
        self.writeStringNoTag(value)

    def writeInt64NoTag(self, value):
        if value >= 0:
            self.writeRawVarint32(value)
        else:
            self.writeRawVarint64(value)

    def writeInt32ArrayNoTag(self, iArr):
        i = 0
        self.writeRawVarint32(self.computeInt32ArraySizeNoTag(iArr))
        self.writeInt32NoTag(0)
        length = len(iArr)
        while i < length:
            self.writeInt32NoTag(iArr[i])
            i += 1

    def writeByteArrayNoTag(self, bArr):
        self.writeRawVarint32(len(bArr))
        self.writeRawByte(bArr)

    def writeStringNoTag(self, str):
        byte = bytes(str, encoding = "utf8")
        self.writeRawVarint32(len(byte))
        self.writeRawByte(byte)

    def writeTag(self, tag, fd):
        self.writeRawVarint32(self.makeTag(tag, fd))

    def writestr(self):
        self.write_E(self.tidTag, self.tid)
        self.write_B(self.gdidTag, self.gdid)
        self.write_B(self.gsidTag, self.gsid)
        self.write_B(self.access_tokenTag, self.access_token)
        self.write_D(self.typeTag, self.type)
        self.write_D(self.protoTag, self.proto)
        self.write_D1(self.flagTag, self.flag)
        self.write_F(self.captcha_infoTag, self.captcha_info)
        self.write_F(self.optionsTag, self.options)
        self.writeTag(self.auxiliariesTag, 2)
        self.writeRawVarint32(self.len)
        self.write_C(self.accecpt_content_typesTag, self.accecpt_content_types)
        self.write_D(self.languageTag, self.language)
        self.write_D(self.platformTag, self.platform)
        self.write_F(self.user_agentTag, self.user_agent)
        self.write_F(self.frommTag, self.fromm)
        self.write_F(self.wmTag, self.wm)
        self.write_D(self.vpTag, self.vp)
        self.write_F(self.requestIdTag, self.requestId)
        self.write_F(self.traceidTag, self.traceid)
        self.write_F(self.idTag, self.id)
        self.write_F(self.parentidTag, self.parentid)
        self.write_F(self.isSampledTag, self.isSampled)

    def write_E(self, tag , value):
        self.writeInt64(tag, value)

    def write_B(self, tag, value):
        self.writeByteArray(tag, value)

    def write_C(self, tag, value):
        self.writeInt32Array(tag, value)

    def write_D(self, tag, value):
        self.writeInt32(tag, value)

    def write_D1(self, Tag, value):
        return 0

    def write_F(self, tag, value):
        if value == "null":
            return 0
        else:
            self.writeString(tag, value)

    def writeRequestId(self, tag, value):
        self.writeInt64(tag, value)

    def writeMax_mid(self, tag, value):
        self.writeInt64(tag, value)

    def writecount(self, tag, value):
        self.writeInt32(tag, value)
