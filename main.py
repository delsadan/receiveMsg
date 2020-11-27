# python3.8
# -*- coding:utf-8 -*-
# Author: imbiubiubiu
# Time : 2020-11-26
# 监听端口数据，提取原始pdu然后转成中文后，通过微信测试号发送至手机
import configparser
from init import logger
import threading
import re
import serial
from phrasePDU import phrasePDU
from init import SQLOperation
from wx_send_msg import send_message

Ret = False


def store_and_send_data(pdu):
    p = phrasePDU(pdu_str=pdu)
    out = p.phrase_msg_detail()
    if out:
        send_message(msg=out['ud'], sender=out['sender'])
        s = SQLOperation()
        s.insert_msg_by_tty(msg_mode=out['msg_mode'], msg_id=out['msg_id'], msg_num=out['msg_num'],
                            msg_num_index=out['msg_num_index'], msg_time=out['msg_time'], out_way=out['out_way'],
                            alphabet=out['alphabet'], ud=out['ud'], raw_pdu=out['raw_pdu'])


class monitorSMS:
    def __init__(self):
        cf = configparser.ConfigParser()
        cf.read('config.ini', encoding='utf-8')
        serial_port = cf['options']['port']
        self.pdu_length = cf['options']['pdu_length']
        global Ret
        try:
            self.ser = serial.Serial(serial_port, 9600, timeout=0.5)
            if self.ser.isOpen():
                logger.info(f'{self.ser.name} 端口已开')
                Ret = True
        except Exception as e:
            logger.error(f'异常: {e}')

    def open_port(self):
        self.ser.open()

    def close_port(self):
        self.ser.close()

    def send_data(self, data):
        return self.ser.write(data.encode('utf-8'))

    def receive_data(self, ):
        return str(self.ser.readall())

    def read_all_msgs(self):
        # 读取sim卡内所有数据
        self.send_data('AT+CMGL=4\r\n')
        out_raw = self.ser.readlines()
        out = []
        for i in out_raw:
            if len(i) > 30:
                pdu = i.decode('utf-8').strip("\r\n")
                out.append(pdu)
                p = phrasePDU(pdu_str=pdu).phrase_msg_detail()
        return out

    def receive_msg_always(self):
        logger.info('------------------开始监听端口数据------------------')
        while True:
            a = str(self.ser.readline().decode('utf-8'))
            if len(a) > int(self.pdu_length):
                logger.info(f'发现有新的短信，详情：{a}')
                store_and_send_data(a)

    def main(self):
        self.send_data('AT+CNMI=2,2,0,0,0\r\n')  # 设置消息为不保存，直接输出到终端
        out = self.receive_data()
        if 'OK' in out:
            logger.info('已将短信接收设置为：不保存SIM卡内，直接输出至终端')
        else:
            logger.error(f'短信接收设置初始化失败，输出详情：{out}')

        self.send_data('AT+CMGF=0\r\n')
        out = self.receive_data()
        if 'OK' in out:
            logger.info('已设置为PDU模式')
        else:
            logger.error(f'未设置成PDU模式，输出详情：{out}')

        self.send_data('AT+CPMS?\r\n')
        out = self.receive_data()
        pa = re.compile(r'CPMS: (.*?)\\r\\n')
        logger.info(f'当前SIM卡内短信存储情况：{pa.findall(out)}')

        t1 = threading.Thread(target=self.receive_msg_always, )
        t1.start()


if __name__ == '__main__':
    m = monitorSMS()

    if Ret:
        m.main()
