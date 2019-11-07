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
from logfile.mlog_type import *


class PDALogRecord:

    P_FILE_CREATE = [0x1, 0x4, 0x10, 0x0, 0x4, 0x1, 0x0]
    P_FILE_DELETE = [0xF, 0x2, 0xF, 0x2]
    p_FILE_RENAME = [0x2, 0x5, 0x1]
    P_FILE_MOVE_1 = [0x2, 0x5, 0x1, 0x4, 0x10, 0x4, 0x1]
    P_FILE_MOVE_2 = [0x2, 0x5, 0x2, 0x4, 0x1]
    P_FILE_MOVE_3 = [0x2, 0x5, 0x2, 0x1, 0x4, 0x10, 0x4, 0x1, 0x4]
    P_FILE_ALLOCATE = [0x6, 0x4]
    P_FILE_FREE = [0x7, 0x4]

    P_DIR_CREATE = [0x0, 0x0, 0x4, 0x10, 0x1, 0x1, 0x1, 0xE]
    P_DIR_DELETE = [0x2, 0xF, 0x2, 0xF]

    P_META_UPDATE = [0x3, 0x3]

    def __init__(self, record, opcode):
        self.record = record
        self.opcode = opcode

    def recognize_context(self):
        for key in dir(self):
            if key.startswith('P'):
                if self.opcode == getattr(self, key):
                    print("Match: ", key)
                    # self.parse_transaction(self.record)
                    break
        else:
            print("Not Match: ", self.opcode)
            # self.recognize_operation()

    def recognize_operation(self):
        raise NotImplementedError

    def parse_transaction(self, txc):
        raise NotImplementedError


class TransactionDataParser:

    def __init__(self):
        pass

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

    def parse_fileid(self, buf):
        pass

    def parse_lcn(self, buf):
        tx_data = io.BytesIO(buf)
        lcn = struct.unpack('<I', tx_data.read(4))[0]
        return lcn


class TransactionParser(TransactionDataParser):

    def __init__(self, redo_tx):
        super(TransactionDataParser, self).__init__()
        self.opcode = redo_tx.header['opcode']
        key_count = redo_tx.header['tablekeys_count']
        value_count = redo_tx.header['value_count']

        REDO_OP_DISPATCH_TABLE = {
            0x0: self.open_table,
            0x1: self.redo_insert_row,
            0x2: self.redo_delete_row,
            0x3: self.redo_update_row,
            0x4: self.redo_update_data_with_root,
            0x5: self.redo_reparent_table,
            0x6: self.redo_allocate,
            0x7: self.redo_free,
            0x8: self.redo_set_range_state,
            0xD: self.redo_set_integrity,
            0xE: self.redo_set_parent_id,
            0xF: self.redo_delete_table,
            0x10: self.redo_value_as_key
        }

        REDO_OP_DISPATCH_TABLE[self.opcode](redo_tx, key_count, value_count)

    # Opcode = 0x0
    def open_table(self, redo_tx, key_count, value_count):
        if key_count > 0:
            key_var = ['obj_info', 'name', 'attr']
            key_func = [self.check_object, self.parse_name, self.parse_attr]
            for i in range(key_count):
                setattr(self, key_var[i], key_func[i](redo_tx.transaction[i]))
        else:
            raise NotImplementedError

    # Opcode = 0x1
    def redo_insert_row(self, redo_tx, key_count, value_count):
        if key_count > 0:
            key_var = ['obj_info', 'name', 'attr']
            key_func = [self.check_object, self.parse_name, self.parse_attr]
            for i in range(key_count):
                setattr(self, key_var[i], key_func[i](redo_tx.transaction[i]))
        else:
            # raise NotImplementedError
            pass

    # Opcode = 0x2
    def redo_delete_row(self, redo_tx, key_count, value_count):
        pass

    # Opcode = 0x3
    def redo_update_row(self, redo_tx, key_count, value_count):
        if key_count > 0:
            key_var = ['obj_info', 'name', 'attr']
            key_func = [self.check_object, self.parse_name, self.parse_attr]
            for i in range(key_count):
                setattr(self, key_var[i], key_func[i](redo_tx.transaction[i]))
        else:
            raise NotImplementedError

    # Opcode = 0x4
    def redo_update_data_with_root(self, redo_tx, key_count, value_count):
        if key_count > 0:
            key_var = ['obj_info', 'name', 'attr']
            key_func = [self.check_object, self.parse_name, self.parse_attr]

            for i in range(key_count):
                setattr(self, key_var[i], key_func[i](redo_tx.transaction[i]))

            if value_count == 1:
                self.parse_timestamp(redo_tx.transaction[key_count])
            elif value_count == 2:
                self.parse_fileid(redo_tx.transaction[key_count])
                # TODO: self.parse_~~~(redo_tx.transaction[key_count+1])
                pass
        else:
            if value_count == 1:
                self.parse_timestamp(redo_tx.transaction[key_count])
            elif value_count == 2:
                # raise NotImplementedError
                pass
            else:
                raise NotImplementedError

    # Opcode = 0x5
    def redo_reparent_table(self, redo_tx, key_count, value_count):
        pass

    # Opcode = 0x6
    def redo_allocate(self, redo_tx, key_count, value_count):
        raise NotImplementedError

    # Opcode = 0x7
    def redo_free(self, redo_tx, key_count, value_count):
        raise NotImplementedError

    # Opcode = 0x8
    def redo_set_range_state(self, redo_tx, key_count, value_count):
        if key_count > 0:
            key_var = ['obj_info', 'name', 'attr']
            key_func = [self.check_object, self.parse_name, self.parse_attr]

            for i in range(key_count):
                setattr(self, key_var[i], key_func[i](redo_tx.transaction[i]))

            if value_count == 1:
                # TODO: self.parse_~~~(redo_tx.transaction[key_count])
                pass
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    # Opcode = 0xD
    def redo_set_integrity(self, redo_tx, key_count, value_count):
        pass

    # Opcode = 0xE
    def redo_set_parent_id(self, redo_tx, key_count, value_count):
        pass

    # Opcode = 0xF
    def redo_delete_table(self, redo_tx, key_count, value_count):
        pass

    # Opcode = 0x10
    def redo_value_as_key(self, redo_tx, key_count, value_count):
        pass


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
                self.preprocess_context()
                self.record = []
                self.opcode = []

            if txc.header['rec_mark'] & 0x4:  # Unknown
                if not start:  # Transaction Start와 함께 쓰인 경우가 아니라면 추가
                    self.record.append(txc)
                    self.opcode.append(txc.header['opcode'])

    def preprocess_context(self):

        if len(self.opcode) > 1:  # Multiple Transaction Context
            pda = PDALogRecord(self.record, self.opcode)
            pda.recognize_context()
        else:  # Single Transaction Context
            context = TransactionParser(self.record[0])
            print(f"Context <Opcode: {hex(context.opcode)}, ObjID: {hex(context.obj_info['obj_id'])}>")
            # print(self.opcode)