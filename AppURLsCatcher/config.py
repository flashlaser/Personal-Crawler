import os
import sys
import pathlib
import configparser
from AppURLsCatcher.logger import Logger

APP_NAME = 'AppURLs'
log = Logger('AppURLs.log')

BIN64_PATH = pathlib.Path(sys.argv[0]).parent.parent.__str__()
APP_FILTER_PATH = BIN64_PATH + '\\Config\\AppCloudFilter.db'
WEBDRIVE_PATH = '{}/Tool/webdriver/{}'.format(pathlib.Path(sys.argv[0]).parent.parent.__str__(), 'chromedriver.exe')
CHROME_PATH = '{}/3rdParty/Chrome/chrome.exe'.format(pathlib.Path(sys.argv[0]).parent.parent.parent.parent.__str__())
TEMP_PATH = pathlib.Path(sys.argv[0]).parent.__str__() + '/appurls_temp'
APPS_AMF_PATH = 'Apps.amf'

FIRST_FORENSIC_FLAG = True

TBINSERT_SQL = '''
    INSERT INTO "TBL_PRCD_APP_CATCHEPROGRESS_INFO" (
    "AppName",
    "LoginAccount",
    "Percent",
    "Description"
    ) VALUES
    ("{}", "{}", 0, "等待开始");
    '''

TBCREATE_SQL = {
'TBL_PRCD_URL_EXCEPTIONS_INFO':
        '''
        CREATE TABLE "TBL_PRCD_URL_EXCEPTIONS_INFO" (
        "Id"  INTEGER NOT NULL,
        "ModifyTime"   TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        "URL"          TEXT,
        "AppName"      TEXT,
        "FileType"     TEXT,
        "Exceptions"   TEXT,
        "Description"  TEXT,
        "Remarks"      TEXT,
        PRIMARY KEY ("id" ASC)
        );
        ''',
'TBL_PRCD_URL_FILE_INFO':
        '''
        CREATE TABLE "TBL_PRCD_URL_FILE_INFO" (
        "Id"  INTEGER NOT NULL,
        "ModifyTime"   TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        "URL"           TEXT,
        "LocalPath"     TEXT,     -- 本地存储路径
        "AppName"       TEXT,     -- URL的APP名称
        "FileName"      TEXT,     -- 文件名称
        "FileType"      TEXT,     -- 文件类型
        "Remarks"       TEXT,
        PRIMARY KEY ("id" ASC)
        );
        ''',
'TBL_PRCD_APP_CATCHEPROGRESS_INFO':
    '''
    CREATE TABLE "TBL_PRCD_APP_CATCHEPROGRESS_INFO" (
    "Id"  INTEGER NOT NULL,
    "ModifyTime"  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    "AppName"  TEXT,
    "LoginAccount"  TEXT, 
    "Percent"  INTEGER,
    "Description"  TEXT,
    "Remarks"  TEXT,
    PRIMARY KEY ("id" ASC)
    );
    '''
}

# SQL_CATCHER_EXCEPT = '''
#               INSERT INTO "TBL_PRCD_URL_EXCEPTIONS_INFO" ("AppName", "URL", "Exceptions", "Description") VALUES ({}, {}, {}, {})
#             '''
#
# SQL_CATCHER_NORMAL = '''
#               INSERT INTO "TBL_PRCD_URL_FILE_INFO" ("AppName", "URL", "FileName", "LocalPath", "FileType") VALUES ({}, {}, {}, {}, {})
# '''

SQL_CATCHER_EXCEPT = '''
              INSERT INTO "TBL_PRCD_URL_EXCEPTIONS_INFO" ("AppName", "URL", "Exceptions", "Description")
                      VALUES
              ("{}", "{}", "{}", "{}") 
            '''

SQL_CATCHER_NORMAL = '''
              INSERT INTO "TBL_PRCD_URL_FILE_INFO" ("AppName", "URL", "FileName", "LocalPath", "FileType") 
                      VALUES 
              ("{}","{}","{}", "{}", "{}")
              '''

SQL_PROGRESS_INSERT = '''
    INSERT INTO "TBL_PRCD_APP_CATCHEPROGRESS_INFO" (
	"AppName",
	"Percent",
	"Description"
    ) VALUES
    ("{}", 0, NULL);
    '''

SQL_PROGRESS_UPDATE = "UPDATE TBL_PRCD_APP_CATCHEPROGRESS_INFO SET LoginAccount = {}, Percent = {}, Description = '{}' WHERE AppName = 'AppURLs'"


class AppURLsConf(object):
    def __init__(self):
        self.headless = False
        self.concurnum = 3
        self.screenshot = True
        self._init_conf()

    def _init_conf(self):
        conf = MyConfig()
        self.headless = conf.get_headless()
        self.chrome_max = conf.get_concurrent()
        self.screenshot = conf.get_screenshot()


class MyConfig(configparser.ConfigParser):
    def __init__(self):
        super(MyConfig, self).__init__()
        self.config_file = TEMP_PATH + '/appurls_config.ini'
        self.SECTION_NAME = 'AppURLs'

    def _get_value(self, option):
        try:
            if not os.path.exists(self.config_file):
                self._write_default()
                return True

            if not self._read_config():
                return True

            if not self.has_option(self.SECTION_NAME, option):
                self._write_default()
                return True

            value = self.get(self.SECTION_NAME, option)
            if value == '1':
                return True
            else:
                return False
        except Exception as e:
            return True

    def _get_value_int(self, option):
        try:
            if not os.path.exists(self.config_file):
                self._write_default()
                return True

            if not self._read_config():
                return True

            if not self.has_option(self.SECTION_NAME, option):
                self._write_default()
                return True

            value = self.get(self.SECTION_NAME, option)
            return int(value)
        except Exception as e:
            return 5

    def get_headless(self):
        return self._get_value('headless')

    def get_maxsize(self):
        return self._get_value('maxsize')

    def get_concurrent(self):
        return self._get_value_int('concurrent')

    def get_screenshot(self):
        return self._get_value('screenshot')


    def _write_default(self):
        if not os.path.exists(TEMP_PATH):
            os.makedirs(TEMP_PATH)
        file = open(self.config_file, 'w', encoding='utf-8')
        if not file:
            return
        if not self.has_section(self.SECTION_NAME):
            self.add_section(self.SECTION_NAME)
        self.set(self.SECTION_NAME, 'headless', '1')
        self.set(self.SECTION_NAME, 'concurrent', '5')
        self.write(file)
        file.close()

    def _read_config(self):
        if not self.read(self.config_file, encoding='utf-8'):
            return False
        return True