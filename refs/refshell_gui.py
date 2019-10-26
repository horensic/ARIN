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
from PyQt5.QtCore import QThread, pyqtSignal
from refs.refs import ReFS
from refs.volume import VolumeHandle
from refs.refs_type import REDO_OP
import refs.logger as logger
from logfile.logfile import LogEntry
from logfile.logfile_pda import PDALogfile
from logfile.error import *
from chgjrnl.change_journal import USNRecordV3


refshell_log = logger.ArinLog("ReFS GUI Shell", level=logger.LOG_DEBUG | logger.LOG_INFO)


class ThreadLogfile(QThread):

    progress_value = pyqtSignal(int)
    logfile_record = pyqtSignal(dict)

    def __init__(self, log_data):
        super().__init__()
        self.log_data = log_data

    def __del__(self):
        self.wait()

    def run(self):

        def check_overwritten(buf):
            flag = False
            ward = buf.tell()
            if buf.read(4) == b'MLog':
                flag = True
            buf.seek(ward)
            return flag

        log_data = io.BytesIO(self.log_data)
        log_data.seek(0x1000 * 2)  # skip control area entry
        overwritten = check_overwritten(log_data)
        if not overwritten:
            log_data.read(0x1000)  # HACK

        cnt = 0
        prog_v = 0
        pda = PDALogfile()

        while True:
            refshell_log.trace(f"Entry Offset: {hex(log_data.tell())}")
            buf = log_data.read(0x1000)
            if not buf:
                break
            entry_buf = io.BytesIO(buf)
            try:
                log_entry = LogEntry(entry_buf)
            except InvalidLogEntrySignatureError:
                if not overwritten:
                    self.progress_value.emit(100)  # Complete
                    break
                else:
                    exit(-2)
            else:
                cnt += 1
                if cnt % 0x400 == 0:
                    prog_v += 1
                    self.progress_value.emit(prog_v)
                lsn = log_entry.entry_header['current_ml_lsn']

                for redo_record in log_entry.log_record:
                    for tx in redo_record.txc:
                        record = dict()
                        record['lsn'] = hex(lsn)
                        record['event'] = ''
                        record['tx_time'] = ''
                        record['opcode'] = REDO_OP[tx.header['opcode']]
                        record['rec_mark'] = hex(tx.header['rec_mark'])
                        record['seq_no'] = hex(tx.header['seq_no'])
                        record['end_mark'] = hex(tx.header['end_mark'])
                        record['filename'] = ''
                        record['ctime'] = ''
                        record['mtime'] = ''
                        record['chtime'] = ''
                        record['atime'] = ''
                        record['lcn'] = ''
                        self.logfile_record.emit(record)
                        op_info = pda.transit(tx)
                        if op_info:
                            event_record = dict()
                            event_record['lsn'] = ''
                            event_record['event'] = op_info['event']
                            event_record['tx_time'] = op_info['tx_time']
                            event_record['opcode'] = ''
                            event_record['rec_mark'] = ''
                            event_record['seq_no'] = ''
                            event_record['end_mark'] = ''
                            event_record['filename'] = op_info['filename']
                            event_record['ctime'] = op_info['timestamp'][0]
                            event_record['mtime'] = op_info['timestamp'][1]
                            event_record['chtime'] = op_info['timestamp'][2]
                            event_record['atime'] = op_info['timestamp'][3]
                            event_record['lcn'] = op_info['file_lcn']
                            self.logfile_record.emit(event_record)


class ThreadChgjrnl(QThread):

    progress_value = pyqtSignal(int)
    chgjrnl_record = pyqtSignal(dict)

    def __init__(self, chgjnrl_data):
        super().__init__()
        self.chgjrnl_data = chgjnrl_data

    def run(self):

        jrnl_data = io.BytesIO(self.chgjrnl_data)

        while True:
            ward = jrnl_data.tell()
            prog_v = ward / 0x200
            if prog_v > 0:
                self.progress_value.emit(prog_v)
            rec_len = struct.unpack('<I', jrnl_data.read(4))[0]
            if rec_len == 0 or not rec_len:
                self.progress_value.emit(100)
                break
            jrnl_data.seek(ward)
            jrnl_rec = USNRecordV3(jrnl_data.read(rec_len))

            record = dict()
            record['usn'] = jrnl_rec.record['usn']
            record['timestamp'] = jrnl_rec.record['timestamp']
            record['name'] = jrnl_rec.record['name']
            record['reason'] = jrnl_rec.record['reason']
            record['source_info'] = jrnl_rec.record['source_info']
            record['file_attribute'] = jrnl_rec.record['file_attribute']
            record['file_ref_no'] = jrnl_rec.record['file_reference_number']
            record['parent_ref_no'] = jrnl_rec.record['parent_file_reference_number']
            self.chgjrnl_record.emit(record)


