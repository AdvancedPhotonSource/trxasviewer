import os
import sys

import numpy as np
import pyqtgraph as pg
from .generated_ui import Ui_MainWindow
from PySide6.QtCore import (QDir, QSortFilterProxyModel,
                            Signal, Slot, QObject, QThread)

from PySide6.QtWidgets import (QApplication, QFileDialog, QFileSystemModel,
                               QMainWindow)

from .trxas_dataset import TrXASDatasetManager, is_sample_data
from .utilities import get_valid_file_index
import logging


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")
pg.setConfigOptions(antialias=True)
pg.setConfigOptions(imageAxisOrder="row-major")


class DatasetFilterModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        """Override this method to filter out non-dataset files."""
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        
        if not index.isValid():
            return False
        
        file_path = model.filePath(index)

        # Allow directories
        if os.path.isdir(file_path):
            return True 

        # Filter files using is_sample_data function
        return is_sample_data(file_path)


class TrXASViewer(QMainWindow, Ui_MainWindow):
    def __init__(self, rawfolder=None):
        super(TrXASViewer, self).__init__()
        self.setupUi(self)
        self.init_ui()
        self.image = None
        self.roi = None
        self.dset_manager = TrXASDatasetManager()
        self.prefix, self.file_indexes = None, None

        self.setup_imageview()
        self.update_colormap()
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        # Create filter proxy model
        self.proxy_model = DatasetFilterModel()
        self.proxy_model.setSourceModel(self.model)
        # self.model.setNameFilterDisables(False) #enable the filters.
        self.treeView_fs.setModel(self.proxy_model)

        # self.treeView_fs.setRootIndex(self.model.index(QDir.homePath()))
        self.treeView_fs.hideColumn(2)  # hide type
        # self.treeView_fs.hideColumn(3)  # hide Date
        self.treeView_fs.selectionModel().selectionChanged.connect(
            self.process_selection
        )
        self.comboBox_cmap.currentIndexChanged.connect(self.update_colormap)
        self.spinBox_roix.valueChanged.connect(self.update_roi)
        self.spinBox_roiy.valueChanged.connect(self.update_roi)
        self.comboBox_channel_num.currentIndexChanged.connect(self.process)
        self.comboBox_target.currentIndexChanged.connect(self.process)
        self.pushButton_replot.clicked.connect(self.process)
        self.pushButton_select_savefname.clicked.connect(self.select_savefname)

        if rawfolder:
            self.select_rawfolder(folder_path=rawfolder)
        
    def process(self):
        if self.radioButton_selection_by_mouse.isChecked():
            self.process_selection(None, None)
        elif self.radioButton_selection_by_index.isChecked():
            self.process_range()
        else:
            logger.debug("No selection method selected")

    def process_selection(self, selected, deselected):
        if not self.radioButton_selection_by_mouse.isChecked():
            return
        logger.debug("process_selection")
        indexes = self.treeView_fs.selectionModel().selectedIndexes()
        file_paths = []
        for proxy_index in indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            if source_index.isValid():
                file_paths.append(self.model.filePath(source_index))
        if file_paths:
            self.plot_dataset(file_paths)
    
    def process_range(self):
        if not self.radioButton_selection_by_index.isChecked():
            return
        logger.debug("process_range")
        idx_min = self.spinBox_fileindex_min.value()
        idx_max = self.spinBox_fileindex_max.value()
        file_paths = []
        for idx in range(idx_min, idx_max + 1):
            if idx in self.file_indexes:
                file_paths.append(f"{self.prefix}{idx:05d}")
        if file_paths:
            self.plot_dataset(file_paths)

    def init_ui(self):
        self.pushButton_select_rawfolder.clicked.connect(self.select_rawfolder)

    def setup_imageview(self):
        # self.img2d_axes = pg.PlotItem()
        # self.pg_hdl_img2d.addItem(self.img2d_axes)
        self.pg_hdl_img2d.getView().setAspectLocked(False)

        # Add crosshair
        self.view = self.pg_hdl_img2d.getView()
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("r"))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("b"))
        self.view.addItem(self.vLine, ignoreBounds=True)
        self.view.addItem(self.hLine, ignoreBounds=True)
        # Initialize plots
        self.h_curve = self.pg_hdl_hline.plot(pen="b")
        self.pg_hdl_hline.setLabel("bottom", "Energy", units="keV")
        self.v_curve = self.pg_hdl_vline.plot(pen="r")
        self.pg_hdl_vline.setLabel("left", "Time", units="μs")
        self.zoomin_image = pg.ImageItem()
        self.pg_hdl_zoomin.addItem(self.zoomin_image)
        self.pg_hdl_zoomin.setAspectLocked(False)
        self.pg_hdl_zoomin.hideAxis("bottom")
        self.pg_hdl_zoomin.hideAxis("left")
        self.proxy = pg.SignalProxy(
            self.view.scene().sigMouseClicked, rateLimit=60, slot=self.mouse_clicked
        )

    def update_roi(self, value, position=None):
        # value is a positional placeholder for the signal. It is not used.
        roi_size = (self.spinBox_roix.value(), self.spinBox_roiy.value())
        if self.roi is None:
            self.roi = pg.RectROI([0, 0], roi_size, pen="k", hoverPen="k", sideScalers=False)
            self.roi.mouseClickEvent = lambda ev: ev.ignore()
            self.pg_hdl_img2d.addItem(self.roi)

        # update size
        if self.roi.size() != roi_size:
            self.roi.setSize(roi_size)

        if position is not None and self.roi.pos() != position:
            self.roi.setPos(
                (position[0] - roi_size[0] / 2, position[1] - roi_size[1] / 2)
            )

    def mouse_clicked(self, event):
        if len(event) == 0 or self.image is None:
            return

        pos = event[0].scenePos()
        if self.view.sceneBoundingRect().contains(pos):
            mouse_point = self.view.mapSceneToView(pos)
            # Update crosshair position
            self.vLine.setPos(mouse_point.x())
            self.hLine.setPos(mouse_point.y()) 
            x = int(mouse_point.x())
            y = int(mouse_point.y())
            # Update line cuts if within image bounds
            if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
                # Get horizontal and vertical cuts
                horizontal_data = self.image[y, :]
                vertical_data = self.image[:, x]
                # Create y-axis values for vertical cut
                x_positions = self.dset_manager.energy_axis[0:horizontal_data.size]
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

    def plot_dataset(self, flist=None):
        if flist and len(flist) > 0:
            self.dset_manager.update_flist(list(set(flist)))

        kwargs = {
            "channel": int(self.comboBox_channel_num.currentText()),
            "target": self.comboBox_target.currentText(),
        }
        if kwargs["target"] in ["normalized-GS"]:
            sync_time = self.radioButton_sync_time.isChecked()
            sync_bunch = self.radioButton_sync_bunch.isChecked()
            assert sync_time != sync_bunch, "Please check sync conditions"
            sync_type = "time" if sync_time else "bunch"
            sync_value = (
                self.spinBox_syncbunch_number.value()
                if sync_bunch
                else self.doubleSpinBox_sync_time_us.value()
            )
            norm_kwargs = {
                "sync_type": sync_type,
                "sync_value": sync_value,
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

    def select_rawfolder(self, placeholder=None, folder_path=None):
        if not folder_path or not os.path.isdir(folder_path):
            folder_path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder_path:
            self.lineEdit_rawfolder.setText(folder_path)
            self.prefix, self.file_indexes = get_valid_file_index(folder_path)

            self.spinBox_fileindex_min.setValue(min(self.file_indexes))
            self.spinBox_fileindex_max.setValue(max(self.file_indexes))

            fs_root_index = self.model.index(folder_path)
            proxy_root_index = self.proxy_model.mapFromSource(fs_root_index)
            self.treeView_fs.setRootIndex(proxy_root_index)

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


def main_gui(rawfolder=None):
    app = QApplication(sys.argv)
    window = TrXASViewer(rawfolder=rawfolder)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_gui()