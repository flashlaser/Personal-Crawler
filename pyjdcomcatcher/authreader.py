# -*- coding: utf-8 -*-

# @Function : 文件用于读取数据库中的授权信息，包括token、密码等
# @Time     : 2017/9/30
# @Author   : LiPb
# @File     : authreader.py
# @Company  : Meiya Pico

import sys
from pyjdmallcatcher.config import BIN64_PATH
sys.path.append(BIN64_PATH)
import pyMyDatabase


class AuthReader(object):
    """
    從數據庫中讀取登錄需要的信息
    """
    def __init__(self, sqlite_path, app_name, table_name, log):
        self.app_name = app_name
        self.table_name = table_name
        self.log = log
        self._conn = pyMyDatabase.SQLiteDatabase(sqlite_path, True)

    def select(self):
        info_list = []
        if not self._conn.tableExists(self.table_name):
            self.log.info('table {} is not exist'.format(self.table_name))
            return info_list
        sql = '''
        SELECT LoginAccount,AuthToken,AuthLogin FROM {} WHERE AppName == '{}' and Other == '1'
        '''.format(self.table_name, self.app_name)

        oSmt = pyMyDatabase.SQLiteStatement(self._conn, sql)
        while oSmt.executeStep():
            login_account = self._get_column_value(oSmt.getColumn(0))
            auth_token = self._get_column_value(oSmt.getColumn(1))
            auth_login = self._get_column_value(oSmt.getColumn(2))
            info_list.append((login_account, auth_token, auth_login))
        return info_list
    
    @staticmethod
    def _get_column_value(column_object):
        if not isinstance(column_object, pyMyDatabase.SQLiteColumn):
            return None
        return column_object.getText("") if not column_object.isNull() else ''


    def update(self, account, logininfo):
        """
            更新用户等登录信息
        """
        sql = "SELECT LoginAccount FROM TBL_PR_APP_AUTHINFO WHERE AppName == '{}'" .format(self.app_name)

        account_list = []
        login_account = ''
        oSmt = pyMyDatabase.SQLiteStatement(self._conn, sql)
        while oSmt.executeStep():
            login_account = oSmt.getColumn(0)

            if not login_account.isNull():
                login = login_account.getText("").strip()
                account_list.append(login)

        if not account_list:
            sql = '''
                INSERT INTO "TBL_PR_APP_AUTHINFO" (AppName, LoginAccount, AuthLogin) VALUES ('{}', '{}', '{}')
            '''.format(self.app_name, account, logininfo)
            self._conn.execute(sql)

        update_sql = '''
                    UPDATE "TBL_PR_APP_AUTHINFO" SET AuthLogin = '{}' WHERE AppName = '{}' AND LoginAccount = '{}'
                '''.format(logininfo, self.app_name, account)
        self._conn.execute(update_sql)

