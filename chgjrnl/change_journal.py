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
from chgjrnl.usn_type import *

class USNRecordV3:

    def __init__(self, record_buf):
        self.record_buf = io.BytesIO(record_buf)
        self.record = self.parse_record(self.record_buf)
        self.record['name'] = self.parse_name(self.record_buf)

    def parse_record(self, record_buf):
        buf = record_buf.read(USN_REC_V3_SZ)
        return dict(zip(USN_REC_V3_FIELDS, struct.unpack(USN_REC_V3_FORMAT, buf)))

    def parse_name(self, record_buf):
        record_buf.seek(self.record['offset'])
        return record_buf.read(self.record['length']).decode('utf-16')
