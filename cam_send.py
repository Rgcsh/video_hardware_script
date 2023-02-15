import socket
import time

import camera
import esp32
import network
from machine import WDT

from flash_light import control_flash
from log_action import LogWriter
from umqtt.simple import MQTTClientRobust

log = LogWriter()


class CamSend:
    def __init__(self, wifi_name, wifi_password, udp_server_ip, udp_server_port, mqtt_server, mqtt_port, mqtt_user,
                 mqtt_password):
        """

        :param wifi_name:
        :param wifi_password:
        :param udp_server_ip:
        :param udp_server_port:
        :param mqtt_server:
        :param mqtt_port:
        :param mqtt_user:
        :param mqtt_password:
        """
        # wifi配置
        self.wifi_name = wifi_name
        self.wifi_password = wifi_password
        # udp传输图片配置
        self.udp_server_ip = udp_server_ip
        self.udp_server_port = udp_server_port
        # mqtt配置
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        # 发送图片间隔时间
        self.send_img_sleep_time = 0.1
        # mqtt订阅的topic
        self.topic = b"camera_frq"

    def mqtt_client_init(self):
        """
        mqtt客户端初始化,连接到mqtt服务器
        :param server:
        :param port:
        :param user:
        :param password:
        :return:
        """
        log.info("尝试连接mqtt")
        self.mqtt_client = MQTTClientRobust("camera_client", self.mqtt_server, self.mqtt_port, self.mqtt_user,
                                            self.mqtt_password)
        self.mqtt_client.set_callback(self.topic_subscribe)
        self.mqtt_client.connect(False)
        log.info("连接成功")
        self.mqtt_client.subscribe(self.topic)

    def connect_wifi(self):
        """
        连接wifi,注意只能连接2.4G HZ的wifi,否则会卡住,且需要拔插操作才能重新操作
        :return:
        """
        log.info('连接wifi')
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        is_connected = wlan.isconnected()
        if not is_connected:
            log.info('尚未连接wifi,现在尝试连接...')
            # connect函数是异步的,所以要手动的等待一段时间
            wlan.connect(self.wifi_name, self.wifi_password)
            time.sleep(5)
            # 循环3次,失败后不再连接,并报错
            count = 0
            while not wlan.isconnected():
                control_flash(0.5)
                count += 1
                log.info(f"尝试连接第{count}次")
                time.sleep(1)
                if count > 1:
                    control_flash(0.1)
                    raise Exception("wifi 连接失败,请检测修改")
        control_flash(1)
        log.info('连接wifi成功!')

    def topic_subscribe(self, topic, msg):
        """
        消息订阅处理函数
        :param topic:
        :param msg:
        :return:
        """
        if topic != self.topic:
            return
        # 摄像头发送图片频率 0:高 1:低
        if int(msg) == 1:
            log.info("图片发送频率降低")
            self.send_img_sleep_time = 0.5
        else:
            log.info("图片发送频率提高")
            self.send_img_sleep_time = 0.1

    def camera_init(self):
        """
        摄像头初始化
        :return:
        """
        log.info("摄像头初始化...")
        try:
            camera.init(0, format=camera.JPEG)
        except Exception:
            camera.deinit()
            camera.init(0, format=camera.JPEG)

    def camera_config(self):
        """
        摄像头参数配置
        :return:
        """
        log.info("摄像头参数配置")

        # 上翻下翻
        camera.flip(0)
        # 左/右
        camera.mirror(1)

        # 分辨率
        camera.framesize(camera.FRAME_HVGA)  # 像素水平:480*320
        # camera.framesize(camera.FRAME_VGA) # 像素水平:640*480
        # camera.framesize(camera.FRAME_SVGA)  # 像素水平:800*600
        # 选项如下：
        # FRAME_96X96 FRAME_QQVGA FRAME_QCIF FRAME_HQVGA FRAME_240X240
        # FRAME_QVGA FRAME_CIF FRAME_HVGA FRAME_VGA FRAME_SVGA
        # FRAME_XGA FRAME_HD FRAME_SXGA FRAME_UXGA FRAME_FHD
        # FRAME_P_HD FRAME_P_3MP FRAME_QXGA FRAME_QHD FRAME_WQXGA
        # FRAME_P_FHD FRAME_QSXGA
        # 有关详细信息，请查看此链接：https://bit.ly/2YOzizz

        # 特效
        camera.speffect(camera.EFFECT_NONE)
        # 选项如下：
        # 效果\无（默认）效果\负效果\ BW效果\红色效果\绿色效果\蓝色效果\复古效果
        # EFFECT_NONE (default) EFFECT_NEG \EFFECT_BW\ EFFECT_RED\ EFFECT_GREEN\ EFFECT_BLUE\ EFFECT_RETRO

        # 白平衡
        camera.whitebalance(camera.WB_HOME)
        # 选项如下：
        # WB_NONE (default) WB_SUNNY WB_CLOUDY WB_OFFICE WB_HOME

        # 饱和
        camera.saturation(0)
        # -2,2（默认为0）. -2灰度
        # -2,2 (default 0). -2 grayscale

        # 亮度
        camera.brightness(0)
        # -2,2（默认为0）. 2亮度
        # -2,2 (default 0). 2 brightness

        # 对比度
        camera.contrast(0)
        # -2,2（默认为0）.2高对比度
        # -2,2 (default 0). 2 highcontrast

        # 质量
        camera.quality(2)
        # 10-63数字越小质量越高

    def udp_init(self):
        """
        UDP连接创建对应socket
        :return:
        """
        log.info("UDP连接创建对应socket")
        self.udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

    def send_data(self):
        """
        图片数据通过udp协议发送给服务器
        :return:
        """
        log.info("开始发送数据")
        try:
            count = 0
            while True:
                self.mqtt_client.check_msg()
                # Then need to sleep
                count += 1
                # 每隔100s查看一下温度
                if count == 100:
                    # 读取 MCU(微控制器)温度
                    temperature = esp32.raw_temperature()
                    # 华氏温度 对 摄氏度换算公式: (华氏温度-32)/1.8
                    log.info(f"MCU温度:{round((int(temperature) - 32) / 1.8, 2)}°C")
                    count = 0
                # 获取图像数据
                buf = camera.capture()
                # 向服务器发送图像数据
                self.udp_client.sendto(b'cameraSend' + buf, (self.udp_server_ip, self.udp_server_port))
                # 根据实际情况调节摄像头发送图片频率,节约资源
                time.sleep(self.send_img_sleep_time)
                # 给看门狗喂食
                self.wdt.feed()
        except:
            pass
        finally:
            camera.deinit()

    def run(self):
        """
        程序运行
        :return:
        """
        # 开门狗,设置10s不喂食,就停止服务,防止服务假死等情况
        self.wdt = WDT(timeout=10000)
        self.connect_wifi()
        self.mqtt_client_init()
        self.camera_init()
        self.camera_config()
        self.udp_init()
        self.send_data()
