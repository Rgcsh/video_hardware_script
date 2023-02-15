# -*- coding: utf-8 -*-
"""

All rights reserved
create time '2023/2/15 16:29'

Usage:

"""
import config
from cam_send import CamSend

# 项目入口,在硬件启动脚本中写入```import manager ```即可插电自启动
CamSend(config.wifi_name, config.wifi_password, config.udp_server_ip, config.udp_server_port, config.mqtt_server,
        config.mqtt_port, config.mqtt_user,
        config.mqtt_password).run()
