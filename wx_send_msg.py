#!/user/bin/env python3
# -*- coding:utf-8 -*-
# 作者：imbiubiubiu
# 创建：2020-11-21
# 更新：2020-11-21
# 用意：微信测试测试号发送信息
# 微信测试公众号申请地址：https://mp.weixin.qq.com/debug/cgi-bin/sandboxinfo?action=showinfo&t=sandbox/index
import json
import requests
import configparser
import time
import init
import threading
from init import logger

sp = init.SQLOperation()

cf = configparser.ConfigParser()
cf.read('config.ini', encoding='utf-8')


class getToken:
    def __init__(self):
        self.appID = cf.get('weixin', 'appID')
        self.appsecret = cf.get('weixin', 'appsecret')

    def get_token(self):
        token_url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appID}&secret={self.appsecret}'
        res = requests.get(url=token_url).json()
        if 'errcode' in res:
            print(f'请检查appID及appsecret配置！具体错误原因：{res}')
            return
        accessToken = res.get('access_token')
        get_token_time = time.time() + 7200
        expire_token_time = time.time() + 7200
        init.logger.info(accessToken)
        sp.insert_token(get_token_time=get_token_time, expire_token_time=expire_token_time,
                        token='\'' + accessToken + '\'')
        return accessToken

    def get_token_always(self):
        # 每119分钟获取一次token插入数据库
        while True:
            self.get_token()
            logger.info('119分钟后再次准备获取Token！')
            time.sleep(60 * 119)


def send_message(**kwargs):
    retry_num = 1
    while retry_num < 4:
        msg = kwargs['msg']
        access_token = sp.get_token_from_sql()
        user_list = cf['user']['user_wx_openid'].split(',')
        if not user_list[-1]:
            user_list.remove('')
        template_id = cf['weixin']['template_id']  # 消息模板
        message_url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
        for user_id in user_list:
            body = {
                "touser": user_id,
                "template_id": template_id,
                "url": '',
                "topcolor": "#FF0000",
                'data': {
                    'sender': {
                        'value': kwargs['sender'],
                        "color": "#173177"
                    },
                    'msg': {
                        'value': kwargs['msg'],
                        "color": "#173177"
                    }
                }
            }
            r = requests.post(url=message_url, data=json.dumps(body, ensure_ascii=False).encode('utf-8'))
            sp.insert_msg_by_wx(
                send_message_time=f"{time.strftime('%Y%m%d%H%M%S')}",
                message_text=f"{msg}",
                msg_response=f"{r.text}"
            )

            if '42001' in r.text:
                logger.error(f'{msg}发送失败，正在重试第 {retry_num} 次，详情：{r.text}')
                getToken().get_token()
                retry_num += 1
            else:
                logger.success(f'{msg}发送成功！')
                return


t1 = threading.Thread(target=getToken().get_token_always)
t1.start()

if __name__ == '__main__':
    send_message()
