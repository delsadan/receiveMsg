搭建个人短信转发设备
===
通过SIM800C模块串口获取短信数据，利用树莓派作为计算中心解码后，将结果通过微信测试公众号平台发给自己的微信号

+ 提醒：别想用于非法目的，“断卡行动”在等你

+ 非专业开发，代码写的比较烂，凑合看，谢谢！

+ BUG肯定是有滴，修基本是不存在滴

# 一、准备工作

## 1.1 硬件

+ 树莓派3B+(Raspbian GNU/Linux 9 (stretch))

+ SIM800C模块（带USB串口，某宝）

+ SIM卡（仅支持中国移动，某宝，自行实名）

## 1.2 软件

+ python3.6+

+ Raspbian/Win/Linux

+ 微信号一个（接收短信及登入下面的平台）

+ [微信公众平台-测试号]("https://mp.weixin.qq.com/debug/cgi-bin/sandboxinfo?action=showinfo&t=sandbox/index")，自行扫码登入即可
  
   * F&Q：为啥不用公开的方糖或者wxpusher?
   * 可以自行采用，不过这边考虑到短信数据可能比较敏感，所以使用测试公众号。缺点为入口比较隐蔽，需要给公众号加星标，但是也有消息提醒。
   
## 1.3 目录文件解析

    ├── 1.txt  # 测试pdu短信解析的文本，没啥用 
    ├── config.ini  # 程序配置文件
    ├── database.db  # 本地存的数据库，需程序初始化以后，才会生成
    ├── init.py  # 程序初始化
    ├── log  # 日志
    │   └── log.txt
    ├── main.py  # 主程序
    ├── phrasePDU.py  # 串口读取到的pdu数据解析为中文函数
    └── wx_send_msg.py  # 利用微信测试号发送消息函数 


# 二、安装&运行

## 2.1 基本

```bash
# 安装环境依赖
pip install -r requirements.txt

# 安装supervisor进程守护
pip install supervisor

# 插好SIM800C模块以后，确认/dev/ttyUSB具体的端口号
ls /dev/tty* | grep ttyUSB
```

## 2.2 config.ini配置文件解析
```
[weixin]
# 测试号管理-测试号信息
appID = wxxxxxxxxxxxx
appsecret = xxxxxxxxxxxxxxxxxxxxxxx
# 新增测试模板，复制模板ID
template_id = xxxxxxxxxxxxxxxxx

[user]
# 用户列表-微信号，多个用户使用英文逗号分割
user_wx_openid = oSxxxxxxxxxxxxxxxxx,

[options]
# tty端口
# Linux：/dev/ttyUSB0、/dev/ttyAMA0、/dev/ttyS1
# Win：1、com4
port=/dev/ttyUSB0
```

关于测试模板，可直接复制粘贴：`大帅逼，你有新的验证码到啦! 发件人：{{sender.DATA}} 正文：{{msg.DATA}}`

+ 注：{{}}内的变量较为重要，如果修改会影响短信发送，其他可自行调整。

程序初始化（当前目录下生成数据库）：`python3 init.py`

## 2.3 supervisor进程守护

+ 新建supervisor子程序配置
 
 `nano /etc/supervisor/conf.d/msg.conf`

复制粘贴以下内容，中间内容自行修改
```
#项目名
[program:msg]
#脚本目录，这个是程序所在目录
directory=/root/receiveMsg
#脚本执行命令
command=python3 /root/receiveMsg/main.py

#supervisor启动的时候是否随着同时启动，默认True
autostart=true
autorestart=false
#这个选项是子进程启动多少秒之后，此时状态如果是running，则我们认为启动成功了。默认值为1
startsecs=3

#脚本运行的用户身份
user = root
#日志输出
stderr_logfile=/tmp/receiveMsg_stderr.log
stdout_logfile=/tmp/receiveMsg_stdout.log
#把stderr重定向到stdout，默认 false
redirect_stderr = false
#stdout日志文件大小，默认 50MB
stdout_logfile_maxbytes = 20MB
#stdout日志文件备份数
stdout_logfile_backups = 10
```

+ 更新配置文件：`supervisorctl update`
+ 查看程序状态：`supervisorctl status msg`
+ 启动程序：`supervisorctl start msg`
+ 关于supervisor: `service supervisor restart/start/stop/status`
+ 程序运行日志：`tail /tmp/receiveMsg_stdout.log`


