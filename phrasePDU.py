# python3.8
# -*- coding:utf-8 -*-
# Author: imbiubiubiu
# Time : 2020-11-26
# desc: 解析短信PDU
"""
0891683108301145F3240EA1019650820213250008021152125105236C3010552F54C14F1A30119A8C8BC1780100310032003200360031003030026B649A8C8BC178014EC575284E8E6CE8518C552F54C14F1A8D2653F7FF0C9A8C8BC1780163D04F9B7ED94ED64EBA5C065BFC81F4552F54C14F1A8D2653F788AB76D7FF0C8BF752FF8F6C53D13002
08 # 短消息中心长度
91 68 31 08 30 11 45 F3 # SMSC：+8613800311543 0：9
24 # PDU Type: 0001 1000 8+1
0E # Length: 14位被叫号码长度 8+2
A1 # Tosca: 地址类型 8+3
01965082021325 # Address: 10690528203152 8+4 8+4+7
00 # PID协议标志，是短消息传输层作为高层协议参考，或者是远程设备协同工作的标志。需要服务商支持。但是00是所有服务商都支持的。建议采用00H即可。程序不处理 19+1
08 # DCS数据编码方法 0000 1000 19+2
021152125105 # SCTS服务中心时间戳：20-11-25 21:15:50
23 # 时区
6C # UDL

长短信分析
08
91
683108301145F3
64
05
A1
0180F6
00
08
021152918041
23
8C # UDL总长度
05 00 03 91 06 04 # UDH内容
    05--UDHL用户数据头长度
    00--UDH的意义，可以看刚才列举出的各个值的意义。
    03--剩下短信标识的长度，即后面的910604
    91--拆分短信的唯一标识，也就是说，以后组合短信时，要靠这个值识别本条拆分短信是属于哪个长短信。取值范围0~255。
    06--表示长短信被拆成多少份
    04--表示这是第4个拆分短信，也就是拆分短信的序号。
"""
import re
from init import logger


def byte_to_bin_array(byte_str):
    # 将单字符转成8位二进制list，如：hex08 --> [0,0,0,0,1,0,0,0,]
    bin_str = bin(int(f'0x{byte_str}', 16)).lstrip('0b')
    zero_num = 8 - len(bin_str)
    return [int(x) for x in list('0' * zero_num + bin_str)]


