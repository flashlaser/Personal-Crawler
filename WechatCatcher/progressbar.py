# -*- coding: utf-8 -*-

# @Function : 对对应的应用进行进度写入和描述写入
# @Time     : 2017/10/9
# @Author   : LiPb
# @File     : progressbar.py
# @Company  : Meiya Pico

import sys
import pathlib
sys.path.append(pathlib.Path(sys.argv[0]).parent.parent.__str__())
import pyMyDatabase

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
    "Description"
    ) VALUES
    ("{}", "{}", 0, NULL);
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
        if not self._conn.tableExists('TBL_PRCD_APP_CATCHEPROGRESS_INFO'):
            self.excute_sql(TBCREATE_SQL)
        sql = '''
                SELECT * FROM TBL_PRCD_APP_CATCHEPROGRESS_INFO WHERE AppName == '{}' AND LoginAccount='{}'
                '''.format(self.app_name, self.login_account)
        oSmt = pyMyDatabase.SQLiteStatement(self._conn, sql)
        if not oSmt.executeStep():
            sql = TBINSERT_SQL.format(self.app_name, self.login_account)
            self.excute_sql(sql)

    def excute_sql(self, sql):
        self._conn.execute(sql)

    def update(self, percent, desc="", remarks='1'):
        sql = '''
                SELECT Percent FROM TBL_PRCD_APP_CATCHEPROGRESS_INFO WHERE AppName = '{}' AND LoginAccount = '{}' 
                '''.format(self.app_name, self.login_account)
        oSmt = pyMyDatabase.SQLiteStatement(self._conn, sql)
        if oSmt.executeStep():
            # 避免进度回退
            percent_old = oSmt.getColumn(0)
            percent_old = int(float(percent_old.getText(""))) if not percent_old.isNull() else 0
            # percent_old = int(percent_old.getText("")) if not percent_old.isNull() else 0
            if percent < percent_old:
                percent = percent_old
            sql = '''
                    UPDATE TBL_PRCD_APP_CATCHEPROGRESS_INFO SET Percent = {}, Description = '{}', Remarks = '{}'
                    WHERE AppName = '{}' AND LoginAccount = '{}'
                    '''.format(percent, desc, remarks, self.app_name, self.login_account)
            self.excute_sql(sql)


class UnknownProgress(object):
    """
    封装一个算法类，计算在未知总数情况下的当前进度
    """

    def __init__(self, total_range, threshold):
        """
        初始化范围与阈值
        :param total_range: 该段进度范围
        :param threshold: 每更新一半进度的阈值
        """
        self.total_range = total_range
        self.threshold = threshold
        self.first_calc = True
        self.base_info_error = False

    def calc_cur_progress(self, cur_cnt):
        """
        计算当前的进度
        :param cur_cnt: 已经获取的条数
        :return: 进度
        """
        if self.first_calc:
            self.first_calc = False
            if self.threshold <= 0 or self.total_range <= 0:
                self.base_info_error = True

        if self.base_info_error or cur_cnt <= 0:
            return 0

        # 先计算剩余的进度总数
        pow_num = cur_cnt // self.threshold
        left_range = self.total_range / (2 ** pow_num)

        # 已走过的进度
        base_range = self.total_range - left_range

        # 将剩余进度除以二，得出本次的进度范围
        cur_range = left_range / 2

        # 计算当前的值所对应的进度
        cur_num = cur_cnt - pow_num * self.threshold
        cur_progress = cur_num / self.threshold * cur_range

        result = int(cur_progress + base_range)
        return result