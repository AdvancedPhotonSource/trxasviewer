import glob
import os
import sys

import numpy as np
import pyqtgraph as pg
from generated_ui import Ui_MainWindow
from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
                               QFileSystemModel, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)
from trxas_dataset import TrXASDataset, TrXASDatasetManager

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")
pg.setConfigOptions(antialias=True)
pg.setConfigOptions(imageAxisOrder="row-major")


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.init_ui()
        self.image = None
        self.roi = None
        self.dset_manager = TrXASDatasetManager()

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
        self.treeView_fs.selectionModel().selectionChanged.connect(
            self.selection_changed
        )
        # self.select_rawfolder('/Users/mqichu/Documents/trxas/XTA_data')
        self.comboBox_cmap.currentIndexChanged.connect(self.update_colormap)
        self.spinBox_roix.valueChanged.connect(self.update_roi)
        self.spinBox_roiy.valueChanged.connect(self.update_roi)
        self.comboBox_channel_num.currentIndexChanged.connect(self.plot_dataset)
        self.comboBox_target.currentIndexChanged.connect(self.plot_dataset)
        self.pushButton_replot.clicked.connect(self.plot_dataset)
        self.pushButton_select_savefname.clicked.connect(self.select_savefname)

    def selection_changed(self, selected, deselected):
        indexes = self.treeView_fs.selectionModel().selectedIndexes()
        if indexes:
            flist = [self.model.filePath(index) for index in indexes]
            self.dset_manager.update_flist(list(set(flist)))
            self.plot_dataset()

    def init_ui(self):
        self.pushButton_select_rawfolder.clicked.connect(self.select_rawfolder)

    def setup_imageview(self):
        # self.img2d_axes = pg.PlotItem()
        # self.pg_hdl_img2d.addItem(self.img2d_axes)
        self.pg_hdl_img2d.getView().setAspectLocked(False)

        # Add crosshair
        self.view = self.pg_hdl_img2d.getView()
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.view.addItem(self.vLine, ignoreBounds=True)
        self.view.addItem(self.hLine, ignoreBounds=True)
        # Initialize plots
        self.h_curve = self.pg_hdl_hline.plot(pen="r")
        self.pg_hdl_hline.setLabel("bottom", "Energy", units="keV")
        self.v_curve = self.pg_hdl_vline.plot(pen="b")
        self.pg_hdl_vline.setLabel("left", "Time", units="μs")
        self.zoomin_image = pg.ImageItem()
        self.pg_hdl_zoomin.addItem(self.zoomin_image)
        self.pg_hdl_zoomin.setAspectLocked(False)
        self.pg_hdl_zoomin.hideAxis("bottom")
        self.pg_hdl_zoomin.hideAxis("left")
        self.proxy = pg.SignalProxy(
            self.view.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved
        )

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
            self.roi.setPos(
                (position[0] - roi_size[0] / 2, position[1] - roi_size[1] / 2)
            )

    def mouseMoved(self, evt):
        pos = evt[0]
        if self.image is None:
            return
        if self.view.sceneBoundingRect().contains(pos):
            mouse_point = self.view.mapSceneToView(pos)
            x = int(mouse_point.x())
            y = int(mouse_point.y())

            # Update crosshair position
            self.vLine.setPos(x)
            self.hLine.setPos(y)

            # Update line cuts if within image bounds
            if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
                # Get horizontal and vertical cuts
                horizontal_data = self.image[y, :]
                vertical_data = self.image[:, x]
                # Create y-axis values for vertical cut
                x_positions = self.dset_manager.energy_axis
                y_positions = (
                    np.arange(len(vertical_data)) * self.dset_manager.delta_t_ns / 1000
                )  # us
                # Update horizontal cut
                self.h_curve.setData(x_positions, horizontal_data)
                self.v_curve.setData(vertical_data, y_positions[::-1])
                self.update_roi(None, position=(x, y))
                energy = self.dset_manager.energy_axis[x]
                t_time = (len(vertical_data) - y) * self.dset_manager.delta_t_ns / 1000
                self.pg_hdl_zoomin.setTitle(
                    f"Energy: {energy:.4f} keV, Time: {t_time:.3f} μs"
                )
            self.update_zoomed_view()

    def update_zoomed_view(self):
        if self.roi is None:
            return
        image_data = self.image
        roi_data = self.roi.getArrayRegion(image_data, self.pg_hdl_img2d.getImageItem())
        if roi_data.size > 0:
            self.zoomin_image.setImage(np.flipud(roi_data))

    def update_colormap(self):
        cmap = self.comboBox_cmap.currentText()
        cmap = pg.colormap.getFromMatplotlib(cmap)
        self.pg_hdl_img2d.setColorMap(cmap)
        self.zoomin_image.setColorMap(cmap)

    def plot_dataset(self):
        kwargs = {
            "channel": int(self.comboBox_channel_num.currentText()),
            "target": self.comboBox_target.currentText(),
        }
        if kwargs["target"] in ["normalized-GS"]:
            norm_kwargs = {
                "trig_index": self.spinBox_syncbunch_number.value(),
                "do_perbunch": self.comboBox_groundstate_method.currentText(),
                "pre_avg_orbitals": self.spinBox_orbitals_number.value(),
                "aft_avg_bunches": self.spinBox_compress_bunches.value(),
            }
            kwargs["norm_kwargs"] = norm_kwargs
        if kwargs["target"] in ["normalized-GS", "normalized"]:
            self.comboBox_channel_num.setEnabled(False)
        else:
            self.comboBox_channel_num.setEnabled(True)

        data, energy, delta_t_ns = self.dset_manager.get_energy_vs_time(**kwargs)
        if data is not None:
            data = data.T
            if self.image is None or data.shape != self.image.shape:
                # remove roi
                if self.roi is not None:
                    self.pg_hdl_img2d.removeItem(self.roi)
                    self.roi = None
                # adjust  roi size
                self.spinBox_roix.setValue(data.shape[1] // 10)
                self.spinBox_roiy.setValue(data.shape[0] // 10)

            if kwargs["target"] in ["normalized-GS"]:
                vmin, vmax = np.percentile(data.ravel(), [0.1, 99.9])
            else:
                vmin, vmax = np.percentile(data.ravel(), [0, 100])
            self.image = np.flipud(data)
            self.pg_hdl_img2d.setImage(self.image, levels=(vmin, vmax))

    def select_rawfolder(self, folder_path=None):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder_path:
            self.lineEdit_rawfolder.setText(folder_path)
            flist = os.listdir(folder_path)
            indexes = [int(f[-5:]) for f in flist]
            self.spinBox_fileindex_min.setValue(min(indexes))
            self.spinBox_fileindex_max.setValue(max(indexes))
            self.model.setRootPath(folder_path)
            self.treeView_fs.setRootIndex(self.model.index(folder_path))

    def select_savefname(self):
        """
        Opens a QFileDialog to allow the user to select a save location for an NPZ file.
        Returns the selected file path with a '.npz' extension.
        """
        file_filter = "NumPy Compressed File (*.npz)"

        # Open the file dialog
        filename, _ = QFileDialog.getSaveFileName(
            None,  # Parent widget (None for standalone)
            "Save File",  # Dialog title
            "",  # Default directory
            file_filter,  # Filter to only show .npz files
        )

        if filename and not filename.endswith(".npz"):
            filename += ".npz"
        if filename:
            self.dset_manager.save_results(filename)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
