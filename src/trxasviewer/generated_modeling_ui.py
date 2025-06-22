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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QGridLayout, QGroupBox, QHeaderView, QLabel,
    QMainWindow, QMenuBar, QProgressBar, QPushButton,
    QSizePolicy, QSpinBox, QSplitter, QStatusBar,
    QTableView, QVBoxLayout, QWidget)

from pyqtgraph import (GraphicsLayoutWidget, ImageView)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1557, 980)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_9 = QGridLayout(self.centralwidget)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.splitter_3 = QSplitter(self.centralwidget)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Orientation.Horizontal)
        self.splitter_2 = QSplitter(self.splitter_3)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Orientation.Vertical)
        self.groupBox = QGroupBox(self.splitter_2)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(1, -1, 1, 1)
        self.pushButton_load = QPushButton(self.groupBox)
        self.pushButton_load.setObjectName(u"pushButton_load")

        self.gridLayout.addWidget(self.pushButton_load, 0, 0, 1, 1)

        self.tableView = QTableView(self.groupBox)
        self.tableView.setObjectName(u"tableView")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(self.tableView.sizePolicy().hasHeightForWidth())
        self.tableView.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.tableView, 1, 0, 1, 2)

        self.checkBox_kinetics_profiles = QCheckBox(self.groupBox)
        self.checkBox_kinetics_profiles.setObjectName(u"checkBox_kinetics_profiles")
        self.checkBox_kinetics_profiles.setChecked(True)

        self.gridLayout.addWidget(self.checkBox_kinetics_profiles, 0, 1, 1, 1)

        self.splitter_2.addWidget(self.groupBox)
        self.groupBox_2 = QGroupBox(self.splitter_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(2, 2, 2, 2)
        self.groupBox_3 = QGroupBox(self.groupBox_2)
        self.groupBox_3.setObjectName(u"groupBox_3")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy2)
        self.gridLayout_8 = QGridLayout(self.groupBox_3)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_graph = QLabel(self.groupBox_3)
        self.label_graph.setObjectName(u"label_graph")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(2)
        sizePolicy3.setHeightForWidth(self.label_graph.sizePolicy().hasHeightForWidth())
        self.label_graph.setSizePolicy(sizePolicy3)
        self.label_graph.setMinimumSize(QSize(400, 200))

        self.gridLayout_8.addWidget(self.label_graph, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_3, 1, 0, 1, 8)

        self.pushButton_save_model = QPushButton(self.groupBox_2)
        self.pushButton_save_model.setObjectName(u"pushButton_save_model")

        self.gridLayout_2.addWidget(self.pushButton_save_model, 6, 0, 1, 2)

        self.groupBox_5 = QGroupBox(self.groupBox_2)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy4)
        self.gridLayout_3 = QGridLayout(self.groupBox_5)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(1, 1, 1, 1)
        self.label = QLabel(self.groupBox_5)
        self.label.setObjectName(u"label")

        self.gridLayout_3.addWidget(self.label, 0, 0, 1, 1)

        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.checkBox_m43 = QCheckBox(self.groupBox_5)
        self.checkBox_m43.setObjectName(u"checkBox_m43")
        self.checkBox_m43.setEnabled(False)
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.checkBox_m43.sizePolicy().hasHeightForWidth())
        self.checkBox_m43.setSizePolicy(sizePolicy5)
        self.checkBox_m43.setMaximumSize(QSize(80, 16777215))
        font = QFont()
        font.setFamilies([u"DejaVu Sans"])
        font.setPointSize(12)
        self.checkBox_m43.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m43, 3, 3, 1, 1)

        self.checkBox_m31 = QCheckBox(self.groupBox_5)
        self.checkBox_m31.setObjectName(u"checkBox_m31")
        sizePolicy5.setHeightForWidth(self.checkBox_m31.sizePolicy().hasHeightForWidth())
        self.checkBox_m31.setSizePolicy(sizePolicy5)
        self.checkBox_m31.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m31.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m31, 2, 1, 1, 1)

        self.checkBox_m11 = QCheckBox(self.groupBox_5)
        self.checkBox_m11.setObjectName(u"checkBox_m11")
        sizePolicy5.setHeightForWidth(self.checkBox_m11.sizePolicy().hasHeightForWidth())
        self.checkBox_m11.setSizePolicy(sizePolicy5)
        self.checkBox_m11.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m11.setFont(font)
        self.checkBox_m11.setChecked(True)

        self.gridLayout_5.addWidget(self.checkBox_m11, 0, 1, 1, 1)

        self.checkBox_m64 = QCheckBox(self.groupBox_5)
        self.checkBox_m64.setObjectName(u"checkBox_m64")
        self.checkBox_m64.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m64.sizePolicy().hasHeightForWidth())
        self.checkBox_m64.setSizePolicy(sizePolicy5)
        self.checkBox_m64.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m64.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m64, 5, 4, 1, 1)

        self.checkBox_m33 = QCheckBox(self.groupBox_5)
        self.checkBox_m33.setObjectName(u"checkBox_m33")
        sizePolicy5.setHeightForWidth(self.checkBox_m33.sizePolicy().hasHeightForWidth())
        self.checkBox_m33.setSizePolicy(sizePolicy5)
        self.checkBox_m33.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m33.setFont(font)
        self.checkBox_m33.setChecked(True)

        self.gridLayout_5.addWidget(self.checkBox_m33, 2, 3, 1, 1)

        self.label_3 = QLabel(self.groupBox_5)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)

        self.gridLayout_5.addWidget(self.label_3, 1, 0, 1, 1)

        self.checkBox_m22 = QCheckBox(self.groupBox_5)
        self.checkBox_m22.setObjectName(u"checkBox_m22")
        sizePolicy5.setHeightForWidth(self.checkBox_m22.sizePolicy().hasHeightForWidth())
        self.checkBox_m22.setSizePolicy(sizePolicy5)
        self.checkBox_m22.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m22.setFont(font)
        self.checkBox_m22.setChecked(True)

        self.gridLayout_5.addWidget(self.checkBox_m22, 1, 2, 1, 1)

        self.checkBox_m32 = QCheckBox(self.groupBox_5)
        self.checkBox_m32.setObjectName(u"checkBox_m32")
        sizePolicy5.setHeightForWidth(self.checkBox_m32.sizePolicy().hasHeightForWidth())
        self.checkBox_m32.setSizePolicy(sizePolicy5)
        self.checkBox_m32.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m32.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m32, 2, 2, 1, 1)

        self.checkBox_m61 = QCheckBox(self.groupBox_5)
        self.checkBox_m61.setObjectName(u"checkBox_m61")
        sizePolicy5.setHeightForWidth(self.checkBox_m61.sizePolicy().hasHeightForWidth())
        self.checkBox_m61.setSizePolicy(sizePolicy5)
        self.checkBox_m61.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m61.setFont(font)
        self.checkBox_m61.setChecked(True)

        self.gridLayout_5.addWidget(self.checkBox_m61, 5, 1, 1, 1)

        self.checkBox_m44 = QCheckBox(self.groupBox_5)
        self.checkBox_m44.setObjectName(u"checkBox_m44")
        self.checkBox_m44.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m44.sizePolicy().hasHeightForWidth())
        self.checkBox_m44.setSizePolicy(sizePolicy5)
        self.checkBox_m44.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m44.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m44, 3, 4, 1, 1)

        self.label_7 = QLabel(self.groupBox_5)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_5.addWidget(self.label_7, 5, 0, 1, 1)

        self.label_5 = QLabel(self.groupBox_5)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font)

        self.gridLayout_5.addWidget(self.label_5, 3, 0, 1, 1)

        self.checkBox_m53 = QCheckBox(self.groupBox_5)
        self.checkBox_m53.setObjectName(u"checkBox_m53")
        self.checkBox_m53.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m53.sizePolicy().hasHeightForWidth())
        self.checkBox_m53.setSizePolicy(sizePolicy5)
        self.checkBox_m53.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m53.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m53, 4, 3, 1, 1)

        self.checkBox_m41 = QCheckBox(self.groupBox_5)
        self.checkBox_m41.setObjectName(u"checkBox_m41")
        self.checkBox_m41.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m41.sizePolicy().hasHeightForWidth())
        self.checkBox_m41.setSizePolicy(sizePolicy5)
        self.checkBox_m41.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m41.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m41, 3, 1, 1, 1)

        self.checkBox_m54 = QCheckBox(self.groupBox_5)
        self.checkBox_m54.setObjectName(u"checkBox_m54")
        self.checkBox_m54.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m54.sizePolicy().hasHeightForWidth())
        self.checkBox_m54.setSizePolicy(sizePolicy5)
        self.checkBox_m54.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m54.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m54, 4, 4, 1, 1)

        self.label_2 = QLabel(self.groupBox_5)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.gridLayout_5.addWidget(self.label_2, 0, 0, 1, 1)

        self.checkBox_m55 = QCheckBox(self.groupBox_5)
        self.checkBox_m55.setObjectName(u"checkBox_m55")
        self.checkBox_m55.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m55.sizePolicy().hasHeightForWidth())
        self.checkBox_m55.setSizePolicy(sizePolicy5)
        self.checkBox_m55.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m55.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m55, 4, 5, 1, 1)

        self.checkBox_m63 = QCheckBox(self.groupBox_5)
        self.checkBox_m63.setObjectName(u"checkBox_m63")
        sizePolicy5.setHeightForWidth(self.checkBox_m63.sizePolicy().hasHeightForWidth())
        self.checkBox_m63.setSizePolicy(sizePolicy5)
        self.checkBox_m63.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m63.setFont(font)
        self.checkBox_m63.setChecked(True)

        self.gridLayout_5.addWidget(self.checkBox_m63, 5, 3, 1, 1)

        self.checkBox_m21 = QCheckBox(self.groupBox_5)
        self.checkBox_m21.setObjectName(u"checkBox_m21")
        sizePolicy5.setHeightForWidth(self.checkBox_m21.sizePolicy().hasHeightForWidth())
        self.checkBox_m21.setSizePolicy(sizePolicy5)
        self.checkBox_m21.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m21.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m21, 1, 1, 1, 1)

        self.label_6 = QLabel(self.groupBox_5)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font)

        self.gridLayout_5.addWidget(self.label_6, 4, 0, 1, 1)

        self.checkBox_m52 = QCheckBox(self.groupBox_5)
        self.checkBox_m52.setObjectName(u"checkBox_m52")
        self.checkBox_m52.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m52.sizePolicy().hasHeightForWidth())
        self.checkBox_m52.setSizePolicy(sizePolicy5)
        self.checkBox_m52.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m52.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m52, 4, 2, 1, 1)

        self.label_4 = QLabel(self.groupBox_5)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.gridLayout_5.addWidget(self.label_4, 2, 0, 1, 1)

        self.checkBox_m62 = QCheckBox(self.groupBox_5)
        self.checkBox_m62.setObjectName(u"checkBox_m62")
        sizePolicy5.setHeightForWidth(self.checkBox_m62.sizePolicy().hasHeightForWidth())
        self.checkBox_m62.setSizePolicy(sizePolicy5)
        self.checkBox_m62.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m62.setFont(font)
        self.checkBox_m62.setChecked(True)

        self.gridLayout_5.addWidget(self.checkBox_m62, 5, 2, 1, 1)

        self.checkBox_m51 = QCheckBox(self.groupBox_5)
        self.checkBox_m51.setObjectName(u"checkBox_m51")
        self.checkBox_m51.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m51.sizePolicy().hasHeightForWidth())
        self.checkBox_m51.setSizePolicy(sizePolicy5)
        self.checkBox_m51.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m51.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m51, 4, 1, 1, 1)

        self.checkBox_m65 = QCheckBox(self.groupBox_5)
        self.checkBox_m65.setObjectName(u"checkBox_m65")
        self.checkBox_m65.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m65.sizePolicy().hasHeightForWidth())
        self.checkBox_m65.setSizePolicy(sizePolicy5)
        self.checkBox_m65.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m65.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m65, 5, 5, 1, 1)

        self.checkBox_m42 = QCheckBox(self.groupBox_5)
        self.checkBox_m42.setObjectName(u"checkBox_m42")
        self.checkBox_m42.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.checkBox_m42.sizePolicy().hasHeightForWidth())
        self.checkBox_m42.setSizePolicy(sizePolicy5)
        self.checkBox_m42.setMaximumSize(QSize(80, 16777215))
        self.checkBox_m42.setFont(font)

        self.gridLayout_5.addWidget(self.checkBox_m42, 3, 2, 1, 1)


        self.gridLayout_3.addLayout(self.gridLayout_5, 1, 0, 1, 5)

        self.spinBox_nstates = QSpinBox(self.groupBox_5)
        self.spinBox_nstates.setObjectName(u"spinBox_nstates")
        self.spinBox_nstates.setMinimum(1)
        self.spinBox_nstates.setMaximum(5)
        self.spinBox_nstates.setValue(3)

        self.gridLayout_3.addWidget(self.spinBox_nstates, 0, 1, 1, 1)

        self.comboBox_model = QComboBox(self.groupBox_5)
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.setObjectName(u"comboBox_model")

        self.gridLayout_3.addWidget(self.comboBox_model, 0, 2, 1, 3)


        self.gridLayout_2.addWidget(self.groupBox_5, 0, 0, 1, 8)

        self.groupBox_6 = QGroupBox(self.groupBox_2)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.gridLayout_7 = QGridLayout(self.groupBox_6)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(1, 1, 1, 1)
        self.tableView_parameters = QTableView(self.groupBox_6)
        self.tableView_parameters.setObjectName(u"tableView_parameters")
        sizePolicy1.setHeightForWidth(self.tableView_parameters.sizePolicy().hasHeightForWidth())
        self.tableView_parameters.setSizePolicy(sizePolicy1)
        self.tableView_parameters.setMinimumSize(QSize(0, 150))

        self.gridLayout_7.addWidget(self.tableView_parameters, 1, 0, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_6, 4, 0, 1, 8)

        self.pushButton_updatemodel = QPushButton(self.groupBox_2)
        self.pushButton_updatemodel.setObjectName(u"pushButton_updatemodel")

        self.gridLayout_2.addWidget(self.pushButton_updatemodel, 6, 6, 1, 2)

        self.pushButton_load_model = QPushButton(self.groupBox_2)
        self.pushButton_load_model.setObjectName(u"pushButton_load_model")

        self.gridLayout_2.addWidget(self.pushButton_load_model, 6, 2, 1, 2)

        self.splitter_2.addWidget(self.groupBox_2)
        self.splitter_3.addWidget(self.splitter_2)
        self.layoutWidget = QWidget(self.splitter_3)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(self.layoutWidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.groupBox_4 = QGroupBox(self.splitter)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy6.setHorizontalStretch(2)
        sizePolicy6.setVerticalStretch(2)
        sizePolicy6.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy6)
        self.groupBox_4.setMinimumSize(QSize(600, 0))
        self.gridLayout_4 = QGridLayout(self.groupBox_4)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.pg_gfit_display = GraphicsLayoutWidget(self.groupBox_4)
        self.pg_gfit_display.setObjectName(u"pg_gfit_display")
        sizePolicy6.setHeightForWidth(self.pg_gfit_display.sizePolicy().hasHeightForWidth())
        self.pg_gfit_display.setSizePolicy(sizePolicy6)
        font1 = QFont()
        font1.setFamilies([u"DejaVu Sans"])
        self.pg_gfit_display.setFont(font1)

        self.gridLayout_4.addWidget(self.pg_gfit_display, 2, 0, 1, 2)

        self.pg_gfit_svd = GraphicsLayoutWidget(self.groupBox_4)
        self.pg_gfit_svd.setObjectName(u"pg_gfit_svd")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy7.setHorizontalStretch(1)
        sizePolicy7.setVerticalStretch(3)
        sizePolicy7.setHeightForWidth(self.pg_gfit_svd.sizePolicy().hasHeightForWidth())
        self.pg_gfit_svd.setSizePolicy(sizePolicy7)

        self.gridLayout_4.addWidget(self.pg_gfit_svd, 0, 1, 1, 1)

        self.pg_diff = ImageView(self.groupBox_4)
        self.pg_diff.setObjectName(u"pg_diff")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy8.setHorizontalStretch(4)
        sizePolicy8.setVerticalStretch(3)
        sizePolicy8.setHeightForWidth(self.pg_diff.sizePolicy().hasHeightForWidth())
        self.pg_diff.setSizePolicy(sizePolicy8)

        self.gridLayout_4.addWidget(self.pg_diff, 0, 0, 1, 1)

        self.splitter.addWidget(self.groupBox_4)
        self.groupBox_kprofiles = QGroupBox(self.splitter)
        self.groupBox_kprofiles.setObjectName(u"groupBox_kprofiles")
        sizePolicy9 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy9.setHorizontalStretch(2)
        sizePolicy9.setVerticalStretch(3)
        sizePolicy9.setHeightForWidth(self.groupBox_kprofiles.sizePolicy().hasHeightForWidth())
        self.groupBox_kprofiles.setSizePolicy(sizePolicy9)
        self.gridLayout_6 = QGridLayout(self.groupBox_kprofiles)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)
        self.pg_pfit_display = GraphicsLayoutWidget(self.groupBox_kprofiles)
        self.pg_pfit_display.setObjectName(u"pg_pfit_display")
        sizePolicy10 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(3)
        sizePolicy10.setHeightForWidth(self.pg_pfit_display.sizePolicy().hasHeightForWidth())
        self.pg_pfit_display.setSizePolicy(sizePolicy10)
        self.label_17 = QLabel(self.pg_pfit_display)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setGeometry(QRect(917, 172, 27, 26))

        self.gridLayout_6.addWidget(self.pg_pfit_display, 0, 0, 1, 1)

        self.splitter.addWidget(self.groupBox_kprofiles)

        self.verticalLayout_2.addWidget(self.splitter)

        self.groupBox_8 = QGroupBox(self.layoutWidget)
        self.groupBox_8.setObjectName(u"groupBox_8")
        sizePolicy11 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy11.setHorizontalStretch(2)
        sizePolicy11.setVerticalStretch(0)
        sizePolicy11.setHeightForWidth(self.groupBox_8.sizePolicy().hasHeightForWidth())
        self.groupBox_8.setSizePolicy(sizePolicy11)
        self.gridLayout_10 = QGridLayout(self.groupBox_8)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setContentsMargins(1, 1, 1, 1)
        self.comboBox_fit_tunit = QComboBox(self.groupBox_8)
        self.comboBox_fit_tunit.addItem("")
        self.comboBox_fit_tunit.addItem("")
        self.comboBox_fit_tunit.addItem("")
        self.comboBox_fit_tunit.addItem("")
        self.comboBox_fit_tunit.addItem("")
        self.comboBox_fit_tunit.addItem("")
        self.comboBox_fit_tunit.addItem("")
        self.comboBox_fit_tunit.setObjectName(u"comboBox_fit_tunit")
        sizePolicy12 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy12.setHorizontalStretch(0)
        sizePolicy12.setVerticalStretch(0)
        sizePolicy12.setHeightForWidth(self.comboBox_fit_tunit.sizePolicy().hasHeightForWidth())
        self.comboBox_fit_tunit.setSizePolicy(sizePolicy12)

        self.gridLayout_10.addWidget(self.comboBox_fit_tunit, 4, 3, 1, 1)

        self.label_19 = QLabel(self.groupBox_8)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_10.addWidget(self.label_19, 1, 6, 1, 1)

        self.label_9 = QLabel(self.groupBox_8)
        self.label_9.setObjectName(u"label_9")
        sizePolicy13 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy13.setHorizontalStretch(2)
        sizePolicy13.setVerticalStretch(0)
        sizePolicy13.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy13)

        self.gridLayout_10.addWidget(self.label_9, 0, 3, 1, 1)

        self.label_11 = QLabel(self.groupBox_8)
        self.label_11.setObjectName(u"label_11")
        sizePolicy14 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy14.setHorizontalStretch(2)
        sizePolicy14.setVerticalStretch(0)
        sizePolicy14.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy14)

        self.gridLayout_10.addWidget(self.label_11, 1, 10, 1, 1)

        self.spinBox_num_tries = QSpinBox(self.groupBox_8)
        self.spinBox_num_tries.setObjectName(u"spinBox_num_tries")
        sizePolicy14.setHeightForWidth(self.spinBox_num_tries.sizePolicy().hasHeightForWidth())
        self.spinBox_num_tries.setSizePolicy(sizePolicy14)
        self.spinBox_num_tries.setMinimum(1)
        self.spinBox_num_tries.setMaximum(9999)
        self.spinBox_num_tries.setValue(32)

        self.gridLayout_10.addWidget(self.spinBox_num_tries, 0, 5, 1, 1)

        self.doubleSpinBox_fit_tmin = QDoubleSpinBox(self.groupBox_8)
        self.doubleSpinBox_fit_tmin.setObjectName(u"doubleSpinBox_fit_tmin")
        sizePolicy15 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy15.setHorizontalStretch(0)
        sizePolicy15.setVerticalStretch(0)
        sizePolicy15.setHeightForWidth(self.doubleSpinBox_fit_tmin.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_fit_tmin.setSizePolicy(sizePolicy15)
        self.doubleSpinBox_fit_tmin.setDecimals(4)
        self.doubleSpinBox_fit_tmin.setMaximum(9999.000000000000000)

        self.gridLayout_10.addWidget(self.doubleSpinBox_fit_tmin, 4, 5, 1, 1)

        self.label_14 = QLabel(self.groupBox_8)
        self.label_14.setObjectName(u"label_14")
        sizePolicy16 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy16.setHorizontalStretch(0)
        sizePolicy16.setVerticalStretch(0)
        sizePolicy16.setHeightForWidth(self.label_14.sizePolicy().hasHeightForWidth())
        self.label_14.setSizePolicy(sizePolicy16)

        self.gridLayout_10.addWidget(self.label_14, 4, 6, 1, 1)

        self.label_12 = QLabel(self.groupBox_8)
        self.label_12.setObjectName(u"label_12")
        sizePolicy16.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy16)

        self.gridLayout_10.addWidget(self.label_12, 4, 0, 1, 2)

        self.label_10 = QLabel(self.groupBox_8)
        self.label_10.setObjectName(u"label_10")
        sizePolicy13.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy13)

        self.gridLayout_10.addWidget(self.label_10, 0, 10, 1, 1)

        self.doubleSpinBox_bsl_tmax = QDoubleSpinBox(self.groupBox_8)
        self.doubleSpinBox_bsl_tmax.setObjectName(u"doubleSpinBox_bsl_tmax")
        sizePolicy15.setHeightForWidth(self.doubleSpinBox_bsl_tmax.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_bsl_tmax.setSizePolicy(sizePolicy15)
        self.doubleSpinBox_bsl_tmax.setDecimals(4)
        self.doubleSpinBox_bsl_tmax.setMaximum(9999.000000000000000)

        self.gridLayout_10.addWidget(self.doubleSpinBox_bsl_tmax, 1, 7, 1, 1)

        self.label_20 = QLabel(self.groupBox_8)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_10.addWidget(self.label_20, 1, 8, 1, 1)

        self.label_13 = QLabel(self.groupBox_8)
        self.label_13.setObjectName(u"label_13")
        sizePolicy16.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy16)

        self.gridLayout_10.addWidget(self.label_13, 4, 4, 1, 1)

        self.doubleSpinBox_bsl_tmin = QDoubleSpinBox(self.groupBox_8)
        self.doubleSpinBox_bsl_tmin.setObjectName(u"doubleSpinBox_bsl_tmin")
        sizePolicy15.setHeightForWidth(self.doubleSpinBox_bsl_tmin.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_bsl_tmin.setSizePolicy(sizePolicy15)
        self.doubleSpinBox_bsl_tmin.setDecimals(4)
        self.doubleSpinBox_bsl_tmin.setMinimum(-99999.000000000000000)
        self.doubleSpinBox_bsl_tmin.setMaximum(9999.000000000000000)

        self.gridLayout_10.addWidget(self.doubleSpinBox_bsl_tmin, 1, 5, 1, 1)

        self.comboBox_bsl_tunit = QComboBox(self.groupBox_8)
        self.comboBox_bsl_tunit.addItem("")
        self.comboBox_bsl_tunit.addItem("")
        self.comboBox_bsl_tunit.addItem("")
        self.comboBox_bsl_tunit.addItem("")
        self.comboBox_bsl_tunit.addItem("")
        self.comboBox_bsl_tunit.addItem("")
        self.comboBox_bsl_tunit.addItem("")
        self.comboBox_bsl_tunit.setObjectName(u"comboBox_bsl_tunit")
        sizePolicy12.setHeightForWidth(self.comboBox_bsl_tunit.sizePolicy().hasHeightForWidth())
        self.comboBox_bsl_tunit.setSizePolicy(sizePolicy12)

        self.gridLayout_10.addWidget(self.comboBox_bsl_tunit, 1, 3, 1, 1)

        self.label_18 = QLabel(self.groupBox_8)
        self.label_18.setObjectName(u"label_18")
        sizePolicy16.setHeightForWidth(self.label_18.sizePolicy().hasHeightForWidth())
        self.label_18.setSizePolicy(sizePolicy16)

        self.gridLayout_10.addWidget(self.label_18, 1, 4, 1, 1)

        self.label_8 = QLabel(self.groupBox_8)
        self.label_8.setObjectName(u"label_8")
        sizePolicy13.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy13)

        self.gridLayout_10.addWidget(self.label_8, 0, 0, 1, 1)

        self.spinBox_num_workers = QSpinBox(self.groupBox_8)
        self.spinBox_num_workers.setObjectName(u"spinBox_num_workers")
        sizePolicy14.setHeightForWidth(self.spinBox_num_workers.sizePolicy().hasHeightForWidth())
        self.spinBox_num_workers.setSizePolicy(sizePolicy14)
        self.spinBox_num_workers.setMinimum(0)
        self.spinBox_num_workers.setMaximum(320)
        self.spinBox_num_workers.setValue(4)

        self.gridLayout_10.addWidget(self.spinBox_num_workers, 0, 2, 1, 1)

        self.label_16 = QLabel(self.groupBox_8)
        self.label_16.setObjectName(u"label_16")
        sizePolicy16.setHeightForWidth(self.label_16.sizePolicy().hasHeightForWidth())
        self.label_16.setSizePolicy(sizePolicy16)

        self.gridLayout_10.addWidget(self.label_16, 1, 0, 1, 1)

        self.comboBox_opt_method = QComboBox(self.groupBox_8)
        self.comboBox_opt_method.addItem("")
        self.comboBox_opt_method.addItem("")
        self.comboBox_opt_method.addItem("")
        self.comboBox_opt_method.addItem("")
        self.comboBox_opt_method.addItem("")
        self.comboBox_opt_method.addItem("")
        self.comboBox_opt_method.setObjectName(u"comboBox_opt_method")
        sizePolicy17 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy17.setHorizontalStretch(3)
        sizePolicy17.setVerticalStretch(0)
        sizePolicy17.setHeightForWidth(self.comboBox_opt_method.sizePolicy().hasHeightForWidth())
        self.comboBox_opt_method.setSizePolicy(sizePolicy17)

        self.gridLayout_10.addWidget(self.comboBox_opt_method, 0, 15, 1, 2)

        self.label_15 = QLabel(self.groupBox_8)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_10.addWidget(self.label_15, 4, 8, 1, 1)

        self.comboBox_fit_method = QComboBox(self.groupBox_8)
        self.comboBox_fit_method.addItem("")
        self.comboBox_fit_method.addItem("")
        self.comboBox_fit_method.setObjectName(u"comboBox_fit_method")

        self.gridLayout_10.addWidget(self.comboBox_fit_method, 0, 7, 1, 1)

        self.doubleSpinBox_fit_tmax = QDoubleSpinBox(self.groupBox_8)
        self.doubleSpinBox_fit_tmax.setObjectName(u"doubleSpinBox_fit_tmax")
        sizePolicy15.setHeightForWidth(self.doubleSpinBox_fit_tmax.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_fit_tmax.setSizePolicy(sizePolicy15)
        self.doubleSpinBox_fit_tmax.setDecimals(4)
        self.doubleSpinBox_fit_tmax.setMaximum(9999.000000000000000)

        self.gridLayout_10.addWidget(self.doubleSpinBox_fit_tmax, 4, 7, 1, 1)

        self.checkBox_fit_trange = QCheckBox(self.groupBox_8)
        self.checkBox_fit_trange.setObjectName(u"checkBox_fit_trange")
        self.checkBox_fit_trange.setChecked(True)

        self.gridLayout_10.addWidget(self.checkBox_fit_trange, 4, 2, 1, 1)

        self.comboBox_bsl_trange = QComboBox(self.groupBox_8)
        self.comboBox_bsl_trange.addItem("")
        self.comboBox_bsl_trange.addItem("")
        self.comboBox_bsl_trange.addItem("")
        self.comboBox_bsl_trange.addItem("")
        self.comboBox_bsl_trange.setObjectName(u"comboBox_bsl_trange")

        self.gridLayout_10.addWidget(self.comboBox_bsl_trange, 1, 2, 1, 1)

        self.checkBox_show_groundstate = QCheckBox(self.groupBox_8)
        self.checkBox_show_groundstate.setObjectName(u"checkBox_show_groundstate")

        self.gridLayout_10.addWidget(self.checkBox_show_groundstate, 4, 10, 1, 1)

        self.progressBar_fit = QProgressBar(self.groupBox_8)
        self.progressBar_fit.setObjectName(u"progressBar_fit")
        sizePolicy17.setHeightForWidth(self.progressBar_fit.sizePolicy().hasHeightForWidth())
        self.progressBar_fit.setSizePolicy(sizePolicy17)
        self.progressBar_fit.setValue(24)

        self.gridLayout_10.addWidget(self.progressBar_fit, 1, 15, 1, 2)

        self.pushButton_plot = QPushButton(self.groupBox_8)
        self.pushButton_plot.setObjectName(u"pushButton_plot")

        self.gridLayout_10.addWidget(self.pushButton_plot, 4, 16, 1, 1)

        self.pushButton_fit = QPushButton(self.groupBox_8)
        self.pushButton_fit.setObjectName(u"pushButton_fit")
        sizePolicy14.setHeightForWidth(self.pushButton_fit.sizePolicy().hasHeightForWidth())
        self.pushButton_fit.setSizePolicy(sizePolicy14)

        self.gridLayout_10.addWidget(self.pushButton_fit, 4, 15, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_8)

        self.splitter_3.addWidget(self.layoutWidget)

        self.gridLayout_9.addWidget(self.splitter_3, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1557, 24))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.comboBox_fit_tunit.setCurrentIndex(1)
        self.comboBox_bsl_tunit.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Kinetics-Modeling", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Kinetics Data", None))
        self.pushButton_load.setText(QCoreApplication.translate("MainWindow", u"Load Results", None))
        self.checkBox_kinetics_profiles.setText(QCoreApplication.translate("MainWindow", u"Kinetics profiles", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Model", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Graph", None))
        self.label_graph.setText("")
        self.pushButton_save_model.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"State-Matrix", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Number of States", None))
        self.checkBox_m43.setText(QCoreApplication.translate("MainWindow", u"m34", None))
        self.checkBox_m31.setText(QCoreApplication.translate("MainWindow", u"m13", None))
        self.checkBox_m11.setText(QCoreApplication.translate("MainWindow", u"m11", None))
        self.checkBox_m64.setText(QCoreApplication.translate("MainWindow", u"m40", None))
        self.checkBox_m33.setText(QCoreApplication.translate("MainWindow", u"m33", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"State2", None))
        self.checkBox_m22.setText(QCoreApplication.translate("MainWindow", u"m22", None))
        self.checkBox_m32.setText(QCoreApplication.translate("MainWindow", u"m23", None))
        self.checkBox_m61.setText(QCoreApplication.translate("MainWindow", u"m10", None))
        self.checkBox_m44.setText(QCoreApplication.translate("MainWindow", u"m44", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"GS", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"State4", None))
        self.checkBox_m53.setText(QCoreApplication.translate("MainWindow", u"m35", None))
        self.checkBox_m41.setText(QCoreApplication.translate("MainWindow", u"m14", None))
        self.checkBox_m54.setText(QCoreApplication.translate("MainWindow", u"m45", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"State1", None))
        self.checkBox_m55.setText(QCoreApplication.translate("MainWindow", u"m55", None))
        self.checkBox_m63.setText(QCoreApplication.translate("MainWindow", u"m30", None))
        self.checkBox_m21.setText(QCoreApplication.translate("MainWindow", u"m12", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"State5", None))
        self.checkBox_m52.setText(QCoreApplication.translate("MainWindow", u"m25", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"State3", None))
        self.checkBox_m62.setText(QCoreApplication.translate("MainWindow", u"m20", None))
        self.checkBox_m51.setText(QCoreApplication.translate("MainWindow", u"m15", None))
        self.checkBox_m65.setText(QCoreApplication.translate("MainWindow", u"m50", None))
        self.checkBox_m42.setText(QCoreApplication.translate("MainWindow", u"m24", None))
        self.comboBox_model.setItemText(0, QCoreApplication.translate("MainWindow", u"parallel", None))
        self.comboBox_model.setItemText(1, QCoreApplication.translate("MainWindow", u"sequential", None))
        self.comboBox_model.setItemText(2, QCoreApplication.translate("MainWindow", u"advanced", None))

        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Parameters", None))
        self.pushButton_updatemodel.setText(QCoreApplication.translate("MainWindow", u"Update", None))
        self.pushButton_load_model.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Global Fitting", None))
        self.groupBox_kprofiles.setTitle(QCoreApplication.translate("MainWindow", u"Profile Fitting", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"]", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.comboBox_fit_tunit.setItemText(0, QCoreApplication.translate("MainWindow", u"ks", None))
        self.comboBox_fit_tunit.setItemText(1, QCoreApplication.translate("MainWindow", u"s", None))
        self.comboBox_fit_tunit.setItemText(2, QCoreApplication.translate("MainWindow", u"ms", None))
        self.comboBox_fit_tunit.setItemText(3, QCoreApplication.translate("MainWindow", u"\u00b5s", None))
        self.comboBox_fit_tunit.setItemText(4, QCoreApplication.translate("MainWindow", u"ns", None))
        self.comboBox_fit_tunit.setItemText(5, QCoreApplication.translate("MainWindow", u"ps", None))
        self.comboBox_fit_tunit.setItemText(6, QCoreApplication.translate("MainWindow", u"fs", None))

        self.label_19.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Total tries:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Progress", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Time Range for Fitting", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Optimization Method:", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u")", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"[", None))
        self.comboBox_bsl_tunit.setItemText(0, QCoreApplication.translate("MainWindow", u"ks", None))
        self.comboBox_bsl_tunit.setItemText(1, QCoreApplication.translate("MainWindow", u"s", None))
        self.comboBox_bsl_tunit.setItemText(2, QCoreApplication.translate("MainWindow", u"ms", None))
        self.comboBox_bsl_tunit.setItemText(3, QCoreApplication.translate("MainWindow", u"\u00b5s", None))
        self.comboBox_bsl_tunit.setItemText(4, QCoreApplication.translate("MainWindow", u"ns", None))
        self.comboBox_bsl_tunit.setItemText(5, QCoreApplication.translate("MainWindow", u"ps", None))
        self.comboBox_bsl_tunit.setItemText(6, QCoreApplication.translate("MainWindow", u"fs", None))

        self.label_18.setText(QCoreApplication.translate("MainWindow", u"[", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Workers:", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Time Range for Baseline", None))
        self.comboBox_opt_method.setItemText(0, QCoreApplication.translate("MainWindow", u"L-BFGS-B", None))
        self.comboBox_opt_method.setItemText(1, QCoreApplication.translate("MainWindow", u"TNC", None))
        self.comboBox_opt_method.setItemText(2, QCoreApplication.translate("MainWindow", u"SLSQP", None))
        self.comboBox_opt_method.setItemText(3, QCoreApplication.translate("MainWindow", u"Powell", None))
        self.comboBox_opt_method.setItemText(4, QCoreApplication.translate("MainWindow", u"trust-constr", None))
        self.comboBox_opt_method.setItemText(5, QCoreApplication.translate("MainWindow", u"RandomChoice", None))

        self.label_15.setText(QCoreApplication.translate("MainWindow", u"]", None))
        self.comboBox_fit_method.setItemText(0, QCoreApplication.translate("MainWindow", u"IndividualFit", None))
        self.comboBox_fit_method.setItemText(1, QCoreApplication.translate("MainWindow", u"JointFit", None))

        self.checkBox_fit_trange.setText(QCoreApplication.translate("MainWindow", u"Enable", None))
        self.comboBox_bsl_trange.setItemText(0, QCoreApplication.translate("MainWindow", u"Disabled", None))
        self.comboBox_bsl_trange.setItemText(1, QCoreApplication.translate("MainWindow", u"Constant", None))
        self.comboBox_bsl_trange.setItemText(2, QCoreApplication.translate("MainWindow", u"Linear", None))
        self.comboBox_bsl_trange.setItemText(3, QCoreApplication.translate("MainWindow", u"Quadratic", None))

        self.checkBox_show_groundstate.setText(QCoreApplication.translate("MainWindow", u"Show Ground State", None))
        self.pushButton_plot.setText(QCoreApplication.translate("MainWindow", u"Plot", None))
        self.pushButton_fit.setText(QCoreApplication.translate("MainWindow", u"Fit", None))
    # retranslateUi

