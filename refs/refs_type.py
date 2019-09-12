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

""" ReFS v1.2 """

# Volume Header
REFS_VHDR_FORMAT = '<3s4s9s4sHHQIIBBHIQQ'
REFS_VHDR_FILEDS = [
    'jump_code',
    'signature',
    '_unknown1',
    'FSRS',
    '_unknown_length',
    '_unknown_checksum',

    'number_of_sectors',
    'bps',  # bytes per sector
    'cpb',  # sectors per block

    'major',
    'minor',
    '_unknown5'
    '_unknown6',
    '_unknown7',
]
REFS_VHDR_SZ = struct.calcsize(REFS_VHDR_FORMAT)

# Metadata Header
META_HDR_FORMAT = '<QQQQ16s'
META_HDR_FILEDS = [
    'block_number',
    'sequence_number',
    '_unknown',
    'object_id',  # If this value is 0, an important metadata file
    '_unknown0'
]
META_HDR_SZ = struct.calcsize(META_HDR_FORMAT)

# Super Block
SUPB_FORMAT = '<112sQQ'
SUPB_FILEDS = [
    '_unknown1',
    'primary',
    'secondary'
]
SUPB_SZ = struct.calcsize(SUPB_FORMAT)

# Check Point
CHKP_FORMAT = '<8sI28sI'
CHKP_FILEDS = [
    '_unknown1',
    'entry_start_offset',
    '_unknown2',
    'number_of_entries'
]
CHKP_SZ = struct.calcsize(CHKP_FORMAT)

REFS_V1_METADATA = ['$Object Tree', '$ALLOCATOR_LRG', '$ALLOCATOR_MED', '$ALLOCATOR_SML', '$ATTRIBUTE_LIST', '$OBJECT']

# Check Point Entry
CHKP_ENTRY_FORMAT = '<QQQ'
CHKP_ENTRY_FILEDS = [
    'block_number',
    '_sequence_number',
    '_checksum'
]
CHKP_ENTRY_SZ = struct.calcsize(CHKP_ENTRY_FORMAT)

# Object Table Entry
OBJT_ENTRY_FORMAT = '<8I'
OBJT_ENTRY_FILEDS = [
    'entry_size',
    'unused_table_data_offset',
    'unused_table_data_size',
    '_unknown1',
    'value_offsets_array_start_offset',
    'number_of_values',
    'value_offsets_array_end_offset',
    '_unknown2'
]
OBJT_ENTRY_SZ = struct.calcsize(OBJT_ENTRY_FORMAT)

META_DATA_HDR_FORMAT = '<I4HI'
META_DATA_HDR_FILEDS = [
    'metadata_size',
    'id_data_offset',
    'id_data_size',
    'flags',
    'data_offset',
    'data_size'
]
META_DATA_HDR_SZ = struct.calcsize(META_DATA_HDR_FORMAT)

META_DATA_FORMAT = '<6Q'
META_DATA_FILEDS = [
    'block_number',
    '_unknown1',
    'checksum',
    '_unknown2',
    '_unknown3',
    'number_of_file'
]
META_DATA_SZ = struct.calcsize(META_DATA_FORMAT)

FILE_META_FORMAT = ''
FILE_META_FILEDS = [

]
FILE_META_SZ = struct.calcsize(FILE_META_FORMAT)

OBJ_ID = {
    0x1: '$ATTRIBUTE_LIST',
    0x2: '$Object Table',
    0x3: '$OBJECT',
    0xC: '$ALLOCATOR_SML',
    0xD: '$ALLOCATOR_MED',
    0xE: '$ALLOCATOR_LRG'
}

# Object ID
OID = {
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00':'$Volume Label',
    b'\x00\x00\x00\x00\x00\x00\x00\x00 \x05\x00\x00\x00\x00\x00\x00':'File System Metadata',
    b'\x00\x00\x00\x00\x00\x00\x00\x000\x05\x00\x00\x00\x00\x00\x00':'$SDS Data',
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00':'Root Directory',
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x07\x00\x00\x00\x00\x00\x00':'Sub Directory',
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x02\x07\x00\x00\x00\x00\x00\x00':'Sub Directory',
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x07\x00\x00\x00\x00\x00\x00':'Sub Directory'
}

