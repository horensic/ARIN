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
# import mmap
from logfile.mlog_type import *


class LogEntry:

    def __init__(self, entry, entry_type='data'):
        # self.entry = mmap.mmap(entry, length=0x1000, access=mmap.ACCESS_READ)
        self.entry = entry
        self.entry_header = self.parse_entry_header(self.entry)
        # TODO: 시그니처 검사 추가
        self.log_header = self.parse_log_header(self.entry)
        if entry_type is 'data':
            self.log_record = self.parse_log_record(self.entry)
        if entry_type is 'control':
            self.info = self.parse_log_control(self.entry)

    def __del__(self):
        self._end()

    def __repr__(self):
        return "LogEntry"

    def _end(self):
        # TODO: 파일의 경우 closed 검사를 하는 것이므로 수정이 필요
        if self.entry.closed is False:
            self.entry.close()

    def parse_entry_header(self, entry):
        buf = entry.read(REFS_ENTRY_HDR_SZ)
        return dict(zip(REFS_ENTRY_HDR_FIELDS, struct.unpack(REFS_ENTRY_HDR_FORMAT, buf)))

    def parse_log_header(self, entry):
        buf = entry.read(REFS_LOG_HDR_SZ)
        return dict(zip(REFS_LOG_HDR_FIELDS, struct.unpack(REFS_LOG_HDR_FORMAT, buf)))

    def parse_log_record(self, entry):
        log_record = []
        record_buf = io.BytesIO(entry.read(self.log_header['data_size']))

        while(True):
            record_size, flag = struct.unpack('<2I', record_buf.read(8))
            if record_size == 0x0:
                break
            record = record_buf.read(record_size)
            log_record.append(RedoRecord(record, record_size))

        return log_record

    def parse_log_control(self, entry):
        buf = entry.read(0x50)
        return dict(zip(REFS_LOG_CTRL_INFO_FIELDS, struct.unpack(REFS_LOG_CTRL_INFO_FORMAT, buf)))


class RedoRecord:

    def __init__(self, buf, size):
        self.buf = io.BytesIO(buf)
        self.size = size
        self.txc = self.parse_tx_context()

    def __repr__(self):
        return "RedoRecord"

    def parse_tx_context(self):
        txc = []

        while(True):
            temp = self.buf.tell()
            if temp == self.size:
                break
            tx_context_size = struct.unpack('<I', self.buf.read(4))[0]
            self.buf.seek(temp)
            tx_context_buf = self.buf.read(tx_context_size)
            txc.append(TransactionContext(tx_context_buf))

        return txc


class TransactionContext:

    def __init__(self, buf):
        self.buf = io.BytesIO(buf)
        self.header = self.parse_header()
        self.transaction = self.parse_transaction()

    def __repr__(self):
        return "TransactionContext"

    def parse_header(self):
        return dict(zip(REFS_REDO_REC_HDR_FIELDS, struct.unpack(REFS_REDO_REC_HDR_FORMAT, self.buf.read(REFS_REDO_REC_HDR_SZ))))

    def parse_transaction(self):
        transaction = []
        tail_offset, tail_size = struct.unpack('<2I', self.buf.read(8))
        next_rp = self.buf.tell()  # read point

        while (True):

            if next_rp == 0:
                break
            if next_rp == tail_offset:
                break
            offset, size = struct.unpack('<2I', self.buf.read(8))
            next_rp = self.buf.tell()

            self.buf.seek(offset)
            transaction.append(self.buf.read(size))
            self.buf.seek(next_rp)

        self.buf.seek(tail_offset)
        tail = self.buf.read(tail_size)
        transaction.insert(0, tail)

        return transaction
