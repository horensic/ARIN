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

from refs.refs import ReFS
from refs.volume import VolumeHandle
import refs.logger as logger


refshell_log = logger.ArinLog("ReFS GUI Shell", level=logger.LOG_DEBUG | logger.LOG_INFO)


class ReFSGUIShell:

    def __init__(self, img):
        self.src = img
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
        self.refs.logfile_info()
        if self.refs.root_dir():
            refshell_log.info("ReFS GUI Shell is Root")
            self._cwd = self.refs.root

    def parse_logfile(self):
        return self.refs.logfile.parse_logfile()

    def extract_chgjrnl(self):
        pass