from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, 
    QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QCheckBox, QComboBox,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import QDir, Qt
import sys
import os
import numpy as np
from generated_ui import Ui_MainWindow
import glob
from trxas_dataset import TrXASDataset
import pyqtgraph as pg

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)
pg.setConfigOptions(imageAxisOrder='row-major')


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.init_ui()
        self.image = None
        self.roi = None
        self.current_dataset = TrXASDataset('/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099')
        self.current_dataset.normalize()
        self.setup_imageview()
        self.update_colormap()
        self.plot_dataset()

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        # self.model.setNameFilterDisables(False) #enable the filters.
        self.treeView_fs.setModel(self.model)
        self.treeView_fs.setRootIndex(self.model.index(QDir.homePath()))
        self.treeView_fs.hideColumn(2)  # hide type
        # self.treeView_fs.hideColumn(3)  # hide Date
        self.treeView_fs.selectionModel().selectionChanged.connect(self.selection_changed)
        self.select_rawfolder('/Users/mqichu/Documents/trxas/XTA_data')
        self.comboBox_cmap.currentIndexChanged.connect(self.update_colormap)
        self.spinBox_roix.valueChanged.connect(self.update_roi)
        self.spinBox_roiy.valueChanged.connect(self.update_roi)

    def selection_changed(self, selected, deselected):
        indexes = self.treeView_fs.selectionModel().selectedIndexes()
        if indexes:
            index = indexes[0]
            file_path = self.model.filePath(index)
            self.current_dataset = TrXASDataset(file_path)
            self.current_dataset.normalize()
            self.plot_dataset()

    def init_ui(self):
        self.pushButton_select_rawfolder.clicked.connect(self.select_rawfolder)
        self.pushButton_select_outputfolder.clicked.connect(self.select_outputfolder)
        self.pushButton_process.clicked.connect(self.process)
    
    def setup_imageview(self):
        # Get the ViewBox from ImageView
        self.view = self.pg_hdl_img2d.getView()
        # Add crosshair
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.view.addItem(self.vLine, ignoreBounds=True)
        self.view.addItem(self.hLine, ignoreBounds=True)
        # Connect mouse events
        self.proxy = pg.SignalProxy(self.view.scene().sigMouseMoved,
                                  rateLimit=60,
                                  slot=self.mouseMoved)
                # Initialize plots
        self.h_curve = self.pg_hdl_hline.plot(pen='r')
        self.v_curve = self.pg_hdl_vline.plot(pen='b')
        self.zoomin_image = pg.ImageItem()
        self.pg_hdl_zoomin.addItem(self.zoomin_image)
        self.pg_hdl_zoomin.setAspectLocked(False)
    
    def update_roi(self, value, position=None):
        # value is a positional placeholder for the signal. It is not used.
        roi_size = (self.spinBox_roix.value(), self.spinBox_roiy.value())
        if self.roi is None:
            self.roi = pg.RectROI([0, 0], roi_size, pen="r")
            self.pg_hdl_img2d.addItem(self.roi)

        # update size
        if self.roi.size() != roi_size:
            self.roi.setSize(roi_size)

        if position is not None and self.roi.pos() != position:
            self.roi.setPos((position[0] - roi_size[0] / 2,
                             position[1] - roi_size[1] / 2))

    def mouseMoved(self, evt):
        pos = evt[0]
        if self.view.sceneBoundingRect().contains(pos):
            mouse_point = self.view.mapSceneToView(pos)
            x = int(mouse_point.x())
            y = int(mouse_point.y())
            
            # Update crosshair position
            self.vLine.setPos(x)
            self.hLine.setPos(y)
            
            # Update line cuts if within image bounds
            if (0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]):
                # Get horizontal and vertical cuts
                horizontal_data = self.image[y, :]
                vertical_data = self.image[:, x]
                # Create y-axis values for vertical cut
                x_positions = np.arange(len(horizontal_data))
                y_positions = np.arange(len(vertical_data))
                
                # Update horizontal cut
                self.h_curve.setData(x_positions, horizontal_data)
                self.v_curve.setData(vertical_data, y_positions)
                
                # Optional: Update plot ranges
                self.pg_hdl_hline.setRange(xRange=[0, self.image.shape[1]])
                # self.pg_hdl_vline.setRange(xRange=[0, self.image.shape[0]])
                self.update_roi(None, position=(x, y))
            self.update_zoomed_view()

    def update_zoomed_view(self):
        if self.roi is None:
            return
        image_data = self.image 
        roi_data = self.roi.getArrayRegion(image_data, self.pg_hdl_img2d.getImageItem())
        if roi_data.size > 0:
            self.zoomin_image.setImage(roi_data) 
    
    def update_colormap(self):
        cmap = self.comboBox_cmap.currentText()
        cmap = pg.colormap.getFromMatplotlib(cmap)
        self.pg_hdl_img2d.setColorMap(cmap)
        self.zoomin_image.setColorMap(cmap)
    
    def plot_dataset(self):
        data = self.current_dataset.get_energy_vs_time(channel=1).T
        self.pg_hdl_img2d.getView().setAspectLocked(False)
        self.pg_hdl_img2d.setImage(data)
        self.image = data
    
    def select_rawfolder(self, folder_path=None):
        if folder_path is None:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder_path:
            self.lineEdit_rawfolder.setText(folder_path)
            flist = os.listdir(folder_path)
            indexes = [int(f[-5:]) for f in flist]
            self.spinBox_fileindex_min.setValue(min(indexes))
            self.spinBox_fileindex_max.setValue(max(indexes))
            self.model.setRootPath(folder_path)
            self.treeView_fs.setRootIndex(self.model.index(folder_path))

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
