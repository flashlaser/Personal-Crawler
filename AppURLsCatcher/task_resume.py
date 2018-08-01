# -*- coding: utf-8 -*-

# @Function : 
# @Time     : 2018/3/26
# @Author   : LiPb (Mocha Lee)
# @File     : task_resume.py
# @Company  : Meiya Pico

import time
import json
import sys, pathlib
sys.path.append(pathlib.Path(sys.argv[0]).parent.parent.__str__())
import pyMyDatabase

SQL_CREATE_STATUSINFO = """CREATE TABLE "TBL_PRCD_APP_CATCHSTATUS_INFO" (
                        "Id"  INTEGER NOT NULL,
                        "ModifyTime"  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                        "Uid"  TEXT NOT NULL,
                        "SubAppName"  TEXT NOT NULL,
                        "Status"  TEXT NOT NULL,
                        "OtherParam"  TEXT,
                        "Remarks"  TEXT,
                        PRIMARY KEY ("Id" ASC)
                        )"""
SQL_CREATE_DOWNLOADINFO = """CREATE TABLE "TBL_PRCD_APP_DOWNLOADINFO" (
                        "Id"  INTEGER NOT NULL,
                        "ModifyTime"  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                        "Uid"  TEXT NOT NULL,
                        "SubAppName"  TEXT NOT NULL,
                        "Gid"  TEXT NOT NULL,
                        "DownloadPath"  TEXT,
                        "OtherParam"  TEXT,
                        "Remarks"  TEXT,
                        PRIMARY KEY ("Id" ASC)
                        )"""


