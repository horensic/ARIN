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

import struct


# USN RECORD V3
USN_REC_V3_FORMAT = '<I2H16s16s2Q4I2H'
USN_REC_V3_FIELDS = [
    'record_length', 'major', 'minor',
    'file_reference_number',
    'parent_file_reference_number',
    'usn',
    'timestamp', 'reason', 'source_info',
    'security_id', 'file_attribute', 'length', 'offset'
]
USN_REC_V3_SZ = struct.calcsize(USN_REC_V3_FORMAT)

if USN_REC_V3_SZ != 0x4C:
    print("USN Record V3 size not match!")
    exit(-1)