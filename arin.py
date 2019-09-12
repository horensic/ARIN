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

import sys
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from refs.refshell_gui import ReFSGUIShell


form_class = uic.loadUiType("ARIN_form.ui")[0]


class StdoutRedirect(QObject):
    print_occur = pyqtSignal(str, str, name="print")

    def __init__(self):
        QObject.__init__(self, None)
        self.daemon = True
        self.sysstdout = sys.stdout.write
        self.sysstderr = sys.stderr.write

    def stop(self):
        sys.stdout.write = self.sysstdout
        sys.stderr.write = self.sysstderr

    def start(self):
        sys.stdout.write = self.write
        sys.stderr.write = lambda msg: self.write(msg, color='red')

    def write(self, s, color='black'):
        sys.stdout.flush()
        self.print_occur.emit(s, color)


class Arin(QMainWindow, form_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()

        self._stdout = StdoutRedirect()
        self._stdout.start()
        self._stdout.print_occur.connect(lambda x: self._debug_view(x))

        self.image_path = ''

    def initUI(self):
        self.actionOpen_Image.triggered.connect(self._open_image)
        self.pB_shell.clicked.connect(self._shell)
        self.refs_browser_root = self.refs_browser.invisibleRootItem()
        self.show()

    def _debug_view(self, msg):
        self.textBrowser.moveCursor(QTextCursor.End)
        self.textBrowser.insertPlainText(msg)
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def _open_image(self):
        self.image_path = QFileDialog.getOpenFileName(caption="Open", filter="RAW/DD Image (*.001)")[0]
        self.tE_image_path.clear()
        self.tE_image_path.insertPlainText(self.image_path)

    def _shell(self):
        if self.image_path is '':
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("ReFS 이미지 파일 오류")
            msg.setText("ReFS 이미지 파일을 지정해주십시요")
            msg.exec_()
            return
        else:
            self.sh = ReFSGUIShell(self.image_path)
            # TODO: 브라우저를 다루기 위한 별도의 클래스 정의? 디렉터리 구조 잘 보여줄 수 있도록 ReFShell 재설계 고려
            fs_meta = self._browser_item(name='File System Metadata', type='DIR')
            self._browser_insert(self.refs_browser_root, fs_meta)
            self._browser_insert(fs_meta, self.sh.refs.fs_meta)
            self._browser_insert(self.refs_browser_root, self.sh._cwd)

    def _browser_insert(self, parent, cwd):
        if isinstance(cwd, QTreeWidgetItem):
            parent.addChild(cwd)
        elif isinstance(cwd.table, dict):
            for name, metadata in cwd.table.items():
                item = QTreeWidgetItem()
                item.setText(0, name)
                if 'file_size' in metadata:
                    item.setText(1, str(metadata['file_size']))
                else:
                    item.setText(1, '')
                item.setText(2, metadata['file_type'])
                item.setText(3, 'N/A')
                item.setText(4, 'N/A')
                item.setText(5, 'N/A')
                parent.addChild(item)

    def _browser_item(self, name, type):
        item = QTreeWidgetItem()
        item.setText(0, name)
        item.setText(1, '')
        item.setText(2, type)
        item.setText(3, 'N/A')
        item.setText(4, 'N/A')
        item.setText(5, 'N/A')

        return item


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Arin()
    sys.exit(app.exec_())
