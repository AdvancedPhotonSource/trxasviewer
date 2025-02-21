from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, 
    QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QCheckBox, QComboBox
)
from PySide6.QtGui import QAction
import sys
import os
import numpy as np
from generated_ui import Ui_MainWindow
import glob
# from trxas_extract import Extract


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.init_ui()

    def init_ui(self):
        self.pushButton_select_rawfolder.clicked.connect(self.select_rawfolder)
        self.pushButton_select_outputfolder.clicked.connect(self.select_outputfolder)
        self.pushButton_process.clicked.connect(self.process)
    
    def select_rawfolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder_path:
            self.lineEdit_rawfolder.setText(folder_path)
            flist = os.listdir(folder_path)
            indexes = [int(f[-5:]) for f in flist]
            self.spinBox_fileindex_min.setValue(min(indexes))
            self.spinBox_fileindex_max.setValue(max(indexes))

    def select_outputfolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select OutputFolder")
        if folder_path:
            self.lineEdit_outputfolder.setText(folder_path)
    
    def process(self):
        kwargs = {
            "rawfolder": self.lineEdit_rawfolder.text(),
            "outputfolder": self.lineEdit_outputfolder.text(),
            "fileindex_min": self.spinBox_fileindex_min.value(),
            "fileindex_max": self.spinBox_fileindex_max.value(),
            "spinBox_syncbunch_number": self.spinBox_syncbunch_number.value(),
            "comboBox_groundstate_method": self.comboBox_groundstate_method.currentText(),
            "spinBox_orbitals_number": self.spinBox_orbitals_number.value(),
            "spinBox_compress_bunches": self.spinBox_compress_bunches.value(),
            "spinBox_output_points": self.spinBox_output_points.value(),
        } 
        print(kwargs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
