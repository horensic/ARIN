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
import mmap


class VolumeHandle:

    def __init__(self):
        self.volume = None
        self.base_offset = 0

    def __del__(self):
        self._end()

    def _end(self):
        if (self.volume is not None) and (self.volume.closed is False):
            self.volume.close()

        if hasattr(self, 'handle'):  # Load Image
            if (self.handle is not None) and (self.handle.closed is False):
                self.handle.close()

    def load_drive(self, source):
        path = '\\\\.\\' + source.split('\\')[0]
        try:
            self.volume = open(path, 'rb')
        except PermissionError:
            print("Requires administrator privileges")
            exit(-1)

    def load_image(self, source):
        # set base offset
        try:
            self.handle = open(source, 'rb')
            self.volume = mmap.mmap(self.handle.fileno(), length=0, access=mmap.ACCESS_READ)  # Read Only
        except IOError:
            exit(-1)

    def read(self, size):
        if self.volume:
            return self.volume.read(size)

    def seek(self, offset, whence=io.SEEK_SET):
        if self.volume:
            self.volume.seek(offset, whence)