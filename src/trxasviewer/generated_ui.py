# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'viewer.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QSplitter, QStatusBar, QWidget)

from pyqtgraph import (ImageView, PlotWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1309, 814)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.groupBox_5 = QGroupBox(self.splitter)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy)
        self.gridLayout_5 = QGridLayout(self.groupBox_5)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.pushButton_select_rawfolder = QPushButton(self.groupBox_5)
        self.pushButton_select_rawfolder.setObjectName(u"pushButton_select_rawfolder")

        self.gridLayout_3.addWidget(self.pushButton_select_rawfolder, 0, 0, 1, 1)

        self.pushButton_select_outputfolder = QPushButton(self.groupBox_5)
        self.pushButton_select_outputfolder.setObjectName(u"pushButton_select_outputfolder")

        self.gridLayout_3.addWidget(self.pushButton_select_outputfolder, 1, 0, 1, 1)

        self.lineEdit_rawfolder = QLineEdit(self.groupBox_5)
        self.lineEdit_rawfolder.setObjectName(u"lineEdit_rawfolder")

        self.gridLayout_3.addWidget(self.lineEdit_rawfolder, 0, 1, 1, 1)

        self.lineEdit_outputfolder = QLineEdit(self.groupBox_5)
        self.lineEdit_outputfolder.setObjectName(u"lineEdit_outputfolder")

        self.gridLayout_3.addWidget(self.lineEdit_outputfolder, 1, 1, 1, 1)


        self.gridLayout_5.addLayout(self.gridLayout_3, 0, 0, 1, 1)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.spinBox_orbitals_number = QSpinBox(self.groupBox_5)
        self.spinBox_orbitals_number.setObjectName(u"spinBox_orbitals_number")
        self.spinBox_orbitals_number.setMinimum(1)
        self.spinBox_orbitals_number.setMaximum(999999)

        self.gridLayout_4.addWidget(self.spinBox_orbitals_number, 3, 4, 1, 2)

        self.label_5 = QLabel(self.groupBox_5)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_4.addWidget(self.label_5, 2, 0, 1, 4)

        self.label_6 = QLabel(self.groupBox_5)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_4.addWidget(self.label_6, 3, 0, 1, 4)

        self.label_8 = QLabel(self.groupBox_5)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_4.addWidget(self.label_8, 5, 0, 1, 4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.spinBox_fileindex_min = QSpinBox(self.groupBox_5)
        self.spinBox_fileindex_min.setObjectName(u"spinBox_fileindex_min")

        self.horizontalLayout.addWidget(self.spinBox_fileindex_min)

        self.spinBox_fileindex_max = QSpinBox(self.groupBox_5)
        self.spinBox_fileindex_max.setObjectName(u"spinBox_fileindex_max")

        self.horizontalLayout.addWidget(self.spinBox_fileindex_max)


        self.gridLayout_4.addLayout(self.horizontalLayout, 0, 4, 1, 2)

        self.label_7 = QLabel(self.groupBox_5)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_4.addWidget(self.label_7, 4, 0, 1, 4)

        self.comboBox_groundstate_method = QComboBox(self.groupBox_5)
        self.comboBox_groundstate_method.addItem("")
        self.comboBox_groundstate_method.addItem("")
        self.comboBox_groundstate_method.setObjectName(u"comboBox_groundstate_method")

        self.gridLayout_4.addWidget(self.comboBox_groundstate_method, 2, 4, 1, 2)

        self.spinBox_compress_bunches = QSpinBox(self.groupBox_5)
        self.spinBox_compress_bunches.setObjectName(u"spinBox_compress_bunches")
        self.spinBox_compress_bunches.setMinimum(1)

        self.gridLayout_4.addWidget(self.spinBox_compress_bunches, 4, 4, 1, 2)

        self.label_4 = QLabel(self.groupBox_5)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_4.addWidget(self.label_4, 1, 0, 1, 4)

        self.spinBox_syncbunch_number = QSpinBox(self.groupBox_5)
        self.spinBox_syncbunch_number.setObjectName(u"spinBox_syncbunch_number")

        self.gridLayout_4.addWidget(self.spinBox_syncbunch_number, 1, 4, 1, 2)

        self.label_2 = QLabel(self.groupBox_5)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_4.addWidget(self.label_2, 0, 0, 1, 4)

        self.spinBox_output_points = QSpinBox(self.groupBox_5)
        self.spinBox_output_points.setObjectName(u"spinBox_output_points")
        self.spinBox_output_points.setMinimum(1)

        self.gridLayout_4.addWidget(self.spinBox_output_points, 5, 4, 1, 2)

        self.pushButton_2 = QPushButton(self.groupBox_5)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.gridLayout_4.addWidget(self.pushButton_2, 6, 3, 1, 3)

        self.pushButton_process = QPushButton(self.groupBox_5)
        self.pushButton_process.setObjectName(u"pushButton_process")

        self.gridLayout_4.addWidget(self.pushButton_process, 6, 0, 1, 3)


        self.gridLayout_5.addLayout(self.gridLayout_4, 1, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer, 2, 0, 1, 1)

        self.splitter.addWidget(self.groupBox_5)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.gridLayout = QGridLayout(self.layoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.groupBox = QGroupBox(self.layoutWidget)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(2)
        sizePolicy1.setVerticalStretch(2)
        sizePolicy1.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy1)
        self.gridLayout_6 = QGridLayout(self.groupBox)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.pg_hdl_img2d = ImageView(self.groupBox)
        self.pg_hdl_img2d.setObjectName(u"pg_hdl_img2d")

        self.gridLayout_6.addWidget(self.pg_hdl_img2d, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.groupBox_3 = QGroupBox(self.layoutWidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(1)
        sizePolicy2.setVerticalStretch(1)
        sizePolicy2.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy2)
        self.gridLayout_8 = QGridLayout(self.groupBox_3)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.pg_hdl_vline = PlotWidget(self.groupBox_3)
        self.pg_hdl_vline.setObjectName(u"pg_hdl_vline")

        self.gridLayout_8.addWidget(self.pg_hdl_vline, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_3, 0, 1, 1, 1)

        self.groupBox_2 = QGroupBox(self.layoutWidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy2.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy2)
        self.gridLayout_7 = QGridLayout(self.groupBox_2)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.pg_hdl_hline = PlotWidget(self.groupBox_2)
        self.pg_hdl_hline.setObjectName(u"pg_hdl_hline")

        self.gridLayout_7.addWidget(self.pg_hdl_hline, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_2, 1, 0, 1, 1)

        self.groupBox_4 = QGroupBox(self.layoutWidget)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy2.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy2)

        self.gridLayout.addWidget(self.groupBox_4, 1, 1, 1, 1)

        self.splitter.addWidget(self.layoutWidget)

        self.gridLayout_2.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1309, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.pushButton_select_rawfolder.setText(QCoreApplication.translate("MainWindow", u"select raw data", None))
        self.pushButton_select_outputfolder.setText(QCoreApplication.translate("MainWindow", u"select output folder", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Ground State Method", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Number of orbitals for ground state", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Number of porints to output", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Number of bunches to compress", None))
        self.comboBox_groundstate_method.setItemText(0, QCoreApplication.translate("MainWindow", u"per_bunch", None))
        self.comboBox_groundstate_method.setItemText(1, QCoreApplication.translate("MainWindow", u"avg_bunch", None))

        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Sync bunch number", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"File index range", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Plot", None))
        self.pushButton_process.setText(QCoreApplication.translate("MainWindow", u"Process", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"GroupBox", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"GroupBox", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"GroupBox", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"GroupBox", None))
    # retranslateUi

