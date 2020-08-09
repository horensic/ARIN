# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
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