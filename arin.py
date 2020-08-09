# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
@contact:   horensic@gmail.com
"""

import os, sys
from datetime import datetime
import csv, sqlite3
from PyQt5 import uic
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QObject, QCoreApplication, QEventLoop, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QMainWindow, QDialog, QApplication, QProgressDialog
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTreeWidgetItem, QTableWidgetItem
from refs.refshell_gui import ReFSGUIShell, ThreadLogfile, ThreadChgjrnl


form_class = uic.loadUiType("resources/ARIN_form.ui")[0]
about_form = uic.loadUiType("resources/About_form.ui")[0]
progress_form = uic.loadUiType("resources/Progress_form.ui")[0]


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


class About(QDialog, about_form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)


class ProgressBar(QDialog, progress_form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    @pyqtSlot(int)
    def exit(self, prog_v):
        if prog_v == 100:
            self.close()


class Arin(QMainWindow, form_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()

        # self._stdout = StdoutRedirect()
        # self._stdout.start()
        # self._stdout.print_occur.connect(lambda x: self._debug_view(x))

        self.image_path = ''
        self.logfile_path = ''
        self.chgjrnl_path = ''
        self.sh = None

    def initUI(self):
        # Exit
        self.actionExit.triggered.connect(QCoreApplication.instance().quit)
        # Open Image
        self.actionOpen_Image.triggered.connect(self._open_image)
        self.tbt_open_image.clicked.connect(self._open_image)
        # Open Drive
        self.actionOpen_Drive.triggered.connect(self._open_drive)
        # Export CSV
        self.actionCSV.triggered.connect(self._export_csv)
        # Export SQLite
        self.actionSQLite.triggered.connect(self._export_sqlite)
        # Image Parsing
        self.pb_shell.clicked.connect(self._shell)
        # [DFC] self.refs_browser_root = self.refs_browser.invisibleRootItem()
        # [DFC] self.refs_browser.itemClicked.connect(self._click_shell_item)
        # Logfile
        self.actionExtract_Logfile.triggered.connect(self._extract_logfile)
        self.tbt_open_logfile.clicked.connect(self._open_logfile)
        self.pb_logfile_parse.clicked.connect(self._parse_logfile)
        # Change Journal
        self.actionExtract_Change_Journal.triggered.connect(self._extract_chgjrnl)
        self.tbt_open_chgjrnl.clicked.connect(self._open_chgjrnl)
        self.pb_chgjrnl_parse.clicked.connect(self._parse_chgjrnl)
        # shell
        self.pb_sh_cmd.clicked.connect(self._shell_cmd)
        # About
        self.actionAbout.triggered.connect(self._about)

        self.show()

    def closeEvent(self, event):
        # 딱히 필요 없을 것 같으면 삭제하기
        self.deleteLater()

    def message_box(self, title, text, icon=QMessageBox.Warning):
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec_()
        return

    def _about(self):
        about_dlg = About()
        about_dlg.exec_()

    def _debug_view(self, msg):
        self.debug_view.moveCursor(QTextCursor.End)
        self.debug_view.insertPlainText(msg)
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def _open_drive(self):
        self.drive = QFileDialog.getExistingDirectory(self, caption="Open Drive", dir='/')[0]
        self.pte_image_path.clear()
        self.pte_image_path.insertPlainText(self.drive)

    def _open_image(self):
        self.image_path = QFileDialog.getOpenFileName(self, caption="Open Image", filter="RAW/DD Image (*.001)")[0]
        self.pte_image_path.clear()
        self.pte_image_path.insertPlainText(self.image_path)

    def _open_logfile(self):
        self.logfile_path = QFileDialog.getOpenFileName(self, caption="Open Logfile")[0]
        self.pte_logfile.clear()
        self.pte_logfile.insertPlainText(self.logfile_path)

    def _open_chgjrnl(self):
        self.chgjrnl_path = QFileDialog.getOpenFileName(self, caption="Open Change Journal")[0]
        self.pte_chgjrnl.clear()
        self.pte_chgjrnl.insertPlainText(self.chgjrnl_path)

    def _shell(self):
        if self.image_path is '':
            self.message_box(title="ReFS 이미지 파일 오류",
                             text="ReFS 이미지 파일을 지정해주십시요")
            return
        else:
            self.sh = ReFSGUIShell(self.image_path)
            # Logfile & ChgJrnl
            self.pte_logfile.clear()
            self.pte_chgjrnl.clear()
            self.tw_loginfo.clear()
            self.tb_logfile.setRowCount(0)
            self.tb_chgjrnl.setRowCount(0)

            if self.sh.refs.logfile:
                self.pte_logfile.insertPlainText('Logfile')
            if self.sh.refs.change_journal:
                self.pte_chgjrnl.insertPlainText('File System Metadata/Change Journal')
            log_info = self.sh.get_log_info()
            self._enter_detail_logfile_info(log_info)

    def _shell_cmd(self):
        if self.sh is None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("ReFS 이미지 오류")
            msg.setText("ReFS 이미지를 먼저 분석해주세요")
            msg.exec_()
            return
        else:
            # lcn = int(self.sh_cmd.text())
            # self.sh.translate_lcn(lcn)
            command = self.sh_cmd.text()
            self.sh._gui_command_interpreter(command)
            self.sh_cmd.clear()

    @pyqtSlot(QTreeWidgetItem, int)
    def _click_shell_item(self, it, col):
        # Browser 기능 확장을 위한 함수
        print(it, col, it.text(col))

    def _enter_detail_logfile_info(self, info):
        self.tw_loginfo.clear()
        for k, v in info.items():
            item = QTreeWidgetItem(self.tw_loginfo)
            item.setText(0, k)
            item.setText(1, hex(v))

    def _extract_logfile(self):
        if self.sh is None:
            self.message_box(title="ReFS 이미지 오류",
                             text="ReFS 이미지를 먼저 분석해주세요")
            return
        else:
            path = QFileDialog.getExistingDirectory(self, caption="Logfile Save")
            if not path:
                return
            logfile_name = os.path.join(path, 'Logfile')
            with open(logfile_name, 'wb') as logfile:
                logfile.write(self.sh.refs.logfile.log_data)
            self.message_box(title="Logfile 추출 완료",
                             text="ReFS 이미지에서 Logfile 추출을 완료하였습니다",
                             icon=QMessageBox.Information)

    def _extract_chgjrnl(self):
        if self.sh is None:
            self.message_box(title="ReFS 이미지 오류",
                             text="ReFS 이미지를 먼저 분석해주세요")
            return
        else:
            if self.sh.refs.change_journal:
                path = QFileDialog.getExistingDirectory(self, caption="Change Journal Save")
                if not path:
                    return
                chgjrnl_name = os.path.join(path, 'Change Journal')
                with open(chgjrnl_name, 'wb') as chgjrnl:
                    chgjrnl.write(self.sh.refs.change_journal.chgjrnl_data)
                self.message_box(title="Change Journal 추출 완료",
                                 text="ReFS 이미지에서 Change Journal 추출을 완료하였습니다",
                                 icon=QMessageBox.Information)
            else:
                self.message_box(title="Change Journal 오류",
                                 text="ReFS 이미지 내 Change Journal 파일이 존재하지 않습니다")

    def _parse_logfile(self):
        if self.sh is None:
            if not self.logfile_path:
                self.message_box(title="Logfile 오류",
                                 text="Logfile 파일을 먼저 지정해주세요")
                return
            else:
                self.tb_logfile.setRowCount(0)
                with open(self.logfile_path, 'rb') as logfile:
                    log_data = logfile.read()
                    thread = ThreadLogfile(log_data)
                    progress_dlg = ProgressBar()
                    progress_dlg.setWindowTitle("Please Wait..")
                    progress_dlg.pgb_label.setText("Parsing Logfile ...")
                    thread.progress_value.connect(progress_dlg.pgb.setValue)
                    thread.progress_value.connect(progress_dlg.exit)
                    thread.logfile_record.connect(self._insert_logfile_tb)
                    thread.start()
                    progress_dlg.exec_()
        else:
            # 별도의 Thread Parsing을 처리해줘야 함?
            self.tb_logfile.setRowCount(0)
            thread = ThreadLogfile(self.sh.refs.logfile.log_data)
            progress_dlg = ProgressBar()
            progress_dlg.setWindowTitle("Please Wait..")
            progress_dlg.pgb_label.setText("Parsing Logfile ...")
            thread.progress_value.connect(progress_dlg.pgb.setValue)
            thread.progress_value.connect(progress_dlg.exit)
            thread.logfile_record.connect(self._insert_logfile_tb)
            thread.start()
            progress_dlg.exec_()

    @pyqtSlot(dict)
    def _insert_logfile_tb(self, record):
        row_pos = self.tb_logfile.rowCount()
        self.tb_logfile.insertRow(row_pos)
        self.tb_logfile.setItem(row_pos, 0, QTableWidgetItem(record['lsn']))
        self.tb_logfile.setItem(row_pos, 1, QTableWidgetItem(record['tx_time']))
        self.tb_logfile.setItem(row_pos, 2, QTableWidgetItem(record['event']))
        self.tb_logfile.setItem(row_pos, 3, QTableWidgetItem(record['desc']))
        self.tb_logfile.setItem(row_pos, 4, QTableWidgetItem(record['opcode']))
        self.tb_logfile.setItem(row_pos, 5, QTableWidgetItem(record['rec_mark']))
        self.tb_logfile.setItem(row_pos, 6, QTableWidgetItem(record['seq_no']))
        self.tb_logfile.setItem(row_pos, 7, QTableWidgetItem(record['end_mark']))
        self.tb_logfile.setItem(row_pos, 8, QTableWidgetItem(record['path']))
        self.tb_logfile.setItem(row_pos, 9, QTableWidgetItem(record['filename']))  # File Name
        self.tb_logfile.setItem(row_pos, 10, QTableWidgetItem(record['ctime']))  # Creation Time
        self.tb_logfile.setItem(row_pos, 11, QTableWidgetItem(record['mtime']))  # Modified Time
        self.tb_logfile.setItem(row_pos, 12, QTableWidgetItem(record['chtime']))  # Changed Time
        self.tb_logfile.setItem(row_pos, 13, QTableWidgetItem(record['atime']))  # Accessed Time
        self.tb_logfile.setItem(row_pos, 14, QTableWidgetItem(record['lcn'])) # File LCN

    def _parse_chgjrnl(self):
        if self.sh is None:
            if not self.chgjrnl_path:
                self.message_box(title="Change Journal 오류",
                                 text="Change Journal 파일을 먼저 지정해주세요")
                return
            else:
                self.tb_chgjrnl.setRowCount(0)
                with open(self.chgjrnl_path, 'rb') as chgjrnl:
                    chgjrnl_data = chgjrnl.read()
                    thread = ThreadChgjrnl(chgjrnl_data)
                    progress_dlg = ProgressBar()
                    progress_dlg.setWindowTitle("Please Wait..")
                    progress_dlg.pgb_label.setText("Parsing Change Journal ...")
                    thread.progress_value.connect(progress_dlg.pgb.setValue)
                    thread.progress_value.connect(progress_dlg.exit)
                    thread.chgjrnl_record.connect(self._insert_chgjrnl_tb)
                    thread.start()
                    progress_dlg.exec_()
        else:
            self.tb_chgjrnl.setRowCount(0)

            records = self.sh.parse_chgjrnl()
            if records is None:
                self.message_box(title="Change Journal 오류",
                                 text="ReFS 이미지 내 Change Journal 파일이 존재하지 않습니다")
                return
            else:
                self.tb_chgjrnl.setRowCount(0)
                thread = ThreadChgjrnl(self.sh.refs.change_journal.chgjrnl_data)
                progress_dlg = ProgressBar()
                progress_dlg.setWindowTitle("Please Wait..")
                progress_dlg.pgb_label.setText("Parsing Change Journal ...")
                thread.progress_value.connect(progress_dlg.pgb.setValue)
                thread.progress_value.connect(progress_dlg.exit)
                thread.chgjrnl_record.connect(self._insert_chgjrnl_tb)
                thread.start()
                progress_dlg.exec_()

    @pyqtSlot(dict)
    def _insert_chgjrnl_tb(self, record):
        row_pos = self.tb_chgjrnl.rowCount()
        self.tb_chgjrnl.insertRow(row_pos)
        self.tb_chgjrnl.setItem(row_pos, 0, QTableWidgetItem(hex(record['usn'])))
        self.tb_chgjrnl.setItem(row_pos, 1, QTableWidgetItem(str(record['timestamp'])))
        self.tb_chgjrnl.setItem(row_pos, 2, QTableWidgetItem(record['name']))
        self.tb_chgjrnl.setItem(row_pos, 3, QTableWidgetItem(record['reason']))
        self.tb_chgjrnl.setItem(row_pos, 4, QTableWidgetItem(hex(record['source_info'])))
        self.tb_chgjrnl.setItem(row_pos, 5, QTableWidgetItem(hex(record['file_attribute'])))
        self.tb_chgjrnl.setItem(row_pos, 6, QTableWidgetItem('N/A'))  # hex(record['file_ref_no'])))
        self.tb_chgjrnl.setItem(row_pos, 7, QTableWidgetItem('N/A'))  # hex(record['parent_ref_no'])))

    def _export_csv(self):

        def write_csv(filename, table):
            with open(filename, 'w') as csvfile:
                writer = csv.writer(csvfile)
                for row_no in range(table.rowCount()):
                    fields = [table.item(row_no, col_no).text() for col_no in range(table.columnCount())]
                    writer.writerow(fields)

        if self.tb_logfile.rowCount() > 0 or self.tb_chgjrnl.rowCount() > 0:
            path = QFileDialog.getExistingDirectory(self, caption="Export CSV")
            if not path:
                return
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H-%M-%S")

            if self.tb_logfile.rowCount() > 0:
                csv_name = os.path.join(path, f'{timestamp}-ARIN-Logfile.csv')
                write_csv(csv_name, self.tb_logfile)

            if self.tb_chgjrnl.rowCount() > 0:
                csv_name = os.path.join(path, f'{timestamp}-ARIN-Change Journal.csv')
                write_csv(csv_name, self.tb_chgjrnl)

            self.message_box(title="CSV 내보내기 완료",
                             text="CSV 내보내기를 완료하였습니다.")

        else:
            self.message_box(title="Export CSV 오류",
                             text="Logfile이나 Change Journal을 먼저 분석해주세요.")

    def _export_sqlite(self):

        def query_insert(cursor, query, table):
            for row_no in range(table.rowCount()):
                values = [table.item(row_no, col_no).text() for col_no in range(table.columnCount())]
                values.insert(0, row_no)
                cursor.execute(query, tuple(values))

        CREATE_LOGFILE_TABLE = """ CREATE TABLE IF NOT EXISTS logfile (
                                id integer PRIMARY KEY,
                                LSN text NOT NULL,
                                Transaction_time text,
                                Event text,
                                Redo_Op text,
                                Record_mark text,
                                Seq_no text,
                                End_mark text,
                                Filename text,
                                Creation_time text,
                                Modified_time text, 
                                Changed_time text,
                                Accessed_time text,
                                File_lcn text );
                                """
        CREATE_CHGJRNL_TABLE = """ CREATE TABLE IF NOT EXISTS chgjrnl (
                                id integer PRIMARY KEY,
                                USN text NOT NULL,
                                Timestamp text,
                                Filename text,
                                Reason text,
                                Source_info text,
                                File_attr text,
                                File_ref_no text,
                                Parent_ref_no text );
                                """
        INSERT_LOGFILE = """ INSERT INTO logfile (id, LSN, Transaction_time, 
                            Event, Redo_Op, Record_mark, Seq_no, End_mark, 
                            Filename, Creation_time, Modified_time, Changed_time,
                            Accessed_time, File_lcn) VALUES 
                            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
        INSERT_CHGJRNL = """ INSERT INTO chgjrnl (id, USN, Timestamp, Filename, Reason, 
                            Source_info, File_attr, File_ref_no, Parent_ref_no) VALUES
                            (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """

        if self.tb_logfile.rowCount() > 0 or self.tb_chgjrnl.rowCount() > 0:
            path = QFileDialog.getExistingDirectory(self, caption="Export SQLite DB")
            if not path:
                return
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
            db_name = os.path.join(path, f'{timestamp}-ARIN.db')
            con = sqlite3.connect(db_name)
            cursor = con.cursor()

            if self.tb_logfile.rowCount() > 0:
                cursor.execute(CREATE_LOGFILE_TABLE)
                query_insert(cursor, INSERT_LOGFILE, self.tb_logfile)
                con.commit()

            if self.tb_chgjrnl.rowCount() > 0:
                cursor.execute(CREATE_CHGJRNL_TABLE)
                query_insert(cursor, INSERT_CHGJRNL, self.tb_chgjrnl)
                con.commit()

            self.message_box(title="SQLite DB 내보내기 완료",
                             text="SQLite DB 내보내기를 완료하였습니다.")

        else:
            self.message_box(title="Export SQLite 오류",
                             text="Logfile이나 Change Journal을 먼저 분석해주세요.")

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
