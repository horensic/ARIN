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
import struct
from datetime import datetime, timedelta
from logfile.mlog_type import *


class PDALogRecord:

    FILE_CREATE = [0x1, 0x4, 0x10, 0x0, 0x4, 0x1, 0x0]
    FILE_DELETE = [0xF, 0x2, 0xF, 0x2]
    FILE_ALLOCATE = [0x6, 0x4]
    FILE_FREE = [0x7, 0x4]

    DIR_CREATE = [0x0, 0x0, 0x4, 0x10, 0x1, 0x1, 0x1, 0xE]
    DIR_DELETE = [0x2, 0xF, 0x2, 0xF]

    def __init__(self, record, opcode):
        self.record = record
        self.opcode = opcode

    def recognize_context(self):
        raise NotImplementedError

    def recognize_operation(self):
        raise NotImplementedError

    def parse_transaction(self, txc):
        raise NotImplementedError


class TransactionParser:

    def __init__(self, redo):
        key_count = redo.header['tablekeys_count']
        value_count = redo.header['value_count']
        # print(f"Update Data <key count: {key_count}, value count: {value_count}>")

        obj_info = self.check_object(redo.transaction[0])
        # print(hex(obj_info['obj_type']), hex(obj_info['obj_id']))

        if obj_info['obj_type'] == 0x130:
            key_var = ['obj_info', 'name', 'attr']
            key_func = [self.check_object, self.parse_name, self.parse_attr]

            value_var = ['timestamp']
            value_func = [self.parse_timestamp]

            if key_count > 0 and key_count <= 3:
                for i in range(key_count):
                    setattr(self, key_var[i], key_func[i](redo.transaction[i]))

            if value_count > 0 and value_count < 2:
                for i in range(value_count):
                    setattr(self, value_var[i], value_func[i](redo.transaction[key_count+i]))

        elif obj_info['obj_type'] == 0x140:
            raise NotImplementedError

        elif obj_info['obj_type'] == 0x150:
            raise NotImplementedError

        elif obj_info['obj_type'] == 0x180:
            raise NotImplementedError

        else:
            raise NotImplementedError

    def check_object(self, buf):
        obj_info = dict(zip(REFS_TX_TARGET_KEY_FIELDS, struct.unpack(REFS_TX_TARGET_KEY_FORMAT, buf)))
        return obj_info

    def parse_index_name(self, buf):
        raise NotImplementedError

    def parse_name(self, buf):
        if len(buf) == 0x10:
            return 'Current Directory Index'
        name_buf = io.BytesIO(buf)
        file_rec_key = dict(zip(REFS_FILE_REC_KEY_FIELDS, struct.unpack(REFS_FILE_REC_KEY_FORMAT, name_buf.read(0x10))))
        name = name_buf.read().decode('utf-16')
        return name

    def parse_attr(self, buf):
        pass

    def parse_timestamp(self, buf):

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

        timestamp = []

        tx_data = io.BytesIO(buf)
        for _ in range(4):
            ts = win64le(struct.unpack('<Q', tx_data.read(8))[0])
            timestamp.append(ts)

        return timestamp

    def parse_lcn(self, buf):
        tx_data = io.BytesIO(buf)
        lcn = struct.unpack('<I', tx_data.read(4))[0]
        return lcn


class ContextAnalyzer:

    def __init__(self):
        self.record = []
        self.opcode = []

    def read_context(self, txc):
        start = False
        if txc.header['rec_mark'] == 0x0:
            self.record.append(txc)
            self.opcode.append(txc.header['opcode'])
        else:
            if txc.header['rec_mark'] & 0x1:  # Transaction Start
                self.record.append(txc)
                self.opcode.append(txc.header['opcode'])
                start = True

            if txc.header['rec_mark'] & 0x2:  # Transaction End
                if not start:
                    self.record.append(txc)
                    self.opcode.append(txc.header['opcode'])
                # raise NotImplementedError
                refs_op = self.preprocess_context()
                self.record = []
                self.opcode = []
                return refs_op

            if txc.header['rec_mark'] & 0x4:  # Unknown
                if not start:  # Transaction Start와 함께 쓰인 경우가 아니라면 추가
                    self.record.append(txc)
                    self.opcode.append(txc.header['opcode'])

    def preprocess_context(self):

        if len(self.opcode) > 1:  # Multiple Transaction Context
            PDALogRecord(self.record, self.opcode)
        else:  # Single Transaction Context
            TransactionParser(self.record[0])