""" ReFS v3.X """

# Metadata signatures
REFS_MAGIC = [b'SUPB', b'CHKP', b'MSB+', b'MLog']

# Metadata Header
META_HDR_3FORMAT = '<4sIQ16s4Q2Q'
META_HDR_3FILEDS = [
    'signature',
    'fixed_0x2?',
    '_unknown_2',
    '_unknown_3',
    'LCN(1)',
    'LCN(2)',
    'LCN(3)',
    'LCN(4)',
    '_object_id',
    'object_id'
]
META_HDR_3SZ = struct.calcsize(META_HDR_3FORMAT)

# Super Block
SUPB_3FORMAT = '<16s2Q4I64sQQ'
SUPB_3FILEDS = [
    'guid',
    '_unknown1',
    '_unknown2',
    '_unknown3',
    '_unknown4',
    '_unknown5',
    '_unknown6',
    '_unknown7',
    'primary',
    'secondary'
]
SUPB_3SZ = struct.calcsize(SUPB_3FORMAT)

# Check Point
CHKP_3FORMAT = '<I2H2IQ6I16s'
CHKP_3FILEDS = [
    '_unknown1',
    'major',
    'minor',
    'entry_offset',
    'entry_size',
    '_block_number',
    '_unknown2',
    '_unknown3',
    '_unknown4',
    '_unknown5',
    '_unknown6',
    '_unknown7',
    '_unknown8'
]
CHKP_3SZ = struct.calcsize(CHKP_3FORMAT)

OBJ_ID_3 = {
    0x1: '$ATTRIBUTE_LIST',
    0x2: '$Object Table',
    0x3: '$OBJECT',
    0x4: 'New_Metadata(1)',
    0x5: 'New_Metadata(2)',
    0x6: 'New_Metadata(3)',
    0xB: 'New_Metadata(4)',
    0xC: '$ALLOCATOR_SML',
    0xD: '$ALLOCATOR_MED',
    0xE: '$ALLOCATOR_LRG',
    0xF: 'New_Metadata(5)',

    0x20: 'New_Metadata(6)',
    0x21: 'New_Metadata(7)',
    0x22: 'New_Metadata(8)'
}

OID_3 = {
    'Upcase Table':b'\x00\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00',
    'Upcase Table (dup)':b'\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00',
    'Logfile Information Table':b'\x00\x00\x00\x00\x00\x00\x00\x00\x09\x00\x00\x00\x00\x00\x00\x00',
    'Logfile Information Table (dup)':b'\x00\x00\x00\x00\x00\x00\x00\x00\x0A\x00\x00\x00\x00\x00\x00\x00',
    'Root Directory':b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00',
    'File System Metadata':b'\x00\x00\x00\x00\x00\x00\x00\x00\x20\x05\x00\x00\x00\x00\x00\x00'
}

REFS_V3_METADATA = [
    '$Object Table',
    '$ALLOCATOR_LRG?',
    '$ALLOCATOR_MED?',
    '$ALLOCATOR_SML?',
    '$ATTRIBUTE_LIST?',
    '$OBJECT?',
    '???1',
    '???2',
    '???3',
    '???4',
    '???5',
    '???6',
    '???7',
    '???8',
]

# Check Point Entry
CHKP_ENTRY_3FORMAT = '<QQQQIIQ56s'
CHKP_ENTRY_3FILEDS = [
    'LCN(1)',
    'LCN(2)',
    'LCN(3)',
    'LCN(4)',
    'unknown1',
    'unknown2',
    'checksum?',
    'padding'
]
CHKP_ENTRY_3SZ = struct.calcsize(CHKP_ENTRY_3FORMAT)

CHKP_ENTRY_PADDING = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                     b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                     b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                     b'\x00\x00\x00\x00\x00\x00\x00\x00'

# Metapage Attribute
TABLE_DESC_3FORMAT = '<6I2Q'
TABLE_DESC_3FILEDS = [
    'size',
    'unknown1',
    'unknown2',
    'meta_type',
    'meta_host',
    'unknown3',
    'child_count',
    'row_count'
]
TABLE_DESC_3SZ = struct.calcsize(TABLE_DESC_3FORMAT)

