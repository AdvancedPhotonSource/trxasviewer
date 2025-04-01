# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'viewer.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMenuBar, QProgressBar, QPushButton, QRadioButton,
    QSizePolicy, QSpinBox, QSplitter, QStatusBar,
    QTabWidget, QToolButton, QTreeView, QVBoxLayout,
    QWidget)

from pyqtgraph import (ImageView, PlotWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1758, 882)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_19 = QGridLayout(self.centralwidget)
        self.gridLayout_19.setObjectName(u"gridLayout_19")
        self.splitter_2 = QSplitter(self.centralwidget)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Orientation.Horizontal)
        self.layoutWidget = QWidget(self.splitter_2)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.groupBox_2 = QGroupBox(self.layoutWidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setMaximumSize(QSize(1200, 16777215))
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_select_rawfolder = QPushButton(self.groupBox_2)
        self.pushButton_select_rawfolder.setObjectName(u"pushButton_select_rawfolder")

        self.horizontalLayout.addWidget(self.pushButton_select_rawfolder)

        self.lineEdit_rawfolder = QLineEdit(self.groupBox_2)
        self.lineEdit_rawfolder.setObjectName(u"lineEdit_rawfolder")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEdit_rawfolder.sizePolicy().hasHeightForWidth())
        self.lineEdit_rawfolder.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.lineEdit_rawfolder)

        self.toolButton_refresh = QToolButton(self.groupBox_2)
        self.toolButton_refresh.setObjectName(u"toolButton_refresh")

        self.horizontalLayout.addWidget(self.toolButton_refresh)


        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.treeView_fs = QTreeView(self.groupBox_2)
        self.treeView_fs.setObjectName(u"treeView_fs")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(2)
        sizePolicy2.setHeightForWidth(self.treeView_fs.sizePolicy().hasHeightForWidth())
        self.treeView_fs.setSizePolicy(sizePolicy2)
        self.treeView_fs.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView_fs.header().setCascadingSectionResizes(False)
        self.treeView_fs.header().setMinimumSectionSize(30)

        self.gridLayout_2.addWidget(self.treeView_fs, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.groupBox_5 = QGroupBox(self.layoutWidget)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(1)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy3)
        self.gridLayout_4 = QGridLayout(self.groupBox_5)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(2, 2, 2, 2)
        self.pushButton_select_savefname = QPushButton(self.groupBox_5)
        self.pushButton_select_savefname.setObjectName(u"pushButton_select_savefname")

        self.gridLayout_4.addWidget(self.pushButton_select_savefname, 7, 2, 1, 1)

        self.pushButton_replot = QPushButton(self.groupBox_5)
        self.pushButton_replot.setObjectName(u"pushButton_replot")

        self.gridLayout_4.addWidget(self.pushButton_replot, 7, 3, 1, 1)

        self.groupBox_10 = QGroupBox(self.groupBox_5)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.gridLayout_12 = QGridLayout(self.groupBox_10)
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.gridLayout_12.setContentsMargins(2, 2, 2, 2)
        self.radioButton_selection_by_index = QRadioButton(self.groupBox_10)
        self.radioButton_selection_by_index.setObjectName(u"radioButton_selection_by_index")
        self.radioButton_selection_by_index.setEnabled(True)
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.radioButton_selection_by_index.sizePolicy().hasHeightForWidth())
        self.radioButton_selection_by_index.setSizePolicy(sizePolicy4)

        self.gridLayout_12.addWidget(self.radioButton_selection_by_index, 0, 1, 1, 1)

        self.radioButton_selection_by_mouse = QRadioButton(self.groupBox_10)
        self.radioButton_selection_by_mouse.setObjectName(u"radioButton_selection_by_mouse")
        sizePolicy4.setHeightForWidth(self.radioButton_selection_by_mouse.sizePolicy().hasHeightForWidth())
        self.radioButton_selection_by_mouse.setSizePolicy(sizePolicy4)
        self.radioButton_selection_by_mouse.setChecked(True)

        self.gridLayout_12.addWidget(self.radioButton_selection_by_mouse, 0, 0, 1, 1)

        self.spinBox_fileindex_max = QSpinBox(self.groupBox_10)
        self.spinBox_fileindex_max.setObjectName(u"spinBox_fileindex_max")
        self.spinBox_fileindex_max.setEnabled(False)
        sizePolicy4.setHeightForWidth(self.spinBox_fileindex_max.sizePolicy().hasHeightForWidth())
        self.spinBox_fileindex_max.setSizePolicy(sizePolicy4)
        self.spinBox_fileindex_max.setMaximum(9999)

        self.gridLayout_12.addWidget(self.spinBox_fileindex_max, 0, 4, 1, 1)

        self.spinBox_fileindex_min = QSpinBox(self.groupBox_10)
        self.spinBox_fileindex_min.setObjectName(u"spinBox_fileindex_min")
        self.spinBox_fileindex_min.setEnabled(False)
        sizePolicy4.setHeightForWidth(self.spinBox_fileindex_min.sizePolicy().hasHeightForWidth())
        self.spinBox_fileindex_min.setSizePolicy(sizePolicy4)
        self.spinBox_fileindex_min.setMaximum(9999)

        self.gridLayout_12.addWidget(self.spinBox_fileindex_min, 0, 3, 1, 1)

        self.comboBox_fileindex_prefix = QComboBox(self.groupBox_10)
        self.comboBox_fileindex_prefix.setObjectName(u"comboBox_fileindex_prefix")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.comboBox_fileindex_prefix.sizePolicy().hasHeightForWidth())
        self.comboBox_fileindex_prefix.setSizePolicy(sizePolicy5)
        self.comboBox_fileindex_prefix.setMinimumSize(QSize(0, 0))

        self.gridLayout_12.addWidget(self.comboBox_fileindex_prefix, 0, 2, 1, 1)


        self.gridLayout_4.addWidget(self.groupBox_10, 5, 0, 1, 4)

        self.label_2 = QLabel(self.groupBox_5)
        self.label_2.setObjectName(u"label_2")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy6)

        self.gridLayout_4.addWidget(self.label_2, 7, 0, 1, 1)

        self.groupBox_timing = QGroupBox(self.groupBox_5)
        self.groupBox_timing.setObjectName(u"groupBox_timing")
        self.gridLayout_5 = QGridLayout(self.groupBox_timing)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(2, 2, 2, 2)
        self.spinBox_syncbunch_number = QSpinBox(self.groupBox_timing)
        self.spinBox_syncbunch_number.setObjectName(u"spinBox_syncbunch_number")
        self.spinBox_syncbunch_number.setMaximum(999999)
        self.spinBox_syncbunch_number.setValue(1820)

        self.gridLayout_5.addWidget(self.spinBox_syncbunch_number, 0, 3, 1, 1)

        self.radioButton_sync_bunch = QRadioButton(self.groupBox_timing)
        self.radioButton_sync_bunch.setObjectName(u"radioButton_sync_bunch")
        self.radioButton_sync_bunch.setChecked(True)

        self.gridLayout_5.addWidget(self.radioButton_sync_bunch, 0, 2, 1, 1)

        self.radioButton_sync_time = QRadioButton(self.groupBox_timing)
        self.radioButton_sync_time.setObjectName(u"radioButton_sync_time")

        self.gridLayout_5.addWidget(self.radioButton_sync_time, 0, 0, 1, 1)

        self.doubleSpinBox_sync_time_us = QDoubleSpinBox(self.groupBox_timing)
        self.doubleSpinBox_sync_time_us.setObjectName(u"doubleSpinBox_sync_time_us")
        self.doubleSpinBox_sync_time_us.setEnabled(False)
        self.doubleSpinBox_sync_time_us.setDecimals(6)
        self.doubleSpinBox_sync_time_us.setMaximum(999999.000000000000000)

        self.gridLayout_5.addWidget(self.doubleSpinBox_sync_time_us, 0, 1, 1, 1)


        self.gridLayout_4.addWidget(self.groupBox_timing, 1, 0, 1, 4)

        self.groupBox_8 = QGroupBox(self.groupBox_5)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.gridLayout_9 = QGridLayout(self.groupBox_8)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.gridLayout_9.setContentsMargins(2, 2, 2, 2)
        self.spinBox_orbitals_number = QSpinBox(self.groupBox_8)
        self.spinBox_orbitals_number.setObjectName(u"spinBox_orbitals_number")
        sizePolicy4.setHeightForWidth(self.spinBox_orbitals_number.sizePolicy().hasHeightForWidth())
        self.spinBox_orbitals_number.setSizePolicy(sizePolicy4)
        self.spinBox_orbitals_number.setMinimum(1)
        self.spinBox_orbitals_number.setMaximum(999999)
        self.spinBox_orbitals_number.setValue(5)

        self.gridLayout_9.addWidget(self.spinBox_orbitals_number, 0, 3, 1, 1)

        self.label_6 = QLabel(self.groupBox_8)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_9.addWidget(self.label_6, 0, 2, 1, 1)

        self.comboBox_groundstate_method = QComboBox(self.groupBox_8)
        self.comboBox_groundstate_method.addItem("")
        self.comboBox_groundstate_method.addItem("")
        self.comboBox_groundstate_method.setObjectName(u"comboBox_groundstate_method")

        self.gridLayout_9.addWidget(self.comboBox_groundstate_method, 0, 1, 1, 1)

        self.label_5 = QLabel(self.groupBox_8)
        self.label_5.setObjectName(u"label_5")
        sizePolicy6.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy6)

        self.gridLayout_9.addWidget(self.label_5, 0, 0, 1, 1)

        self.tabWidget_binning = QTabWidget(self.groupBox_8)
        self.tabWidget_binning.setObjectName(u"tabWidget_binning")
        self.tabWidget_binning.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget_binning.setElideMode(Qt.TextElideMode.ElideRight)
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.gridLayout_15 = QGridLayout(self.tab_3)
        self.gridLayout_15.setObjectName(u"gridLayout_15")
        self.label_7 = QLabel(self.tab_3)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_15.addWidget(self.label_7, 1, 0, 1, 1)

        self.spinBox_binning_linnum = QSpinBox(self.tab_3)
        self.spinBox_binning_linnum.setObjectName(u"spinBox_binning_linnum")
        self.spinBox_binning_linnum.setMinimum(1)
        self.spinBox_binning_linnum.setMaximum(99999)
        self.spinBox_binning_linnum.setValue(5)

        self.gridLayout_15.addWidget(self.spinBox_binning_linnum, 1, 1, 1, 1)

        self.label_binning_linmsg = QLabel(self.tab_3)
        self.label_binning_linmsg.setObjectName(u"label_binning_linmsg")

        self.gridLayout_15.addWidget(self.label_binning_linmsg, 0, 0, 1, 1)

        self.tabWidget_binning.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.gridLayout_18 = QGridLayout(self.tab_4)
        self.gridLayout_18.setObjectName(u"gridLayout_18")
        self.label_binning_logmsg = QLabel(self.tab_4)
        self.label_binning_logmsg.setObjectName(u"label_binning_logmsg")

        self.gridLayout_18.addWidget(self.label_binning_logmsg, 0, 0, 1, 2)

        self.label_11 = QLabel(self.tab_4)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_18.addWidget(self.label_11, 1, 0, 1, 1)

        self.spinBox_binning_lognum = QDoubleSpinBox(self.tab_4)
        self.spinBox_binning_lognum.setObjectName(u"spinBox_binning_lognum")
        self.spinBox_binning_lognum.setDecimals(3)
        self.spinBox_binning_lognum.setMinimum(1.000000000000000)
        self.spinBox_binning_lognum.setSingleStep(0.010000000000000)
        self.spinBox_binning_lognum.setValue(1.200000000000000)

        self.gridLayout_18.addWidget(self.spinBox_binning_lognum, 1, 1, 1, 1)

        self.tabWidget_binning.addTab(self.tab_4, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.gridLayout_16 = QGridLayout(self.tab_5)
        self.gridLayout_16.setObjectName(u"gridLayout_16")
        self.label_binbunches = QLabel(self.tab_5)
        self.label_binbunches.setObjectName(u"label_binbunches")

        self.gridLayout_16.addWidget(self.label_binbunches, 4, 0, 1, 1)

        self.label_anchorbunch = QLabel(self.tab_5)
        self.label_anchorbunch.setObjectName(u"label_anchorbunch")

        self.gridLayout_16.addWidget(self.label_anchorbunch, 3, 0, 1, 1)

        self.label_rtime3 = QLabel(self.tab_5)
        self.label_rtime3.setObjectName(u"label_rtime3")

        self.gridLayout_16.addWidget(self.label_rtime3, 0, 4, 1, 1)

        self.spinBox_numb1 = QSpinBox(self.tab_5)
        self.spinBox_numb1.setObjectName(u"spinBox_numb1")
        self.spinBox_numb1.setMinimum(-1)
        self.spinBox_numb1.setMaximum(9999)
        self.spinBox_numb1.setValue(1)

        self.gridLayout_16.addWidget(self.spinBox_numb1, 4, 2, 1, 1)

        self.spinBox_numb0 = QSpinBox(self.tab_5)
        self.spinBox_numb0.setObjectName(u"spinBox_numb0")
        self.spinBox_numb0.setMinimum(0)
        self.spinBox_numb0.setMaximum(9999)
        self.spinBox_numb0.setValue(0)

        self.gridLayout_16.addWidget(self.spinBox_numb0, 4, 1, 1, 1)

        self.spinBox_anchor4 = QSpinBox(self.tab_5)
        self.spinBox_anchor4.setObjectName(u"spinBox_anchor4")
        self.spinBox_anchor4.setMinimum(1)
        self.spinBox_anchor4.setMaximum(9999)
        self.spinBox_anchor4.setValue(1024)

        self.gridLayout_16.addWidget(self.spinBox_anchor4, 3, 5, 1, 1)

        self.spinBox_numb3 = QSpinBox(self.tab_5)
        self.spinBox_numb3.setObjectName(u"spinBox_numb3")
        self.spinBox_numb3.setMinimum(-1)
        self.spinBox_numb3.setMaximum(9999)
        self.spinBox_numb3.setValue(16)

        self.gridLayout_16.addWidget(self.spinBox_numb3, 4, 4, 1, 1)

        self.label_rtime2 = QLabel(self.tab_5)
        self.label_rtime2.setObjectName(u"label_rtime2")

        self.gridLayout_16.addWidget(self.label_rtime2, 0, 3, 1, 1)

        self.spinBox_numb2 = QSpinBox(self.tab_5)
        self.spinBox_numb2.setObjectName(u"spinBox_numb2")
        self.spinBox_numb2.setMinimum(-1)
        self.spinBox_numb2.setMaximum(9999)
        self.spinBox_numb2.setValue(4)
        self.spinBox_numb2.setDisplayIntegerBase(10)

        self.gridLayout_16.addWidget(self.spinBox_numb2, 4, 3, 1, 1)

        self.spinBox_anchor1 = QSpinBox(self.tab_5)
        self.spinBox_anchor1.setObjectName(u"spinBox_anchor1")
        self.spinBox_anchor1.setMinimum(1)
        self.spinBox_anchor1.setMaximum(9999)
        self.spinBox_anchor1.setValue(4)

        self.gridLayout_16.addWidget(self.spinBox_anchor1, 3, 2, 1, 1)

        self.spinBox_anchor2 = QSpinBox(self.tab_5)
        self.spinBox_anchor2.setObjectName(u"spinBox_anchor2")
        self.spinBox_anchor2.setMinimum(1)
        self.spinBox_anchor2.setMaximum(9999)
        self.spinBox_anchor2.setValue(32)

        self.gridLayout_16.addWidget(self.spinBox_anchor2, 3, 3, 1, 1)

        self.label_rtime1 = QLabel(self.tab_5)
        self.label_rtime1.setObjectName(u"label_rtime1")

        self.gridLayout_16.addWidget(self.label_rtime1, 0, 2, 1, 1)

        self.label_18 = QLabel(self.tab_5)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_16.addWidget(self.label_18, 0, 0, 1, 1)

        self.spinBox_anchor3 = QSpinBox(self.tab_5)
        self.spinBox_anchor3.setObjectName(u"spinBox_anchor3")
        self.spinBox_anchor3.setMinimum(1)
        self.spinBox_anchor3.setMaximum(9999)
        self.spinBox_anchor3.setValue(256)

        self.gridLayout_16.addWidget(self.spinBox_anchor3, 3, 4, 1, 1)

        self.label_rtime4 = QLabel(self.tab_5)
        self.label_rtime4.setObjectName(u"label_rtime4")

        self.gridLayout_16.addWidget(self.label_rtime4, 0, 5, 1, 1)

        self.label_rtime0 = QLabel(self.tab_5)
        self.label_rtime0.setObjectName(u"label_rtime0")

        self.gridLayout_16.addWidget(self.label_rtime0, 0, 1, 1, 1)

        self.spinBox_anchor0 = QSpinBox(self.tab_5)
        self.spinBox_anchor0.setObjectName(u"spinBox_anchor0")
        self.spinBox_anchor0.setMinimum(1)
        self.spinBox_anchor0.setMaximum(9999)
        self.spinBox_anchor0.setValue(1)

        self.gridLayout_16.addWidget(self.spinBox_anchor0, 3, 1, 1, 1)

        self.spinBox_numb4 = QSpinBox(self.tab_5)
        self.spinBox_numb4.setObjectName(u"spinBox_numb4")
        self.spinBox_numb4.setMinimum(-1)
        self.spinBox_numb4.setMaximum(9999)
        self.spinBox_numb4.setValue(64)

        self.gridLayout_16.addWidget(self.spinBox_numb4, 4, 5, 1, 1)

        self.tabWidget_binning.addTab(self.tab_5, "")

        self.gridLayout_9.addWidget(self.tabWidget_binning, 1, 0, 1, 4)


        self.gridLayout_4.addWidget(self.groupBox_8, 2, 0, 1, 4)

        self.progressBar = QProgressBar(self.groupBox_5)
        self.progressBar.setObjectName(u"progressBar")
        sizePolicy5.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progressBar.setSizePolicy(sizePolicy5)
        self.progressBar.setValue(0)

        self.gridLayout_4.addWidget(self.progressBar, 7, 1, 1, 1)

        self.groupBox_6 = QGroupBox(self.groupBox_5)
        self.groupBox_6.setObjectName(u"groupBox_6")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.groupBox_6.sizePolicy().hasHeightForWidth())
        self.groupBox_6.setSizePolicy(sizePolicy7)
        self.gridLayout_11 = QGridLayout(self.groupBox_6)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.gridLayout_11.setContentsMargins(2, 2, 2, 2)
        self.label_13 = QLabel(self.groupBox_6)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_11.addWidget(self.label_13, 1, 0, 1, 1)

        self.comboBox = QComboBox(self.groupBox_6)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")

        self.gridLayout_11.addWidget(self.comboBox, 1, 1, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.doubleSpinBox_kinetics_edelta1 = QDoubleSpinBox(self.groupBox_6)
        self.doubleSpinBox_kinetics_edelta1.setObjectName(u"doubleSpinBox_kinetics_edelta1")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.doubleSpinBox_kinetics_edelta1.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_kinetics_edelta1.setSizePolicy(sizePolicy8)
        self.doubleSpinBox_kinetics_edelta1.setDecimals(4)
        self.doubleSpinBox_kinetics_edelta1.setSingleStep(0.001000000000000)

        self.gridLayout_3.addWidget(self.doubleSpinBox_kinetics_edelta1, 1, 1, 1, 1)

        self.doubleSpinBox_kinetics_ecenter1 = QDoubleSpinBox(self.groupBox_6)
        self.doubleSpinBox_kinetics_ecenter1.setObjectName(u"doubleSpinBox_kinetics_ecenter1")
        sizePolicy8.setHeightForWidth(self.doubleSpinBox_kinetics_ecenter1.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_kinetics_ecenter1.setSizePolicy(sizePolicy8)
        self.doubleSpinBox_kinetics_ecenter1.setDecimals(4)
        self.doubleSpinBox_kinetics_ecenter1.setSingleStep(0.001000000000000)

        self.gridLayout_3.addWidget(self.doubleSpinBox_kinetics_ecenter1, 0, 1, 1, 1)

        self.checkBox_kinetics_roi4 = QCheckBox(self.groupBox_6)
        self.checkBox_kinetics_roi4.setObjectName(u"checkBox_kinetics_roi4")
        sizePolicy8.setHeightForWidth(self.checkBox_kinetics_roi4.sizePolicy().hasHeightForWidth())
        self.checkBox_kinetics_roi4.setSizePolicy(sizePolicy8)

        self.gridLayout_3.addWidget(self.checkBox_kinetics_roi4, 2, 4, 1, 1)

        self.checkBox_kinetics_roi1 = QCheckBox(self.groupBox_6)
        self.checkBox_kinetics_roi1.setObjectName(u"checkBox_kinetics_roi1")
        sizePolicy8.setHeightForWidth(self.checkBox_kinetics_roi1.sizePolicy().hasHeightForWidth())
        self.checkBox_kinetics_roi1.setSizePolicy(sizePolicy8)
        self.checkBox_kinetics_roi1.setChecked(True)

        self.gridLayout_3.addWidget(self.checkBox_kinetics_roi1, 2, 1, 1, 1)

        self.doubleSpinBox_kinetics_edelta2 = QDoubleSpinBox(self.groupBox_6)
        self.doubleSpinBox_kinetics_edelta2.setObjectName(u"doubleSpinBox_kinetics_edelta2")
        sizePolicy8.setHeightForWidth(self.doubleSpinBox_kinetics_edelta2.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_kinetics_edelta2.setSizePolicy(sizePolicy8)
        self.doubleSpinBox_kinetics_edelta2.setDecimals(4)
        self.doubleSpinBox_kinetics_edelta2.setSingleStep(0.001000000000000)

        self.gridLayout_3.addWidget(self.doubleSpinBox_kinetics_edelta2, 1, 2, 1, 1)

        self.checkBox_kinetics_roi3 = QCheckBox(self.groupBox_6)
        self.checkBox_kinetics_roi3.setObjectName(u"checkBox_kinetics_roi3")
        sizePolicy8.setHeightForWidth(self.checkBox_kinetics_roi3.sizePolicy().hasHeightForWidth())
        self.checkBox_kinetics_roi3.setSizePolicy(sizePolicy8)

        self.gridLayout_3.addWidget(self.checkBox_kinetics_roi3, 2, 3, 1, 1)

        self.doubleSpinBox_kinetics_ecenter2 = QDoubleSpinBox(self.groupBox_6)
        self.doubleSpinBox_kinetics_ecenter2.setObjectName(u"doubleSpinBox_kinetics_ecenter2")
        sizePolicy8.setHeightForWidth(self.doubleSpinBox_kinetics_ecenter2.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_kinetics_ecenter2.setSizePolicy(sizePolicy8)
        self.doubleSpinBox_kinetics_ecenter2.setDecimals(4)
        self.doubleSpinBox_kinetics_ecenter2.setSingleStep(0.001000000000000)

        self.gridLayout_3.addWidget(self.doubleSpinBox_kinetics_ecenter2, 0, 2, 1, 1)

        self.label_8 = QLabel(self.groupBox_6)
        self.label_8.setObjectName(u"label_8")
        sizePolicy8.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy8)

        self.gridLayout_3.addWidget(self.label_8, 0, 0, 1, 1)

        self.doubleSpinBox_kinetics_ecenter4 = QDoubleSpinBox(self.groupBox_6)
        self.doubleSpinBox_kinetics_ecenter4.setObjectName(u"doubleSpinBox_kinetics_ecenter4")
        self.doubleSpinBox_kinetics_ecenter4.setEnabled(False)
        sizePolicy8.setHeightForWidth(self.doubleSpinBox_kinetics_ecenter4.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_kinetics_ecenter4.setSizePolicy(sizePolicy8)
        self.doubleSpinBox_kinetics_ecenter4.setDecimals(4)
        self.doubleSpinBox_kinetics_ecenter4.setSingleStep(0.001000000000000)

        self.gridLayout_3.addWidget(self.doubleSpinBox_kinetics_ecenter4, 0, 4, 1, 1)

        self.label_4 = QLabel(self.groupBox_6)
        self.label_4.setObjectName(u"label_4")
        sizePolicy8.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy8)

        self.gridLayout_3.addWidget(self.label_4, 2, 0, 1, 1)

        self.doubleSpinBox_kinetics_ecenter3 = QDoubleSpinBox(self.groupBox_6)
        self.doubleSpinBox_kinetics_ecenter3.setObjectName(u"doubleSpinBox_kinetics_ecenter3")
        self.doubleSpinBox_kinetics_ecenter3.setEnabled(False)
        sizePolicy8.setHeightForWidth(self.doubleSpinBox_kinetics_ecenter3.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_kinetics_ecenter3.setSizePolicy(sizePolicy8)
        self.doubleSpinBox_kinetics_ecenter3.setDecimals(4)
        self.doubleSpinBox_kinetics_ecenter3.setSingleStep(0.001000000000000)

        self.gridLayout_3.addWidget(self.doubleSpinBox_kinetics_ecenter3, 0, 3, 1, 1)

        self.checkBox_kinetics_roi2 = QCheckBox(self.groupBox_6)
        self.checkBox_kinetics_roi2.setObjectName(u"checkBox_kinetics_roi2")
        sizePolicy8.setHeightForWidth(self.checkBox_kinetics_roi2.sizePolicy().hasHeightForWidth())
        self.checkBox_kinetics_roi2.setSizePolicy(sizePolicy8)
        self.checkBox_kinetics_roi2.setChecked(True)

        self.gridLayout_3.addWidget(self.checkBox_kinetics_roi2, 2, 2, 1, 1)

        self.doubleSpinBox_kinetics_edelta4 = QDoubleSpinBox(self.groupBox_6)
        self.doubleSpinBox_kinetics_edelta4.setObjectName(u"doubleSpinBox_kinetics_edelta4")
        self.doubleSpinBox_kinetics_edelta4.setEnabled(False)
        sizePolicy8.setHeightForWidth(self.doubleSpinBox_kinetics_edelta4.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_kinetics_edelta4.setSizePolicy(sizePolicy8)
        self.doubleSpinBox_kinetics_edelta4.setDecimals(4)
        self.doubleSpinBox_kinetics_edelta4.setSingleStep(0.001000000000000)

        self.gridLayout_3.addWidget(self.doubleSpinBox_kinetics_edelta4, 1, 4, 1, 1)

        self.doubleSpinBox_kinetics_edelta3 = QDoubleSpinBox(self.groupBox_6)
        self.doubleSpinBox_kinetics_edelta3.setObjectName(u"doubleSpinBox_kinetics_edelta3")
        self.doubleSpinBox_kinetics_edelta3.setEnabled(False)
        sizePolicy8.setHeightForWidth(self.doubleSpinBox_kinetics_edelta3.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_kinetics_edelta3.setSizePolicy(sizePolicy8)
        self.doubleSpinBox_kinetics_edelta3.setDecimals(4)
        self.doubleSpinBox_kinetics_edelta3.setSingleStep(0.001000000000000)

        self.gridLayout_3.addWidget(self.doubleSpinBox_kinetics_edelta3, 1, 3, 1, 1)

        self.label_12 = QLabel(self.groupBox_6)
        self.label_12.setObjectName(u"label_12")
        sizePolicy8.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy8)

        self.gridLayout_3.addWidget(self.label_12, 1, 0, 1, 1)


        self.gridLayout_11.addLayout(self.gridLayout_3, 0, 0, 1, 2)


        self.gridLayout_4.addWidget(self.groupBox_6, 3, 0, 1, 4)


        self.verticalLayout.addWidget(self.groupBox_5)

        self.splitter_2.addWidget(self.layoutWidget)
        self.splitter = QSplitter(self.splitter_2)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.groupBox = QGroupBox(self.splitter)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy9 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy9.setHorizontalStretch(2)
        sizePolicy9.setVerticalStretch(2)
        sizePolicy9.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy9)
        self.gridLayout_14 = QGridLayout(self.groupBox)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.gridLayout_14.setContentsMargins(0, 0, 0, 0)
        self.label_10 = QLabel(self.groupBox)
        self.label_10.setObjectName(u"label_10")
        sizePolicy10 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(0)
        sizePolicy10.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy10)

        self.gridLayout_14.addWidget(self.label_10, 0, 0, 1, 1)

        self.comboBox_target = QComboBox(self.groupBox)
        self.comboBox_target.addItem("")
        self.comboBox_target.addItem("")
        self.comboBox_target.addItem("")
        self.comboBox_target.setObjectName(u"comboBox_target")
        self.comboBox_target.setMinimumSize(QSize(120, 0))

        self.gridLayout_14.addWidget(self.comboBox_target, 0, 1, 1, 1)

        self.label_9 = QLabel(self.groupBox)
        self.label_9.setObjectName(u"label_9")
        sizePolicy10.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy10)

        self.gridLayout_14.addWidget(self.label_9, 0, 2, 1, 1)

        self.comboBox_channel_num = QComboBox(self.groupBox)
        self.comboBox_channel_num.addItem("")
        self.comboBox_channel_num.addItem("")
        self.comboBox_channel_num.addItem("")
        self.comboBox_channel_num.setObjectName(u"comboBox_channel_num")
        self.comboBox_channel_num.setEnabled(False)
        sizePolicy4.setHeightForWidth(self.comboBox_channel_num.sizePolicy().hasHeightForWidth())
        self.comboBox_channel_num.setSizePolicy(sizePolicy4)

        self.gridLayout_14.addWidget(self.comboBox_channel_num, 0, 3, 1, 1)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        sizePolicy10.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy10)

        self.gridLayout_14.addWidget(self.label_3, 0, 4, 1, 1)

        self.comboBox_cmap = QComboBox(self.groupBox)
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.addItem("")
        self.comboBox_cmap.setObjectName(u"comboBox_cmap")
        sizePolicy4.setHeightForWidth(self.comboBox_cmap.sizePolicy().hasHeightForWidth())
        self.comboBox_cmap.setSizePolicy(sizePolicy4)
        self.comboBox_cmap.setMaximumSize(QSize(80, 16777215))

        self.gridLayout_14.addWidget(self.comboBox_cmap, 0, 5, 1, 1)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        sizePolicy10.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy10)

        self.gridLayout_14.addWidget(self.label, 0, 6, 1, 1)

        self.spinBox_roix = QSpinBox(self.groupBox)
        self.spinBox_roix.setObjectName(u"spinBox_roix")
        self.spinBox_roix.setMinimum(5)
        self.spinBox_roix.setMaximum(999999)

        self.gridLayout_14.addWidget(self.spinBox_roix, 0, 7, 1, 1)

        self.spinBox_roiy = QSpinBox(self.groupBox)
        self.spinBox_roiy.setObjectName(u"spinBox_roiy")
        self.spinBox_roiy.setMinimum(5)
        self.spinBox_roiy.setMaximum(999999)
        self.spinBox_roiy.setSingleStep(200)

        self.gridLayout_14.addWidget(self.spinBox_roiy, 0, 8, 1, 1)

        self.gridLayout_13 = QGridLayout()
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.groupBox_9 = QGroupBox(self.groupBox)
        self.groupBox_9.setObjectName(u"groupBox_9")
        sizePolicy11 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy11.setHorizontalStretch(4)
        sizePolicy11.setVerticalStretch(3)
        sizePolicy11.setHeightForWidth(self.groupBox_9.sizePolicy().hasHeightForWidth())
        self.groupBox_9.setSizePolicy(sizePolicy11)
        self.gridLayout_6 = QGridLayout(self.groupBox_9)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.pg_hdl_img2d = ImageView(self.groupBox_9)
        self.pg_hdl_img2d.setObjectName(u"pg_hdl_img2d")
        sizePolicy12 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy12.setHorizontalStretch(4)
        sizePolicy12.setVerticalStretch(3)
        sizePolicy12.setHeightForWidth(self.pg_hdl_img2d.sizePolicy().hasHeightForWidth())
        self.pg_hdl_img2d.setSizePolicy(sizePolicy12)

        self.gridLayout_6.addWidget(self.pg_hdl_img2d, 0, 0, 1, 1)


        self.gridLayout_13.addWidget(self.groupBox_9, 0, 0, 1, 1)

        self.groupBox_vlinecut = QGroupBox(self.groupBox)
        self.groupBox_vlinecut.setObjectName(u"groupBox_vlinecut")
        sizePolicy13 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy13.setHorizontalStretch(1)
        sizePolicy13.setVerticalStretch(3)
        sizePolicy13.setHeightForWidth(self.groupBox_vlinecut.sizePolicy().hasHeightForWidth())
        self.groupBox_vlinecut.setSizePolicy(sizePolicy13)
        self.gridLayout_8 = QGridLayout(self.groupBox_vlinecut)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.pg_hdl_vline = PlotWidget(self.groupBox_vlinecut)
        self.pg_hdl_vline.setObjectName(u"pg_hdl_vline")
        sizePolicy14 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy14.setHorizontalStretch(1)
        sizePolicy14.setVerticalStretch(3)
        sizePolicy14.setHeightForWidth(self.pg_hdl_vline.sizePolicy().hasHeightForWidth())
        self.pg_hdl_vline.setSizePolicy(sizePolicy14)

        self.gridLayout_8.addWidget(self.pg_hdl_vline, 0, 0, 1, 1)


        self.gridLayout_13.addWidget(self.groupBox_vlinecut, 0, 1, 1, 1)

        self.groupBox_hlinecut = QGroupBox(self.groupBox)
        self.groupBox_hlinecut.setObjectName(u"groupBox_hlinecut")
        sizePolicy15 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy15.setHorizontalStretch(4)
        sizePolicy15.setVerticalStretch(1)
        sizePolicy15.setHeightForWidth(self.groupBox_hlinecut.sizePolicy().hasHeightForWidth())
        self.groupBox_hlinecut.setSizePolicy(sizePolicy15)
        self.gridLayout = QGridLayout(self.groupBox_hlinecut)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.pg_hdl_hline = PlotWidget(self.groupBox_hlinecut)
        self.pg_hdl_hline.setObjectName(u"pg_hdl_hline")
        sizePolicy15.setHeightForWidth(self.pg_hdl_hline.sizePolicy().hasHeightForWidth())
        self.pg_hdl_hline.setSizePolicy(sizePolicy15)

        self.gridLayout.addWidget(self.pg_hdl_hline, 0, 0, 1, 1)


        self.gridLayout_13.addWidget(self.groupBox_hlinecut, 1, 0, 1, 1)

        self.groupBox_4 = QGroupBox(self.groupBox)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy16 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy16.setHorizontalStretch(1)
        sizePolicy16.setVerticalStretch(1)
        sizePolicy16.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy16)
        self.gridLayout_10 = QGridLayout(self.groupBox_4)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setContentsMargins(0, 0, 0, 0)
        self.pg_hdl_zoomin = PlotWidget(self.groupBox_4)
        self.pg_hdl_zoomin.setObjectName(u"pg_hdl_zoomin")
        sizePolicy17 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy17.setHorizontalStretch(1)
        sizePolicy17.setVerticalStretch(0)
        sizePolicy17.setHeightForWidth(self.pg_hdl_zoomin.sizePolicy().hasHeightForWidth())
        self.pg_hdl_zoomin.setSizePolicy(sizePolicy17)

        self.gridLayout_10.addWidget(self.pg_hdl_zoomin, 0, 0, 1, 1)


        self.gridLayout_13.addWidget(self.groupBox_4, 1, 1, 1, 1)


        self.gridLayout_14.addLayout(self.gridLayout_13, 1, 0, 1, 9)

        self.splitter.addWidget(self.groupBox)
        self.groupBox_11 = QGroupBox(self.splitter)
        self.groupBox_11.setObjectName(u"groupBox_11")
        sizePolicy18 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy18.setHorizontalStretch(0)
        sizePolicy18.setVerticalStretch(0)
        sizePolicy18.setHeightForWidth(self.groupBox_11.sizePolicy().hasHeightForWidth())
        self.groupBox_11.setSizePolicy(sizePolicy18)
        self.gridLayout_7 = QGridLayout(self.groupBox_11)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.pg_hdl_kinetics = PlotWidget(self.groupBox_11)
        self.pg_hdl_kinetics.setObjectName(u"pg_hdl_kinetics")
        sizePolicy19 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy19.setHorizontalStretch(2)
        sizePolicy19.setVerticalStretch(1)
        sizePolicy19.setHeightForWidth(self.pg_hdl_kinetics.sizePolicy().hasHeightForWidth())
        self.pg_hdl_kinetics.setSizePolicy(sizePolicy19)
        self.gridLayout_17 = QGridLayout(self.pg_hdl_kinetics)
        self.gridLayout_17.setObjectName(u"gridLayout_17")

        self.gridLayout_7.addWidget(self.pg_hdl_kinetics, 0, 0, 1, 2)

        self.splitter.addWidget(self.groupBox_11)
        self.splitter_2.addWidget(self.splitter)

        self.gridLayout_19.addWidget(self.splitter_2, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1758, 23))
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)
        self.checkBox_kinetics_roi1.toggled.connect(self.doubleSpinBox_kinetics_edelta1.setEnabled)
        self.checkBox_kinetics_roi1.toggled.connect(self.doubleSpinBox_kinetics_ecenter1.setEnabled)
        self.checkBox_kinetics_roi2.toggled.connect(self.doubleSpinBox_kinetics_edelta2.setEnabled)
        self.checkBox_kinetics_roi2.toggled.connect(self.doubleSpinBox_kinetics_ecenter2.setEnabled)
        self.checkBox_kinetics_roi3.toggled.connect(self.doubleSpinBox_kinetics_edelta3.setEnabled)
        self.checkBox_kinetics_roi3.toggled.connect(self.doubleSpinBox_kinetics_ecenter3.setEnabled)
        self.checkBox_kinetics_roi4.toggled.connect(self.doubleSpinBox_kinetics_edelta4.setEnabled)
        self.checkBox_kinetics_roi4.toggled.connect(self.doubleSpinBox_kinetics_ecenter4.setEnabled)
        self.radioButton_selection_by_index.toggled.connect(self.spinBox_fileindex_min.setEnabled)
        self.radioButton_selection_by_index.toggled.connect(self.spinBox_fileindex_max.setEnabled)

        self.tabWidget_binning.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"TrXASViewer", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Rawdata", None))
        self.pushButton_select_rawfolder.setText(QCoreApplication.translate("MainWindow", u"select", None))
        self.toolButton_refresh.setText(QCoreApplication.translate("MainWindow", u"Refresh", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.pushButton_select_savefname.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.pushButton_replot.setText(QCoreApplication.translate("MainWindow", u"Process", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("MainWindow", u"File Selection", None))
        self.radioButton_selection_by_index.setText(QCoreApplication.translate("MainWindow", u"Index", None))
        self.radioButton_selection_by_mouse.setText(QCoreApplication.translate("MainWindow", u"Mouse", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Progress:", None))
        self.groupBox_timing.setTitle(QCoreApplication.translate("MainWindow", u"Sync Timing", None))
        self.radioButton_sync_bunch.setText(QCoreApplication.translate("MainWindow", u"Bunch", None))
        self.radioButton_sync_time.setText(QCoreApplication.translate("MainWindow", u"Time", None))
        self.doubleSpinBox_sync_time_us.setSuffix(QCoreApplication.translate("MainWindow", u" \u03bcs", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("MainWindow", u"Ground State Normalization and Binning", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Number of orbitals ", None))
        self.comboBox_groundstate_method.setItemText(0, QCoreApplication.translate("MainWindow", u"per_bunch", None))
        self.comboBox_groundstate_method.setItemText(1, QCoreApplication.translate("MainWindow", u"avg_bunch", None))

        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Method", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Number of bunches", None))
        self.label_binning_linmsg.setText(QCoreApplication.translate("MainWindow", u"Linear Binning:", None))
        self.tabWidget_binning.setTabText(self.tabWidget_binning.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Linear", None))
        self.label_binning_logmsg.setText(QCoreApplication.translate("MainWindow", u"Logarithmic binning:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Number of bunches Base", None))
        self.tabWidget_binning.setTabText(self.tabWidget_binning.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Log", None))
        self.label_binbunches.setText(QCoreApplication.translate("MainWindow", u"Bin Bunchs", None))
        self.label_anchorbunch.setText(QCoreApplication.translate("MainWindow", u"Anchor Bunch", None))
        self.label_rtime3.setText("")
        self.label_rtime2.setText("")
        self.label_rtime1.setText("")
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Rel-Time (\u03bcs)", None))
        self.label_rtime4.setText("")
        self.label_rtime0.setText("")
        self.tabWidget_binning.setTabText(self.tabWidget_binning.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", u"Manual", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Kinetics-Modeling", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Fitting Model", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Placeholder1", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"Placeholder2", None))

        self.checkBox_kinetics_roi4.setText(QCoreApplication.translate("MainWindow", u"ROI4", None))
        self.checkBox_kinetics_roi1.setText(QCoreApplication.translate("MainWindow", u"ROI1", None))
        self.checkBox_kinetics_roi3.setText(QCoreApplication.translate("MainWindow", u"ROI3", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"E (keV)", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Enable", None))
        self.checkBox_kinetics_roi2.setText(QCoreApplication.translate("MainWindow", u"ROI2", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"\u00b1\u03b4E (keV)", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Time-resolved XAS", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Target", None))
        self.comboBox_target.setItemText(0, QCoreApplication.translate("MainWindow", u"normalized", None))
        self.comboBox_target.setItemText(1, QCoreApplication.translate("MainWindow", u"normalized-GS", None))
        self.comboBox_target.setItemText(2, QCoreApplication.translate("MainWindow", u"raw", None))

        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Channel", None))
        self.comboBox_channel_num.setItemText(0, QCoreApplication.translate("MainWindow", u"1", None))
        self.comboBox_channel_num.setItemText(1, QCoreApplication.translate("MainWindow", u"2", None))
        self.comboBox_channel_num.setItemText(2, QCoreApplication.translate("MainWindow", u"0", None))

        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Cmap", None))
        self.comboBox_cmap.setItemText(0, QCoreApplication.translate("MainWindow", u"bwr", None))
        self.comboBox_cmap.setItemText(1, QCoreApplication.translate("MainWindow", u"jet", None))
        self.comboBox_cmap.setItemText(2, QCoreApplication.translate("MainWindow", u"Spectral", None))
        self.comboBox_cmap.setItemText(3, QCoreApplication.translate("MainWindow", u"coolwarm", None))
        self.comboBox_cmap.setItemText(4, QCoreApplication.translate("MainWindow", u"seismic", None))
        self.comboBox_cmap.setItemText(5, QCoreApplication.translate("MainWindow", u"viridis", None))
        self.comboBox_cmap.setItemText(6, QCoreApplication.translate("MainWindow", u"plasma", None))
        self.comboBox_cmap.setItemText(7, QCoreApplication.translate("MainWindow", u"inferno", None))
        self.comboBox_cmap.setItemText(8, QCoreApplication.translate("MainWindow", u"magma", None))
        self.comboBox_cmap.setItemText(9, QCoreApplication.translate("MainWindow", u"Greys", None))
        self.comboBox_cmap.setItemText(10, QCoreApplication.translate("MainWindow", u"Blues", None))

        self.label.setText(QCoreApplication.translate("MainWindow", u"ROI(x-y)", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("MainWindow", u"Data", None))
        self.groupBox_vlinecut.setTitle(QCoreApplication.translate("MainWindow", u"Vertical Linecut", None))
        self.groupBox_hlinecut.setTitle(QCoreApplication.translate("MainWindow", u"Horizontal Linecut", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Zoomin", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("MainWindow", u"Kinetics", None))
    # retranslateUi

