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

import os, sys
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
        self.sh = None

    def initUI(self):
        # Open Image
        self.actionOpen_Image.triggered.connect(self._open_image)
        self.tbt_open_image.clicked.connect(self._open_image)
        # Image Parsing
        self.pb_shell.clicked.connect(self._shell)
        self.refs_browser_root = self.refs_browser.invisibleRootItem()
        self.refs_browser.itemClicked.connect(self._click_shell_item)
        # Logfile
        self.actionExtract_Logfile.triggered.connect(self._extract_logfile)
        self.pb_logfile_parse.clicked.connect(self._parse_logfile)
        # Change Journal
        self.actionExtract_Change_Journal.triggered.connect(self._extract_chgjrnl)
        self.pb_chgjrnl_parse.clicked.connect(self._parse_chgjrnl)
        # shell
        self.pb_sh_cmd.clicked.connect(self._shell_cmd)

        self.show()

    def _debug_view(self, msg):
        self.debug_view.moveCursor(QTextCursor.End)
        self.debug_view.insertPlainText(msg)
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def _open_image(self):
        self.image_path = QFileDialog.getOpenFileName(self, caption="Open", filter="RAW/DD Image (*.001)")[0]
        self.pte_image_path.clear()
        self.pte_image_path.insertPlainText(self.image_path)

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
            # Logfile & ChgJrnl
            self.pte_logfile.insertPlainText('Logfile')
            self.pte_chgjrnl.insertPlainText('File System Metadata/Change Journal')
            # TODO: 브라우저를 다루기 위한 별도의 클래스 정의? 디렉터리 구조 잘 보여줄 수 있도록 ReFShell 재설계 고려
            fs_meta = self._browser_item(name='File System Metadata', type='DIR')
            self._browser_insert(self.refs_browser_root, fs_meta)
            self._browser_insert(fs_meta, self.sh.refs.fs_meta)
            self._browser_insert(self.refs_browser_root, self.sh._cwd)

    def _shell_cmd(self):
        if self.sh is None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("ReFS 이미지 오류")
            msg.setText("ReFS 이미지를 먼저 분석해주세요")
            msg.exec_()
            return
        else:
            lcn = int(self.sh_cmd.text())
            self.sh.translate_lcn(lcn)

    @pyqtSlot(QTreeWidgetItem, int)
    def _click_shell_item(self, it, col):
        print(it, col, it.text(col))


    def _extract_logfile(self):
        if self.sh is None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("ReFS 이미지 오류")
            msg.setText("ReFS 이미지를 먼저 분석해주세요")
            msg.exec_()
            return
        else:
            path = QFileDialog.getExistingDirectory(self, caption="Logfile Save")
            logfile_name = os.path.join(path, 'Logfile')
            with open(logfile_name, 'wb') as logfile:
                logfile.write(self.sh.refs.logfile.log_data)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Logfile 추출 완료")
            msg.setText("ReFS 이미지에서 Logfile 추출을 완료하였습니다")
            msg.exec_()

    def _extract_chgjrnl(self):
        if self.sh is None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("ReFS 이미지 오류")
            msg.setText("ReFS 이미지를 먼저 분석해주세요")
            msg.exec_()
            return
        else:
            path = QFileDialog.getExistingDirectory(self, caption="Change Journal Save")
            chgjrnl_name = os.path.join(path, 'Change Journal')
            with open(chgjrnl_name, 'wb') as chgjrnl:
                chgjrnl.write(self.sh.refs.change_journal.chgjrnl_data)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Change Journal 추출 완료")
            msg.setText("ReFS 이미지에서 Change Journal 추출을 완료하였습니다")
            msg.exec_()

    def _parse_logfile(self):
        if self.sh is None:
            return
        else:
            self.tb_logfile.setRowCount(0)

            records = self.sh.parse_logfile()
            for record in records:
                row_pos = self.tb_logfile.rowCount()
                self.tb_logfile.insertRow(row_pos)
                self.tb_logfile.setItem(row_pos, 0, QTableWidgetItem(hex(record['lsn'])))
                self.tb_logfile.setItem(row_pos, 1, QTableWidgetItem('N/A'))
                self.tb_logfile.setItem(row_pos, 2, QTableWidgetItem('N/A'))
                self.tb_logfile.setItem(row_pos, 3, QTableWidgetItem(record['opcode']))
                self.tb_logfile.setItem(row_pos, 4, QTableWidgetItem(hex(record['rec_mark'])))
                self.tb_logfile.setItem(row_pos, 5, QTableWidgetItem(hex(record['seq_no'])))
                self.tb_logfile.setItem(row_pos, 6, QTableWidgetItem(hex(record['end_mark'])))
                self.tb_logfile.setItem(row_pos, 7, QTableWidgetItem('N/A'))

    def _parse_chgjrnl(self):
        if self.sh is None:
            return
        else:
            self.tb_chgjrnl.setRowCount(0)

            records = self.sh.parse_chgjrnl()
            for record in records:
                row_pos = self.tb_chgjrnl.rowCount()
                self.tb_chgjrnl.insertRow(row_pos)
                self.tb_chgjrnl.setItem(row_pos, 0, QTableWidgetItem(hex(record['usn'])))
                self.tb_chgjrnl.setItem(row_pos, 1, QTableWidgetItem(str(record['timestamp'])))
                self.tb_chgjrnl.setItem(row_pos, 2, QTableWidgetItem(record['name']))
                self.tb_chgjrnl.setItem(row_pos, 3, QTableWidgetItem(hex(record['reason'])))
                self.tb_chgjrnl.setItem(row_pos, 4, QTableWidgetItem(hex(record['source_info'])))
                self.tb_chgjrnl.setItem(row_pos, 5, QTableWidgetItem(hex(record['file_attribute'])))
                self.tb_chgjrnl.setItem(row_pos, 6, QTableWidgetItem('N/A'))# hex(record['file_ref_no'])))
                self.tb_chgjrnl.setItem(row_pos, 7, QTableWidgetItem('N/A'))# hex(record['parent_ref_no'])))

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
