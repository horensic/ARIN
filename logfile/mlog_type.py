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


# Logfile Entry

# Entry Header
REFS_ENTRY_HDR_FORMAT = '<4s3I16s2I2Q8I32s'
REFS_ENTRY_HDR_FIELDS = [
    'signature', 'id', '0x1(fixed)', 'size',
    'uuid',
    'control', '0x0(fixed)', 'current_ml_lsn',
    'previous_ml_lsn', 'unknown1(0x1)', 'unknown2(0x1)',
    'offset_0x24_value', 'unknown3', 'unknown4', 'unknown5',
    'unknown6(0x0)', 'entry_hdr_size',
    'unknown7'
]
REFS_ENTRY_HDR_SZ = struct.calcsize(REFS_ENTRY_HDR_FORMAT)

if REFS_ENTRY_HDR_SZ != 0x78:
    print("REFS Entry header size not match!")
    exit(-1)

# Log Header
REFS_LOG_HDR_FORMAT = '<2Q2IQ4IQ'
REFS_LOG_HDR_FIELDS = [
    'current_ml_lsn', 'checksum',
    'unknown1', 'unknown2', 'previous_ml_lsn',
    'data_size', 'unknown3(0x1)', 'log_hdr_size', 'log_size',
    'type'
]
REFS_LOG_HDR_SZ = struct.calcsize(REFS_LOG_HDR_FORMAT)

if REFS_LOG_HDR_SZ != 0x38:
    print("REFS Log header size not match!")
    exit(-1)

# Log Control Info
REFS_LOG_CTRL_INFO_FORMAT = '<5Q16s2I2Q'
REFS_LOG_CTRL_INFO_FIELDS = [
    'seq_no', 'start_offset',
    'end_offset', 'next_lsn',
    'next_lsn (dup)', 'uuid',
    'control', 'unknown1',
    'unknown2', 'unknown3'
]
REFS_LOG_CTRL_INFO_SZ = struct.calcsize(REFS_LOG_CTRL_INFO_FORMAT)

# Redo Record Header
REFS_REDO_REC_HDR_FORMAT = '<6I2Q4I'
REFS_REDO_REC_HDR_FIELDS = [
    'redo_rec_size', 'opcode', 'tablekeys_count', 'tablekeys_offset',
    'value_count', 'value_offset', 'unknown1',
    'unknown2', 'unknown3', 'rec_mark',
    'seq_no', 'end_mark'
]
REFS_REDO_REC_HDR_SZ = struct.calcsize(REFS_REDO_REC_HDR_FORMAT)

if REFS_REDO_REC_HDR_SZ != 0x38:
    print("REFS Transaction context header size not match!")
    exit(-1)

# Transaction Target Object
REFS_TX_TARGET_KEY_FORMAT = '<3I2Q'
REFS_TX_TARGET_KEY_FIELDS = [
    '_unknown1', 'obj_type', '_unknown2',
    'parent_id', 'obj_id'
]
REFS_TX_TARGET_KEY_SZ = struct.calcsize(REFS_TX_TARGET_KEY_FORMAT)

REFS_FILE_REC_KEY_FORMAT = '<4I'
REFS_FILE_REC_KEY_FIELDS = [
    '_unknown1', 'obj_type', '_unknown2', 'type'
]
REFS_FILE_REC_KEY_SZ = struct.calcsize(REFS_FILE_REC_KEY_FORMAT)

REFS_FILE_IDX_KEY_FORMAT = '<2I2Q'
REFS_FILE_IDX_KEY_FIELDS = [
    'type', '_unknown1', 'file_seq_no', '_unknown2'
]
REFS_FILE_IDX_KEY_SZ = struct.calcsize(REFS_FILE_IDX_KEY_FORMAT)