# Entry Table Header
TABLE_HDR_3FORMAT = '<10I'
TABLE_HDR_3FIELDS = [
    'len_of_table_header',
    'len_of_total_entry',  # Header Start Offset +
    'len_of_padding',
    'type',  # 0x301 - Children Node // 0x600 - File $DATA Attribute
    'array_start',
    'fanout',
    '_unknown1',
    '_unknown2',
    'array_end',
    '_padding'
]
TABLE_HDR_3SZ = struct.calcsize(TABLE_HDR_3FORMAT)

# Element of Array
ARR_ELEM_3FORMAT = '<HH'
ARR_ELEM_3SZ = struct.calcsize(ARR_ELEM_3FORMAT)

# ROW Type Header
ROW_HDR_3FORMAT = '<I6H'
ROW_HDR_3FIELDS = [
    'length',
    'offset_key',
    'len_key',
    'flags',
    'offset_value',
    'len_value',
    'padding'
]
ROW_HDR_3SZ = struct.calcsize(ROW_HDR_3FORMAT)

# LCN_CHKSUM
LCN_CHKSUM_3FORMAT = '<4Q2I8s'
LCN_CHKSUM_3FIELDS = [
    'LCN(1)',
    'LCN(2)',
    'LCN(3)',
    'LCN(4)',
    '_unknown1',
    '_unknown2',
    'checksum'
]
LCN_CHKSUM_3SZ = struct.calcsize(LCN_CHKSUM_3FORMAT)

# Container Table row value
CONTAINER_ROW_3FORMAT = '<Q136sQ2I'
CONTAINER_ROW_3FIELDS = [
    'key',
    '_unknown1',
    'cluster_no',
    'cpc',
    'padding'
]
CONTAINER_ROW_3SZ = struct.calcsize(CONTAINER_ROW_3FORMAT)

# Object Table row value
# OLD_OBJECT_ROW_3FORMAT = '<8I4Q2I8s112s6Q'
OBJECT_ROW_3FORMAT = '<8I4Q2I8s'
OBJECT_ROW_3FIELDS = [
    '_unknown1',
    '_unknown2',
    '_unknown3',
    '_unknown4',
    '_unknown5',
    '_unknown6',
    '_unknown7',
    '_unknown8',
    'LCN(1)',
    'LCN(2)',
    'LCN(3)',
    'LCN(4)',
    '_unknown9',
    '_unknown10',
    'checksum'
]
OBJECT_ROW_3SZ = struct.calcsize(OBJECT_ROW_3FORMAT)

# Logfile Information Table
LOGFILE_INFO_ROW_3FORMAT = '<6Q'
LOGFILE_INFO_ROW_3FIELDS = [
    '_unknown1',
    '_unknown2',
    '_unknown3',
    'LOGFILE_INFO_LCN',
    'LOGFILE_INFO_LCN (dup)',
    '_unknown4'
]
LOGFILE_INFO_ROW_3SZ = struct.calcsize(LOGFILE_INFO_ROW_3FORMAT)

# Logfile
LOGFILE_HDR_3FORMAT = '<4I16s4Q'
LOGFILE_HDR_3FIELDS = [
    'signature',
    '_checksum',
    '_unknown1',
    '_unknown2',
    'uuid',
    '_unknown_',
    'CURRENT_LSN',
    'PREVIOUS_LSN',
    'unknown'
]
LOGFILE_HDR_3SZ = struct.calcsize(LOGFILE_HDR_3FORMAT)

