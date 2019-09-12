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

import argparse
from refs.refs import ReFS
from refs.volume import VolumeHandle
import refs.logger as logger


refshell_log = logger.ArinLog("ReFShell", level=logger.LOG_DEBUG | logger.LOG_INFO)


class ReFShell:

    def __init__(self):
        self.args = None
        self.parent_dir = []
        self._cwd = None
        self._pwd = []
        self._parse_command_line()
        self._load_volume()

# private

    def _parse_command_line(self):
        parser = argparse.ArgumentParser(description='ReFShell')

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--drive', help='specify the ReFS volume, ex) E:\\\\')
        group.add_argument('--image', help='specify the ReFS image file')

        self.args = parser.parse_args()

    def _open_volume(self):

        vol = VolumeHandle()

        if self.args.drive:
            source = self.args.drive
            vol.load_drive(source)

        elif self.args.image:
            source = self.args.image
            vol.load_image(source)

        return vol

    def _load_volume(self):
        vol = self._open_volume()
        self.refs = ReFS(vol)
        self.refs.read_volume()
        self.refs.file_system_metadata()
        self.refs.logfile_info()
        if self.refs.root_dir():
            self._cwd = self.refs.root
            self._pwd.append('/')

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

    def _command_interpreter(self):

        argv = []

        while True:
            command = input(f"ReFShell {'/'.join(self._pwd)}> ")
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

    def refs_stat(self):
        print("Not yet developed...")

    def extract_file(self, filename):
        print("Not yet developed...")


if __name__ == '__main__':
    sh = ReFShell()
    sh._command_interpreter()