class TaskResume(object):
    """
    任务恢复类，用于支持实现断点续传
    """
    def __init__(self, amf_path, log):
        """
        初始化实例
        :param amf_path: 该应用的amf数据库路径 type: str
        :param subappnames: 所有的子应用名称 type:tuple
        """
        self.pending = {}
        self.log = log
        self._conn = pyMyDatabase.SQLiteDatabase(amf_path, True)
        if not self._conn.tableExists('TBL_PRCD_APP_CATCHSTATUS_INFO'):
            self._sql_execute_try(SQL_CREATE_STATUSINFO)
        if not self._conn.tableExists('TBL_PRCD_APP_DOWNLOADINFO'):
            self._sql_execute_try(SQL_CREATE_DOWNLOADINFO)

    def init_progress(self, uid):
        """
        初始化进度，开始之前，初始化之前已经进行的进度
        :param uid: 用户唯一ID
        :return: 无
        """
        sql = """select SubAppName, Status, OtherParam, Remarks 
            from TBL_PRCD_APP_CATCHSTATUS_INFO where Uid = '{}'
            """.format(uid)
        o_smt = pyMyDatabase.SQLiteStatement(self._conn, sql)
        task_progress = []
        while o_smt.executeStep():
            subappname, status = o_smt.getColumn(0), o_smt.getColumn(1)
            other_param, remarks = o_smt.getColumn(2), o_smt.getColumn(3)
            subappname = subappname.getText("") if not subappname.isNull() else None
            status = status.getText("") if not status.isNull() else None
            other_param = other_param.getText("") if not other_param.isNull() else None
            remarks = remarks.getText("") if not remarks.isNull() else None
            if subappname:
                task_progress.append(
                    {'subappname': subappname, 'status': status, 'remarks': remarks,
                     'other_param': json.loads(other_param) if other_param else []}
                )
        self.pending = {uid: task_progress}

    def update(self, uid, subappname, status, other_param='', remarks=''):
        """
        更新某个子应用的进度状态和备注
        :param uid: 账户唯一ID
        :param subappname: 子应用名
        :param status: 状态（0 该项目未开始, 1 该项目正常完成, 2 该项目取证异常）
        :param other_param: 其他参数
        :param remarks: 备注
        :return: 无
        """
        sql_select = """
            select Status from TBL_PRCD_APP_CATCHSTATUS_INFO where Uid = '{}' and SubAppName = '{}' LIMIT 1 
            """.format(uid, subappname)
        o_smt = pyMyDatabase.SQLiteStatement(self._conn, sql_select)
        if not o_smt.executeStep():
            sql = """
                insert into "TBL_PRCD_APP_CATCHSTATUS_INFO" 
                ("Uid", "SubAppName", "Status", "OtherParam", "Remarks") 
                values ('{}', '{}', '{}', '{}', '{}')
                """.format(uid, subappname, status, other_param, remarks)
        else:
            sql = """
                UPDATE TBL_PRCD_APP_CATCHSTATUS_INFO SET Status = '{}', OtherParam = '{}', Remarks = '{}' 
                WHERE SubAppName = '{}' and Uid = '{}'
                """.format(status, other_param, remarks, subappname, uid)
        self._sql_execute_try(sql)

    def add_downloadinfo(self, uid, subappname, gid, download_path='', other_param='', remarks=''):
        """
        主要针对邮件、文件、照片这类取证项，增加详细的进度参数
        :param uid: 唯一ID
        :param subappname: 子取证项
        :param gid: 下载器返回的唯一id
        :param download_path: 该文件下载对应的本地路径，可选
        :param other_param: 对应该下载的其他相关信息，可选，如果是json需要提前dumps
        :param remarks: 待添加的详细描述
        :return: 无
        """
        sql = """
            INSERT INTO "TBL_PRCD_APP_DOWNLOADINFO" 
            ("Uid", "SubAppName", "Gid", "DownloadPath", "OtherParam", "Remarks")
            values ('{}', '{}', '{}', '{}', '{}', '{}')
            """.format(uid, subappname, gid, download_path, other_param, remarks)
        self._sql_execute_try(sql)

    def get_param_list(self, uid, subappname):
        sql_select = """select OtherParam 
                        from TBL_PRCD_APP_DOWNLOADINFO where Uid = '{}' and SubAppName = '{}'
                        """.format(uid, subappname)
        o_smt = pyMyDatabase.SQLiteStatement(self._conn, sql_select)
        result = []
        while o_smt.executeStep():
            other_param = o_smt.getColumn(0)
            other_param = other_param.getText("") if not other_param.isNull() else None
            result.append(other_param)
        return result

    def get_downloadinfo(self, uid, subappname):
        """
        获取某取证项的others_param
        :param uid: 唯一ID
        :param subappname: 子取证项
        :return: type:list
        """
        sql_select = """
                   select Gid, DownloadPath, OtherParam 
                   from TBL_PRCD_APP_DOWNLOADINFO where Uid = '{}' and SubAppName = '{}'
                   """.format(uid, subappname)
        o_smt = pyMyDatabase.SQLiteStatement(self._conn, sql_select)
        result = []
        while o_smt.executeStep():
            gid, download_path, other_param = o_smt.getColumn(0), o_smt.getColumn(1), o_smt.getColumn(2)
            gid = gid.getText("") if not gid.isNull() else None
            download_path = download_path.getText("") if not download_path.isNull() else None
            other_param = other_param.getText("") if not other_param.isNull() else None
            result.append({'gid': gid, 'download_path': download_path, 'other_param': other_param})
        return result

    def is_done(self, uid, subappname):
        """
        判断某账号的某子应用项是否取证完成
        :param uid: 唯一ID
        :param subappname: 子取证项
        :return: True or False
        """
        status_info = self.pending.get(uid)
        if not status_info:
            return False
        for item in status_info:
            if item.get('subappname') == subappname:
                return True if item.get('status') in [1, '1'] else False
        return False

    # @staticmethod
    # def _left_item(all_subname, task_progress):
    #     """
    #     根据要获取的整体项目和已获取的进度，计算剩余要获取的项目
    #     :param all_subname: 要获取的整体项目
    #     :param task_progress: 已获取的进度
    #     :return: 剩余要获取的项目
    #     """
    #     left_item = []
    #     for item in task_progress:
    #         subappname, status = item.get('subappname'), item.get('status')
    #         if status in [1, '1']:
    #             continue
    #         if subappname not in all_subname and all_subname != '*':
    #             continue
    #         left_item.append(item)
    #     return left_item

    def _sql_execute_try(self, sql):
        """
        sql执行函数，失败会重试一次， select这类有返回的不可在这里执行
        :param sql: sql语句
        :return: 无
        """
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
                    self.log.exception('sql_execute error! errorinfo:%s\r\nsql:%s' % (e.__str__(), sql))
            break