# Redo Operation
REDO_OP = {
    0x0: 'Open Table',
    0x1: 'Redo Insert Row',
    0x2: 'Redo Delete Row',
    0x3: 'Redo Update Row',
    0x4: 'Redo Update Data with Root',
    0x5: 'Redo Reparent Table',
    0x6: 'Redo Allocate',
    0x7: 'Redo Free',
    0x8: 'Redo Set Range State (0x8)',
    0x9: 'Redo Set Range State (0x9)',
    0xA: 'Redo Duplicate Extents',
    0xB: 'Redo Modify Stream Extent',
    0xC: 'Redo Strip Metadata Stream Extent',
    0xD: 'Redo Set Integrity',
    0xE: 'Redo Set Parent Id',
    0xF: 'Redo Delete Table',
    0x10: 'Redo Value as Key',
    0x11: 'Redo Add Schema',
    0x12: 'Copy Key Helper (0x12)',
    0x13: 'Redo Add Container',
    0x14: 'Redo Move Container',
    0x15: 'Copy Key Helper (0x15)',
    0x16: 'Redo Cache Invalidation',
    0x17: 'Redo Generate Checksum',
    0x18: 'Redo Container Compression',
    0x19: 'Redo Delete Compression Unit Offsets',
    0x1A: 'Redo Add Compress Unit Offsets',
    0x1B: 'Redo Ghost Extents',
    0x1C: 'Redo Compaction Unreserve'
}

# FILE_TYPE
FILE_TYPE_3 = {
    b'\x30\x00\x02\x00':'Directory',
    b'\x30\x00\x01\x00':'Regular file',
    b'\x10\x00\x00\x00':'Self',
    b'\x20\x00\x00\x80':'???'
}

# Directory Entry Value
# DIR_ENTRY_VALUE_3FORMAT = '<6Q16sHHI'
DIR_TYPE_ENTRY_3FORMAT = '<16s4Q16sHHI'
DIR_TYPE_ENTRY_3FIELDS = [
    'object_id',
    'CreateTime',
    'AccessTime',
    'ModifiedTime',
    'EntryTime',
    '_unknown1',
    'flag',
    'flag2?',
    'padding'
]
DIR_TYPE_ENTRY_3SZ = struct.calcsize(DIR_TYPE_ENTRY_3FORMAT)

# Regular File Entry Value
# REG_FILE_ENTRY_VALUE_3FORMAT = '<3I4s2I2Q4QQI84s'
REG_TYPE_ENTRY_3FORMAT = '<6I16s4Q6I'
REG_TYPE_ENTRY_3FIELDS = [
    'length_of_metadata',
    'fixed_0x10028?',
    'fixed_0x1?',
    '_unknown1',
    '_unknown1_repeat?',
    '_unknown2',
    'object_id',
    'CreateTime',
    'AccessTime',
    'ModifiedTime',
    'EntryTime',
    '_unknown3',
    '_unknown4',
    '_unknown5',
    '_unknown6',
    'file_size',
    '_unknown8'
]
REG_TYPE_ENTRY_3SZ = struct.calcsize(REG_TYPE_ENTRY_3FORMAT)  # 0xA8 - 0x48

# Directory Entry Flag
DIR_ENTRY_FLAG = {
    b'\x30\x00\x02\x00' : 'Regular File',
    b'\x30\x00\x01\x00' : 'Directory',
    b'\x20\x00\x00\x80' : 'Deleted File?',
    b'\x10\x00\x00\x00' : 'Index'
}

REFS_ATTR_DATA_3FORMAT = '<6I'
REFS_ATTR_DATA_3FIELDS = [
    'LCN',
    '_unknown1',
    '_unknown2',
    '_unknown3',
    '_unknown4',
    '_unknown5'
]
REFS_ATTR_DATA_3SZ = struct.calcsize(REFS_ATTR_DATA_3FORMAT)

"""
flag = Index(0x10), Deleted?(0x20), Live?(0x30)
type = Regular file (0x1), Directory (0x2), ??? (0x8000)
"""
#TODO: 심볼릭 링크 파일, 아카이브 파일은 플래그 어떻게 나타나는지 확인하기

REFS_V3_FLAG_INDEX = 0x10
REFS_V3_FLAG_DELETED = 0x20
REFS_V3_FLAG_LIVE = 0x30

REFS_V3_TYPE_REG = 0x1
REFS_V3_TYPE_DIR = 0x2

REFS_V3_ATTR_DATA = 0x80
REFS_V3_ATTR_INDEX_ROOT = 0x90
REFS_V3_ATTR_ADS = 0xB0
