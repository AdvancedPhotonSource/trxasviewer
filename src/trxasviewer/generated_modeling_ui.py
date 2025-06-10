# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'modeling.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QGroupBox, QHeaderView, QLabel, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QSpinBox,
    QSplitter, QStatusBar, QTableView, QVBoxLayout,
    QWidget)

from pyqtgraph import GraphicsLayoutWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1230, 1052)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_6 = QGridLayout(self.centralwidget)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.groupBox = QGroupBox(self.layoutWidget)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(1, -1, 1, 1)
        self.pushButton_load = QPushButton(self.groupBox)
        self.pushButton_load.setObjectName(u"pushButton_load")

        self.gridLayout.addWidget(self.pushButton_load, 1, 0, 1, 1)

        self.tableView = QTableView(self.groupBox)
        self.tableView.setObjectName(u"tableView")

        self.gridLayout.addWidget(self.tableView, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.layoutWidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(1, 1, 1, 1)
        self.groupBox_5 = QGroupBox(self.groupBox_2)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_3 = QGridLayout(self.groupBox_5)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(1, 1, 1, 1)
        self.pushButton_3 = QPushButton(self.groupBox_5)
        self.pushButton_3.setObjectName(u"pushButton_3")

        self.gridLayout_3.addWidget(self.pushButton_3, 2, 1, 1, 1)

        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.checkBox_m52 = QCheckBox(self.groupBox_5)
        self.checkBox_m52.setObjectName(u"checkBox_m52")
        self.checkBox_m52.setMaximumSize(QSize(80, 16777215))
        font = QFont()
        font.setFamilies([u"DejaVu Sans"])
        font.setPointSize(12)
        self.checkBox_m52.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m52, 4, 2, 1, 1)

        self.checkBox_m51 = QCheckBox(self.groupBox_5)
        self.checkBox_m51.setObjectName(u"checkBox_m51")
        self.checkBox_m51.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m51.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m51, 4, 1, 1, 1)

        self.checkBox_m42 = QCheckBox(self.groupBox_5)
        self.checkBox_m42.setObjectName(u"checkBox_m42")
        self.checkBox_m42.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m42.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m42, 3, 2, 1, 1)

        self.checkBox_m54 = QCheckBox(self.groupBox_5)
        self.checkBox_m54.setObjectName(u"checkBox_m54")
        self.checkBox_m54.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m54.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m54, 4, 4, 1, 1)

        self.checkBox_m33 = QCheckBox(self.groupBox_5)
        self.checkBox_m33.setObjectName(u"checkBox_m33")
        self.checkBox_m33.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m33.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m33, 2, 3, 1, 1)

        self.label_2 = QLabel(self.groupBox_5)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.gridLayout_5.addWidget(self.label_2, 0, 0, 1, 1)

        self.checkBox_m53 = QCheckBox(self.groupBox_5)
        self.checkBox_m53.setObjectName(u"checkBox_m53")
        self.checkBox_m53.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m53.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m53, 4, 3, 1, 1)

        self.label_3 = QLabel(self.groupBox_5)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)

        self.gridLayout_5.addWidget(self.label_3, 1, 0, 1, 1)

        self.checkBox_m22 = QCheckBox(self.groupBox_5)
        self.checkBox_m22.setObjectName(u"checkBox_m22")
        self.checkBox_m22.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m22.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m22, 1, 2, 1, 1)

        self.checkBox_m32 = QCheckBox(self.groupBox_5)
        self.checkBox_m32.setObjectName(u"checkBox_m32")
        self.checkBox_m32.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m32.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m32, 2, 2, 1, 1)

        self.checkBox_m31 = QCheckBox(self.groupBox_5)
        self.checkBox_m31.setObjectName(u"checkBox_m31")
        self.checkBox_m31.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m31.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m31, 2, 1, 1, 1)

        self.label_5 = QLabel(self.groupBox_5)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font)

        self.gridLayout_5.addWidget(self.label_5, 3, 0, 1, 1)

        self.checkBox_m21 = QCheckBox(self.groupBox_5)
        self.checkBox_m21.setObjectName(u"checkBox_m21")
        self.checkBox_m21.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m21.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m21, 1, 1, 1, 1)

        self.checkBox_m11 = QCheckBox(self.groupBox_5)
        self.checkBox_m11.setObjectName(u"checkBox_m11")
        self.checkBox_m11.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m11.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m11, 0, 1, 1, 1)

        self.label_4 = QLabel(self.groupBox_5)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.gridLayout_5.addWidget(self.label_4, 2, 0, 1, 1)

        self.checkBox_m43 = QCheckBox(self.groupBox_5)
        self.checkBox_m43.setObjectName(u"checkBox_m43")
        self.checkBox_m43.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m43.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m43, 3, 3, 1, 1)

        self.checkBox_m41 = QCheckBox(self.groupBox_5)
        self.checkBox_m41.setObjectName(u"checkBox_m41")
        self.checkBox_m41.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m41.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m41, 3, 1, 1, 1)

        self.checkBox_m44 = QCheckBox(self.groupBox_5)
        self.checkBox_m44.setObjectName(u"checkBox_m44")
        self.checkBox_m44.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m44.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m44, 3, 4, 1, 1)

        self.label_6 = QLabel(self.groupBox_5)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font)

        self.gridLayout_5.addWidget(self.label_6, 4, 0, 1, 1)

        self.checkBox_m55 = QCheckBox(self.groupBox_5)
        self.checkBox_m55.setObjectName(u"checkBox_m55")
        self.checkBox_m55.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m55.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m55, 4, 5, 1, 1)

        self.checkBox_m61 = QCheckBox(self.groupBox_5)
        self.checkBox_m61.setObjectName(u"checkBox_m61")
        self.checkBox_m61.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m61.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m61, 5, 1, 1, 1)

        self.label_7 = QLabel(self.groupBox_5)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_5.addWidget(self.label_7, 5, 0, 1, 1)

        self.checkBox_m62 = QCheckBox(self.groupBox_5)
        self.checkBox_m62.setObjectName(u"checkBox_m62")
        self.checkBox_m62.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m62.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m62, 5, 2, 1, 1)

        self.checkBox_m63 = QCheckBox(self.groupBox_5)
        self.checkBox_m63.setObjectName(u"checkBox_m63")
        self.checkBox_m63.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m63.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m63, 5, 3, 1, 1)

        self.checkBox_m64 = QCheckBox(self.groupBox_5)
        self.checkBox_m64.setObjectName(u"checkBox_m64")
        self.checkBox_m64.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m64.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m64, 5, 4, 1, 1)

        self.checkBox_m65 = QCheckBox(self.groupBox_5)
        self.checkBox_m65.setObjectName(u"checkBox_m65")
        self.checkBox_m65.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m65.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m65, 5, 5, 1, 1)


        self.gridLayout_3.addLayout(self.gridLayout_5, 0, 0, 1, 3)

        self.pushButton_2 = QPushButton(self.groupBox_5)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.gridLayout_3.addWidget(self.pushButton_2, 2, 0, 1, 1)

        self.pushButton_updatemodel = QPushButton(self.groupBox_5)
        self.pushButton_updatemodel.setObjectName(u"pushButton_updatemodel")

        self.gridLayout_3.addWidget(self.pushButton_updatemodel, 2, 2, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_5, 1, 0, 1, 4)

        self.groupBox_3 = QGroupBox(self.groupBox_2)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_8 = QGridLayout(self.groupBox_3)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_graph = QLabel(self.groupBox_3)
        self.label_graph.setObjectName(u"label_graph")
        self.label_graph.setMinimumSize(QSize(200, 200))

        self.gridLayout_8.addWidget(self.label_graph, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_3, 2, 0, 1, 4)

        self.groupBox_6 = QGroupBox(self.groupBox_2)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.gridLayout_7 = QGridLayout(self.groupBox_6)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(1, 1, 1, 1)
        self.tableView_parameters = QTableView(self.groupBox_6)
        self.tableView_parameters.setObjectName(u"tableView_parameters")
        self.tableView_parameters.setMinimumSize(QSize(0, 300))

        self.gridLayout_7.addWidget(self.tableView_parameters, 1, 0, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_6, 3, 0, 1, 4)

        self.comboBox_model = QComboBox(self.groupBox_2)
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.setObjectName(u"comboBox_model")

        self.gridLayout_2.addWidget(self.comboBox_model, 0, 3, 1, 1)

        self.spinBox_nstates = QSpinBox(self.groupBox_2)
        self.spinBox_nstates.setObjectName(u"spinBox_nstates")
        self.spinBox_nstates.setMinimum(1)
        self.spinBox_nstates.setMaximum(5)
        self.spinBox_nstates.setValue(3)

        self.gridLayout_2.addWidget(self.spinBox_nstates, 0, 2, 1, 1)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 2)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.splitter.addWidget(self.layoutWidget)
        self.groupBox_4 = QGroupBox(self.splitter)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy)
        self.groupBox_4.setMinimumSize(QSize(600, 0))
        self.gridLayout_4 = QGridLayout(self.groupBox_4)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.display = GraphicsLayoutWidget(self.groupBox_4)
        self.display.setObjectName(u"display")
        font1 = QFont()
        font1.setFamilies([u"DejaVu Sans"])
        self.display.setFont(font1)

        self.gridLayout_4.addWidget(self.display, 0, 0, 1, 1)

        self.splitter.addWidget(self.groupBox_4)

        self.gridLayout_6.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1230, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Kinetics-Modeling", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Kinetics Datasets", None))
        self.pushButton_load.setText(QCoreApplication.translate("MainWindow", u"Load Results", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Model", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"State-Matrix", None))
        self.pushButton_3.setText(QCoreApplication.translate("MainWindow", u"PushButton", None))
        self.checkBox_m52.setText(QCoreApplication.translate("MainWindow", u"m25", None))
        self.checkBox_m51.setText(QCoreApplication.translate("MainWindow", u"m15", None))
        self.checkBox_m42.setText(QCoreApplication.translate("MainWindow", u"m24", None))
        self.checkBox_m54.setText(QCoreApplication.translate("MainWindow", u"m45", None))
        self.checkBox_m33.setText(QCoreApplication.translate("MainWindow", u"m33", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"State1", None))
        self.checkBox_m53.setText(QCoreApplication.translate("MainWindow", u"m35", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"State2", None))
        self.checkBox_m22.setText(QCoreApplication.translate("MainWindow", u"m22", None))
        self.checkBox_m32.setText(QCoreApplication.translate("MainWindow", u"m23", None))
        self.checkBox_m31.setText(QCoreApplication.translate("MainWindow", u"m13", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"State4", None))
        self.checkBox_m21.setText(QCoreApplication.translate("MainWindow", u"m12", None))
        self.checkBox_m11.setText(QCoreApplication.translate("MainWindow", u"m11", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"State3", None))
        self.checkBox_m43.setText(QCoreApplication.translate("MainWindow", u"m34", None))
        self.checkBox_m41.setText(QCoreApplication.translate("MainWindow", u"m14", None))
        self.checkBox_m44.setText(QCoreApplication.translate("MainWindow", u"m44", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"State5", None))
        self.checkBox_m55.setText(QCoreApplication.translate("MainWindow", u"m55", None))
        self.checkBox_m61.setText(QCoreApplication.translate("MainWindow", u"m1g", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"GS", None))
        self.checkBox_m62.setText(QCoreApplication.translate("MainWindow", u"m2g", None))
        self.checkBox_m63.setText(QCoreApplication.translate("MainWindow", u"m3g", None))
        self.checkBox_m64.setText(QCoreApplication.translate("MainWindow", u"m4g", None))
        self.checkBox_m65.setText(QCoreApplication.translate("MainWindow", u"m5g", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.pushButton_updatemodel.setText(QCoreApplication.translate("MainWindow", u"Update", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Graph", None))
        self.label_graph.setText("")
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Parameters", None))
        self.comboBox_model.setItemText(0, QCoreApplication.translate("MainWindow", u"parallel", None))
        self.comboBox_model.setItemText(1, QCoreApplication.translate("MainWindow", u"sequential", None))
        self.comboBox_model.setItemText(2, QCoreApplication.translate("MainWindow", u"advanced", None))

        self.label.setText(QCoreApplication.translate("MainWindow", u"Number of States", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"GroupBox", None))
    # retranslateUi

