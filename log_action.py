# -*- coding: utf-8 -*-
"""

All rights reserved
create time '2022/11/24 14:14'

Usage:

"""


class LogWriter:
    """日志类"""
    def __init__(self):
        """

        """
        f = open('log.txt', 'a')
        self.f = f

    def info(self, message):
        """

        :param message:
        :return:
        """
        print(message)
        # self.f.write(f"{message} \n")

    def close(self):
        """

        :return:
        """
        self.f.close()

#
# log = LogWriter()
# log.info("info")
# log.close()
