#!/usr/bin/env python
# -*- coding: utf-8 -*-

#           OH MY GIRL License
#   To create a program using this source code,
#   Follow the link below to listen to the OH MY GIRL's song at least once.
#   LINK (1): https://youtu.be/RrvdjyIL0fA
#   LINK (2): https://youtu.be/QIN5_tJRiyY
#   LINK (3): https://youtu.be/udGwca1HBM4
#   LINK (4): https://youtu.be/QTD_yleCK9Y

"""
@author:    Seonho Lee
@license:   OH_MY_GIRL License
@contact:   horensic@gmail.com
"""

import io
from datetime import datetime, timedelta
from chgjrnl.usn_type import *

class USNRecordV3:

    def __init__(self, record_buf):
        self.record_buf = io.BytesIO(record_buf)
        self.record = self.parse_record(self.record_buf)
        self.record['name'] = self.parse_name(self.record_buf)

    def parse_record(self, record_buf):

        def win64le(v, bias=None):
            """
            ReFS Timestamp format
            :param v: little-endian binary data in long(integer) type (ex. 131210007740281591)
            :param bias: timezone option
            :return: YYYY-MM-DD hh:mm:ss.us
            """
            dt = "{0:x}".format(v)
            us = int(dt, 16) / 10.
            return datetime(1601, 1, 1) + timedelta(microseconds=us)

        def reason(flag):
            ret = []
            for k, v in USN_REASON.items():
                if (flag & k) == k:
                    ret.append(v)
            return ' | '.join(ret)

        buf = record_buf.read(USN_REC_V3_SZ)
        record = dict(zip(USN_REC_V3_FIELDS, struct.unpack(USN_REC_V3_FORMAT, buf)))
        record['timestamp'] = win64le(record['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        record['reason'] = reason(record['reason'])
        return record

    def parse_name(self, record_buf):
        record_buf.seek(self.record['offset'])
        return record_buf.read(self.record['length']).decode('utf-16')
