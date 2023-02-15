# -*- coding: utf-8 -*-
# """
#
# All rights reserved
# create time '2022/11/24 11:31'
#

# """
import time

from machine import Pin


def control_flash(times=1):
    """
    闪光灯
    :param times:闪烁时长(s)
    :return:
    """
    # 控制闪光灯
    pin33 = Pin(4, Pin.OUT)
    time.sleep(times)
    print("设置值为1")
    pin33.value(1)
    time.sleep(times)
    print("设置值为0")
    pin33.value(0)
    time.sleep(times)
