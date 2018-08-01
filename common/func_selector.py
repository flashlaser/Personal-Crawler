# -*- coding: utf-8 -*-

# @Function : 函数选择器
# @Time     : 2017/11/9
# @Author   : LiPb (Mocha Lee)
# @File     : func_selector.py
# @Company  : Meiya Pico

import sys
import pathlib
sys.path.append(pathlib.Path(sys.argv[0]).parent.parent.__str__())
import pyMyDatabase


class FuncSelector(object):
    def __init__(self, sqlite_path, app_name, account):
        self.app_name = app_name
        self.account = account
        self._conn = pyMyDatabase.SQLiteDatabase(sqlite_path, True)

    def __del__(self):
        self._conn.close()

    def get(self):
        if not self._conn.tableExists('TBL_PRCD_APP_SELECTION_INFO'):
            return None
        sql = '''
            SELECT ParamList FROM TBL_PRCD_APP_SELECTION_INFO WHERE AppName = '{}' and LoginAccount = '{}' LIMIT 1
            '''.format(self.app_name, self.account)
        oSmt = pyMyDatabase.SQLiteStatement(self._conn, sql)
        if oSmt.executeStep():
            paramlist = oSmt.getColumn(0)
            return paramlist.getText("") if not paramlist.isNull() else None
        return None