class ReFSGUIShell:

    def __init__(self, img):
        self.src = img
        self.parent_dir = []
        self._cwd = None
        self._pwd = []
        self._load_volume()

    def _open_volume(self):
        vol = VolumeHandle()
        vol.load_image(self.src)
        return vol

    def _load_volume(self):
        vol = self._open_volume()
        self.refs = ReFS(vol)
        self.refs.read_volume()
        self.refs.file_system_metadata()
        if self.refs.chgjrnl_info():
            refshell_log.info("ReFS Change Journal")
        if self.refs.logfile_info():
            refshell_log.info("ReFS Logfile")

        if self.refs.root_dir():
            refshell_log.info("ReFS GUI Shell is Root")
            self._cwd = self.refs.root
            self._pwd.append('/')

    def get_log_info(self):
        if self.refs.logfile_information:
            return self.refs.logfile_information.children_table[0].table[1]

    def parse_logfile(self, logfile=None):
        if logfile:
            ret = None
        else:
            ret = self.refs.logfile.parse_logfile()
        return ret

    def parse_chgjrnl(self, chgjrnl=None):
        if self.refs.change_journal is not None:
            return self.refs.change_journal.parse_chgjrnl()
        else:
            return None

    def _view(self, buf, ofs=0):
        offset = ofs

        while True:
            data = buf[:16]
            buf = buf[16:]
            ldata = len(data)

            if ldata == 0:
                break

            output = '{0:08X} : '.format(offset)

            for i in range(ldata):
                output += '{0:02X} '.format(data[i])

            if ldata != 16:
                for i in range(16 - ldata):
                    output += '{0:2s}'.format('   ')

            for i in range(ldata):
                if (data[i]) >= 0x20 and (data[i]) <= 0x7E:
                    output += '{0:s}'.format(chr(data[i]))
                else:
                    output += '{0:s}'.format('.')

            print(output)
            offset += 16

    def _gui_command_interpreter(self, command):

        argv = []

        print(f"ReFShell {'/'.join(self._pwd)}> {command}")
        refshell_log.trace("command: {0}".format(command))

        if command == 'exit':
            self.refs.vol._end()
            exit(0)

        for arg in command.split(' '):
            argv.append(arg)
        refshell_log.trace("argv: {0}".format(argv))

        method = argv[0]
        refshell_log.trace("method: {0}".format(method))

        if hasattr(self, method):
            func = getattr(self, method)
            nargs = func.__code__.co_argcount - 1
            if nargs:
                args = argv[1:]
                if len(args) == nargs:
                    func(*args)
                elif len(args) > nargs:
                    func(' '.join(args))
            else:
                func()
        else:
            print("{cmd}: command not found".format(cmd=method))

    def _command_interpreter(self, command):

        argv = []

        while True:
            # command = input(f"ReFShell {'/'.join(self._pwd)}> ")
            refshell_log.trace("command: {0}".format(command))

            if command == 'exit':
                self.refs.vol._end()
                exit(0)

            for arg in command.split(' '):
                argv.append(arg)
            refshell_log.trace("argv: {0}".format(argv))

            method = argv[0]
            refshell_log.trace("method: {0}".format(method))

            if hasattr(self, method):
                func = getattr(self, method)
                nargs = func.__code__.co_argcount - 1
                if nargs:
                    args = argv[1:]
                    if len(args) == nargs:
                        func(*args)
                    elif len(args) > nargs:
                        func(' '.join(args))
                else:
                    func()
            else:
                print("{cmd}: command not found".format(cmd=method))

            argv = []

# public

    def help(self):
        for method in dir(self):
            if not method.startswith('_') and method != 'help':
                func = getattr(self, method)
                if hasattr(func, '__code__'):
                    argcount = func.__code__.co_argcount
                    args = ', '.join(['<{0}>'.format(a.upper()) for a in func.__code__.co_varnames[1:argcount]])
                    print(" {name} {arg}".format(name=method, arg=args))

    def cd(self, directory):
        if directory == '..':
            if self._pwd[-1] == '/':
                pass
            else:
                self._cwd = self.parent_dir.pop()
                self._pwd.pop()

        elif directory == '/':
            if self._pwd[-1] == '/':
                pass
            else:
                self._cwd = self.refs.root
                self._pwd = ['/']

        else:
            try:
                oid = self._cwd.table[directory]['object_id']
            except KeyError:
                print(f"cd: {directory}: No such file or directory")
            else:
                self.parent_dir.append(self._cwd)
                self._pwd.append(directory)
                dir_obj = self.refs.object_table.table[oid]
                self._cwd = self.refs.change_directory(dir_obj)

    def ls(self):
        self._cwd.ls()

    def pwd(self):
        print('/'.join(self._pwd))

    def cat(self, filename):
        try:
            metadata = self._cwd.table[filename]
        except KeyError:
            print(f"cat: {filename}: No such file or directory")
        else:
            if metadata['file_type'] == 'REG':
                file_data = self.refs.read_file(metadata)
                for data in file_data:
                    self._view(data, 0)
                    print()
            else:
                print(f"cat: {filename} is directory")

    def translate_lcn(self, LCN):
        lcn = int(LCN)
        LCNTuple = [lcn, lcn+1, lcn+2, lcn+3]
        print(self.refs.translate_lcn(LCNTuple))
        return self.refs.translate_lcn(LCNTuple)[0]

    def refs_stat(self):
        print("Not yet developed...")

    def extract_file(self, filename):
        print("Not yet developed...")