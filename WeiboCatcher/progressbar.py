# -*- coding: utf-8 -*-

# @Function : 对对应的应用进行进度写入和描述写入
# @Time     : 2017/10/9
# @Author   : LiPb
# @File     : progressbar.py
# @Company  : Meiya Pico

import sys
import pathlib
from WeiboCatcher.config import log,FIRST_FORENSIC_FLAG
sys.path.append(pathlib.Path(sys.argv[0]).parent.parent.__str__())
import pyMyDatabase


# global FIRST_FORENSIC_FLAG = True
# FIRST_FORENSIC_FLAG = True

TBCREATE_SQL = '''
    CREATE TABLE "TBL_PRCD_APP_CATCHEPROGRESS_INFO" (
    "Id"  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "ModifyTime"  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    "AppName"  TEXT,
    "LoginAccount"  TEXT,
    "Percent"  INTEGER,
    "Description"  TEXT,
    "Remarks"  TEXT
    );
    '''

TBINSERT_SQL = '''
    INSERT INTO "TBL_PRCD_APP_CATCHEPROGRESS_INFO" (
    "AppName",
    "LoginAccount",
    "Percent",
    "Description",
    "Remarks"
    ) VALUES
    ("{}", "{}", 0, NULL, "{}");
    '''


class ProcessBar(object):
    """
    进度刷新类，用于控制进度刷新和描述信息展示
    """

    def __init__(self, sqlite_path, app_name, login_account):
        """
        初始化函数
        :param sqlite_path: sqlite数据库路径
        :param app_name: 应用名称
        """
        self.app_name = app_name
        self.login_account = login_account
        self._conn = pyMyDatabase.SQLiteDatabase(sqlite_path, True)
        self.__init_progress()

    def __init_progress(self):
        """
        初始化进度
        :return:
        """
        global FIRST_FORENSIC_FLAG
        if FIRST_FORENSIC_FLAG:
            if self._conn.tableExists('TBL_PRCD_APP_CATCHEPROGRESS_INFO'):
                self.sql_execute_try('DELETE FROM {}'.format('TBL_PRCD_APP_CATCHEPROGRESS_INFO'))
            self.sql_execute_try(TBCREATE_SQL)
            FIRST_FORENSIC_FLAG = False
        else:
            if not self._conn.tableExists('TBL_PRCD_APP_CATCHEPROGRESS_INFO'):
                self.sql_execute_try(TBCREATE_SQL)

        sql = '''
                SELECT * FROM TBL_PRCD_APP_CATCHEPROGRESS_INFO WHERE AppName == '{}' AND LoginAccount='{}'
                '''.format(self.app_name, self.login_account)
        oSmt = pyMyDatabase.SQLiteStatement(self._conn, sql)
        if not oSmt.executeStep():
            sql = TBINSERT_SQL.format(self.app_name, self.login_account, '1')
            self.sql_execute_try(sql)

    def update(self, percent, desc="", finish='1'):
        sql = '''
                SELECT Percent FROM TBL_PRCD_APP_CATCHEPROGRESS_INFO WHERE AppName = '{}' AND LoginAccount = '{}' 
                '''.format(self.app_name, self.login_account)
        oSmt = pyMyDatabase.SQLiteStatement(self._conn, sql)
        if oSmt.executeStep():
            # 避免进度回退
            percent_old = oSmt.getColumn(0)
            percent_old = int(float(percent_old.getText(""))) if not percent_old.isNull() else 0
            if percent < percent_old:
                percent = percent_old
            sql = '''
                    UPDATE TBL_PRCD_APP_CATCHEPROGRESS_INFO SET Percent = {}, Description = '{}', Remarks = '{}'
                    WHERE AppName = '{}' AND LoginAccount = '{}'
                    '''.format(percent, desc, finish, self.app_name, self.login_account)
            self.sql_execute_try(sql)

    def sql_execute_try(self, sql):
        first = True
        while True:
            try:
                self._conn.execute(sql)
            except Exception as e:
                if first:
                    first = False
                    continue
                else:
                    log.exception('sql_execute error! errorinfo:%s\r\nsql:%s' % (e, sql), exc_info=e)
                    return False
            break
        return True
