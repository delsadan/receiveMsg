import sqlite3
import time

from loguru import logger
import os

if not os.path.exists('log'):
    os.mkdir('log')

# logger.remove(handler_id=None)  # 关闭日志终端输出
logger.add('./log/log.txt', rotation="20 MB", encoding='utf-8')


def sql_init():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute("""CREATE TABLE Token
                ( ID INTEGER PRIMARY KEY AUTOINCREMENT,
                get_token_time INTEGER,
                expire_token_time INTEGER,
                token TEXT
                );""")
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()
    finally:
        conn.close()


class SQLOperation:
    def __init__(self):
        self.conn = sqlite3.connect('database.db', check_same_thread=False)

    def __del__(self):
        self.conn.close()
        # logger.info('SQL链接已断开！')

    def init(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE Token
                ( ID INTEGER PRIMARY KEY AUTOINCREMENT,
                get_token_time INTEGER,
                expire_token_time INTEGER,
                token TEXT);""")

        c.execute("""CREATE TABLE Message
                ( ID INTEGER PRIMARY KEY AUTOINCREMENT,
                send_message_time INTEGER,
                message_text TEXT,
                msg_response TEXT);""")
        c.execute("""CREATE TABLE ReceiveMsg
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                receive_time INTEGER,
                msg_mode INTEGER,
                msg_id INTEGER,
                msg_num INTEGER,
                msg_num_index INTEGER,
                msg_time TEXT,
                out_way TEXT,
                alphabet TEXT,
                ud TEXT,
                raw_pdu TEXT);""")
        self.conn.commit()
        logger.success('数据库初始化成功！')

    def insert_token(self, **kwargs):
        c = self.conn.cursor()
        try:
            i = f"INSERT INTO Token (get_token_time, expire_token_time, token) VALUES ({kwargs['get_token_time']},{kwargs['expire_token_time']},{kwargs['token']}) "
            c.execute(i)
            self.conn.commit()
            logger.info('Token数据插入成功')
        except Exception as e:
            self.conn.rollback()
            logger.error(f'Token数据插入失败，数据已回退,错误原因：{e}')

    def insert_msg_by_wx(self, **kwargs):
        c = self.conn.cursor()
        try:
            i = f"""INSERT INTO Message (send_message_time, message_text, msg_response) 
            VALUES ({kwargs['send_message_time']},'{kwargs['message_text']}','{kwargs['msg_response']}')"""
            c.execute(i)
            self.conn.commit()
            logger.info('验证码数据插入成功')
        except Exception as e:
            self.conn.rollback()
            logger.error(f'验证码数据插入失败，数据已回退,错误原因：{e}')

    def get_token_from_sql(self):
        c = self.conn.cursor()
        c.execute("select Token.token from Token order by ID DESC limit 0,1")
        access_token = c.fetchone()
        return access_token[0]

    def insert_msg_by_tty(self, **kwargs):
        c = self.conn.cursor()
        try:
            i = f"""INSERT INTO ReceiveMsg (receive_time, msg_mode, msg_id, msg_num, msg_num_index, msg_time, out_way, alphabet, ud, raw_pdu)
            VALUES ({time.strftime('%Y%m%d%H%M%S')},
                    {kwargs['msg_mode']},{kwargs['msg_id']},{kwargs['msg_num']},{kwargs['msg_num_index']},
                    '{kwargs['msg_time']}','{kwargs['out_way']}','{kwargs['alphabet']}','{kwargs['ud']}','{kwargs['raw_pdu']}')"""
            c.execute(i)
            self.conn.commit()
            logger.info('从终端获取的短信数据插入数据库成功')
        except Exception as e:
            self.conn.rollback()
            logger.error(f'从终端获取的短信数据插入数据库失败，数据已回退,错误原因：{e}')


if __name__ == '__main__':
    SQLOperation().init()
