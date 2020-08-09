# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
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

# USN REASON
USN_REASON = {
    0x00000001:'DATA OVERWRITE',
    0x00000002:'DATA EXTEND',
    0x00000004:'DATA TRUNCATION',
    0x00000010:'NAMED DATA OVERWRITE',
    0x00000020:'NAMED DATA EXTEND',
    0x00000040:'NAMED DATA TRUNCATION',
    0x00000100:'FILE CREATE',
    0x00000200:'FILE DELETE',
    0x00000400:'EA CHANGE',
    0x00000800:'SECURITY CHANGE',
    0x00001000:'RENAME OLD NAME',
    0x00002000:'RENAME NEW NAME',
    0x00004000:'INDEXABLE CHANGE',
    0x00008000:'BASIC INfO CHANGE',
    0x00010000:'HARD LINK CHANGE',
    0x00020000:'COMPRESSION CHANGE',
    0x00040000:'ENCRYPTION CHANGE',
    0x00080000:'OBJECT ID CHANGE',
    0x00100000:'REPARSE POINT CHANGE',
    0x00200000:'STREAM CHANGE',
    0x00400000:'TRANSACTED CHANGE',
    0x00800000:'INTEGRITY CHANGE',
    0x80000000:'CLOSE'
}