class phrasePDU:
    def __init__(self, pdu_str):
        self.pdu_str = pdu_str
        self.pdu_total = re.findall('.{2}', self.pdu_str)
        oa_length_raw = self.pdu_total[int(self.pdu_total[0]) + 2]
        oa_length = int(f'0x{oa_length_raw}', 16)
        if not oa_length % 2:
            self.sender_num_position = int(int(self.pdu_total[0]) + 4 + oa_length / 2)
        else:
            self.sender_num_position = int(int(self.pdu_total[0]) + 4 + oa_length / 2 + 1)

    def phrase_smsc(self):
        # 解析信息中心号码
        sca = self.pdu_total[:int(self.pdu_total[0]) + 1]
        if sca[1] == '91':  # 此处仅作常规91即'+'号判断，其他情况输出问号
            sca_out = ['+']
        else:
            sca_out = ['?']
        for n in sca[2:]:
            n = n[1] + n[0]
            sca_out.append(n)
        smsc = ''.join(sca_out).rstrip('F')  # 信息中心号码
        return smsc

    def is_short_message(self):
        # 判断是长或短信息,二进制第2位为1的存在UDHI，判断为长短信
        pdu_type = self.pdu_total[int(self.pdu_total[0]) + 1]
        if int(f'0x{pdu_type}', 16) < 64:
            return True
        else:
            return False

    def phrase_oa(self):
        # 解析发送方号码
        sender_num_list = self.pdu_total[int(self.pdu_total[0]) + 4:int(self.sender_num_position)]
        # print(sender_num_list)
        sender_num = []
        for n in sender_num_list:
            n = n[1] + n[0]
            sender_num.append(n)
        sender_phone = ''.join(sender_num).rstrip('F')  # 发送方号码
        return sender_phone

    def phrase_dcs(self):
        # 解析短信编码方案
        dcs_raw = self.pdu_total[self.sender_num_position + 1]
        b = byte_to_bin_array(dcs_raw)
        if b[6] == 0:
            if b[7] == 0:
                out_way = '短消息直接显示到用户终端'
            else:
                out_way = '消息存储在SIM卡上'
        else:
            if b[7] == 0:
                out_way = '短消息必须存储在SIM卡上，禁止直接传输到终端'
            else:
                out_way = '短消息存储在用户设备上'

        if b[4] == 0:
            if b[5] == 0:
                alphabet = '默认字母表'
            else:
                alphabet = '8bit数据'
        else:
            if b[5] == 0:
                alphabet = 'UCS2编码'
            else:
                alphabet = '保留'
        return {'out_way': out_way, 'alphabet': alphabet}

    def phrase_msg_time(self):
        # 解析消息到达时间
        time_raw = self.pdu_total[self.sender_num_position + 2:self.sender_num_position + 8]
        msg_time_list = []
        for t in time_raw:
            t = t[1] + t[0]
            msg_time_list.append(t)
        msg_time = f'20{msg_time_list[0]}年{msg_time_list[1]}月{msg_time_list[2]}日 {msg_time_list[3]}:{msg_time_list[4]}:{msg_time_list[5]}'
        # print(msg_time)
        return msg_time

    def phrase_longMsg(self):
        udl_raw = self.pdu_total[self.sender_num_position + 9:]
        udh_length = int(udl_raw[1])
        udh_raw = udl_raw[2:udh_length + 2]
        ud = ''.join(udl_raw[int(udl_raw[1]) + 2:])
        if udh_raw[0] != '00':
            return False
        else:
            long_msg_detail = {'msg_id': int(f'0x{udh_raw[2]}', 16),
                               'msg_num': int(f'0x{udh_raw[3]}', 16),
                               'msg_num_index': int(f'0x{udh_raw[4]}', 16),
                               'ud': ud}
            return long_msg_detail

    @staticmethod
    def phrase_ud(ud):
        """
        将pdu的ud部分按照2个字节拆分，拼接成unicode字符串，转成中文
        :param ud: ud短信内容原始数据
        :return: 解码过的中文短信
        """
        unicode_out = []
        if len(ud) % 4 == 0:
            split_4_str_list = re.findall('.{4}', ud)  # 切割4个字符，组成list
            for single_4 in split_4_str_list:
                su = f'\\u{single_4}'
                unicode_out.append(su)
            total_unicode_out = ''.join(unicode_out)
            return total_unicode_out.encode('utf-8').decode('unicode_escape')

    def phrase_msg_detail(self):
        # 根据短信长短,读取短信，主函数
        dcs = self.phrase_dcs()
        if self.is_short_message():
            ud_raw = ''.join(self.pdu_total[self.sender_num_position + 10:])
            # print(f'当前为普通短信，内容为：{self.phrase_ud(ud_raw)}\n')

            return {'msg_mode': 0,  # 代表普通短信
                    'msg_id': 1,
                    'msg_num': 1,
                    'msg_num_index': 1,
                    'msg_time': self.phrase_msg_time(),
                    'out_way': dcs['out_way'],
                    'alphabet': dcs['alphabet'],
                    'ud': self.phrase_ud(ud_raw),
                    'raw_pdu': self.pdu_str,
                    'sender': self.phrase_oa()}
        else:
            long_msg = self.phrase_longMsg()
            if not long_msg:
                logger.error(f'当前短信不是长短信：{self.pdu_str}')
                return
            else:
                # print(f'当前为长短信，短信ID：{long_msg["msg_id"]}，\n'
                #       f'当前为：{long_msg["msg_num_index"]}/{long_msg["msg_num"]}。\n短信内容为：{self.phrase_ud(long_msg["ud"])}')
                return {
                    'msg_mode': 1,  # 代表长短信
                    'msg_id': long_msg["msg_id"],
                    'msg_num': long_msg["msg_num"],
                    'msg_num_index': long_msg["msg_num_index"],
                    'msg_time': self.phrase_msg_time(),
                    'out_way': dcs['out_way'],
                    'alphabet': dcs['alphabet'],
                    'ud': self.phrase_ud(long_msg["ud"]),
                    'raw_pdu': self.pdu_str,
                    'sender': self.phrase_oa()
                }


if __name__ == '__main__':

    with open('1.txt', 'r', encoding='utf-8') as f:
        file = f.readlines()
    for i in file:
        i = i.strip('\n')
        p = phrasePDU(pdu_str=i)
        p.phrase_msg_detail()
