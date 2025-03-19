import os
import sys
import time
import numpy as np
import pyqtgraph as pg
from pathlib import Path
from multiprocessing import Process
from .generated_ui import Ui_MainWindow
from PySide6.QtCore import (QDir, QSortFilterProxyModel,
                            Signal, Slot, QObject, QThread)

from PySide6.QtWidgets import (QApplication, QFileDialog, QFileSystemModel,
                               QMainWindow)

from .trxas_dataset import TrXASDatasetManager, create_trxas_cache_from_flist, build_cache_database
from .utilities import get_scan_type
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")
pg.setConfigOptions(antialias=True)
pg.setConfigOptions(imageAxisOrder="row-major")


class DatasetFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache_db = {"scan_type": {}}
    
    def update_cache_db(self, cache_db):
        self.cache_db = cache_db

    def filterAcceptsRow(self, source_row, source_parent):
        """Override this method to filter out non-dataset files."""
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        
        if not index.isValid():
            return False
        full_path = model.filePath(index)
        scan_type = self.cache_db["scan_type"].get(full_path, None)
        if scan_type is None:
            scan_type = get_scan_type(full_path)
            if scan_type in ['exafs', 'laserd']:
                self.cache_db["scan_type"][full_path] = scan_type
        # show the directory and parent directory
        return scan_type != "invalid"


class AverageWorker(QObject):
    finished = Signal()
    progress = Signal(int)
    start_task = Signal()
    stop_worker = Signal()

    def __init__(self):
        super().__init__()
        self.dset_manager = TrXASDatasetManager()
        self.flist = None
        self.kwargs = None
        self.results = None
        self.start_task.connect(self.run)

    def set_kwargs(self, flist, **kwargs):
        self.flist = flist
        self.kwargs = kwargs

    @Slot()
    def run(self):
        t0 = time.perf_counter()
        self.dset_manager.update_flist(self.flist)
        self.results = self.dset_manager.get_energy_vs_time(
            progress=self.progress, **self.kwargs)
        self.finished.emit()
        t1 = time.perf_counter()
        logger.info(f'AverageWorker.run finished in {t1 - t0:.3f} seconds on {len(self.flist)} files')
    
    def get_results(self):
        # data, energy, delta_t_ns
        return self.results
    
    def quit(self):
        self.stop_worker.emit()


class CacheWorker(QThread):
    """Manages multiple processes for cache generation"""
    # progress = Signal(int)
    finished = Signal()

    def __init__(self, file_list, number_of_processes=4):
        super().__init__()
        self.file_list = file_list
        self.processes = []
        self.number_of_processes = number_of_processes

    def run(self):
        t0 = time.perf_counter()
        k, m = divmod(len(self.file_list), self.number_of_processes)
        flist_parts = [self.file_list[i * k + min(i, m): (i + 1) * k + min(i + 1, m)]
                       for i in range(self.number_of_processes)]
        logger.info(f"Starting CacheWorker with {self.number_of_processes} processes to prepare {len(self.file_list)} datasets.")

        for part in flist_parts:
            process = Process(target=create_trxas_cache_from_flist, args=(part,))
            process.start()
            self.processes.append(process)

        for process in self.processes:
            process.join()  # Wait for each process to finish (in background thread)

        self.finished.emit()
        t1 = time.perf_counter()
        logger.info(f"CacheWorker.run finished in {t1 - t0:.3f} seconds")


class TrXASViewer(QMainWindow, Ui_MainWindow):
    def __init__(self, rawfolder=None):
        super(TrXASViewer, self).__init__()
        self.setupUi(self)
        self.init_ui()
        self.image = None
        self.energy_axis = None
        self.t_axis = None
        self.last_position = None
        self.roi = None
        self.cache_db = {}

        self.setup_imageview()
        self.update_colormap()
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        # Create filter proxy model
        self.proxy_model = DatasetFilterModel()
        self.proxy_model.setSourceModel(self.model)
        # self.model.setNameFilterDisables(False) #enable the filters.
        self.treeView_fs.setModel(self.proxy_model)
        self.treeView_fs.setColumnWidth(0, 200)

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
        self.comboBox_fileindex_prefix.currentIndexChanged.connect(self.update_fileindex)

        if rawfolder:
            self.select_rawfolder(folder_path=rawfolder)

        self.is_processing = False
        self.thread = QThread()
        self.avg_worker = AverageWorker()
        self.avg_worker.progress.connect(self.update_progress_bar)
        self.avg_worker.finished.connect(self.plot_results)
        self.progressBar.setValue(0)
        self.avg_worker.moveToThread(self.thread)
        self.thread.started.connect(lambda: logger.info("Starting AverageWorker..."))
        self.thread.start()
        
    def process(self):
        if self.is_processing:
            return
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
            if proxy_index.column() != 0:  # Ensure we only process the first column
                continue
            source_index = self.proxy_model.mapToSource(proxy_index)
            if source_index.isValid():
                file_paths.append(self.model.filePath(source_index))
        if file_paths:
            self.process_flist(file_paths)
    
    def process_range(self):
        if not self.radioButton_selection_by_index.isChecked():
            return
        logger.debug("process_range")

        idx_min = self.spinBox_fileindex_min.value()
        idx_max = self.spinBox_fileindex_max.value()
        raw_folder = self.lineEdit_rawfolder.text()

        prefix = self.comboBox_fileindex_prefix.currentText()
        file_indexes = self.cache_db["prefix_db"]

        file_paths = []
        for idx in range(idx_min, idx_max + 1):
            if idx in file_indexes:
                full_path = Path(raw_folder) / f"{prefix}{idx:05d}"
                file_paths.append(full_path)
        if file_paths:
            self.process_flist(file_paths)

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

    def mouse_clicked(self, event=None):
        if self.image is None:
            return

        if event is None:
            if self.last_position is None:
                return
            else:
                pos = self.last_position
        else:
            pos = event[0].scenePos()
            self.last_position = pos

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
                x_positions = self.energy_axis[0:horizontal_data.size]
                y_positions = self.t_axis[0:vertical_data.size] / 1000
                y_positions = y_positions[::-1]

                # Update horizontal cut
                self.h_curve.setData(x_positions, horizontal_data)
                self.v_curve.setData(vertical_data, y_positions)
                self.update_roi(None, position=(x, y))

                pos_energy = self.energy_axis[x]
                pos_time = y_positions[y] 
                self.pg_hdl_zoomin.setTitle(
                    f"Energy: {pos_energy:.4f} keV, Time: {pos_time:.3f} μs"
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

    def process_flist(self, flist=None):
        if not flist: return

        kwargs = {
            "channel": int(self.comboBox_channel_num.currentText()),
            "target": self.comboBox_target.currentText(),
        }
        if kwargs["target"] == "raw":    # fix me; disable raw plotting
            return

        if kwargs["target"] in ["normalized-GS"]:
            norm_kwargs = self.get_normalization_subgs_kwargs()
            kwargs["norm_kwargs"] = norm_kwargs
        if kwargs["target"] in ["normalized-GS", "normalized"]:
            self.comboBox_channel_num.setEnabled(False)
        else:
            self.comboBox_channel_num.setEnabled(True)
        
        self.progressBar.setValue(0)
        self.avg_worker.set_kwargs(flist, **kwargs)
        self.is_processing = True
        self.pushButton_replot.setText('Processing...')
        self.pushButton_replot.setDisabled(True)
        self.avg_worker.start_task.emit()
    
    def get_normalization_subgs_kwargs(self):
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
        return norm_kwargs

    def plot_results(self):
        data, energy_axis, t_axis = self.avg_worker.get_results()
        self.energy_axis = energy_axis
        self.t_axis = t_axis

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

            if self.comboBox_target.currentText() == 'normalized-GS':
                vmin, vmax = np.percentile(data.ravel(), [0.1, 99.9])
            else:
                vmin, vmax = np.percentile(data.ravel(), [0, 100])
            self.image = np.flipud(data)
            self.pg_hdl_img2d.setImage(self.image, levels=(vmin, vmax))
            self.mouse_clicked()
        
        self.is_processing = False
        self.pushButton_replot.setText('Process')
        self.pushButton_replot.setEnabled(True)
    
    def update_progress_bar(self, value):
        """Updates the progress bar."""
        self.progressBar.setValue(value)

    def select_rawfolder(self, placeholder=None, folder_path=None):
        if not folder_path or not Path(folder_path).is_dir():
            folder_path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder_path:
            self.lineEdit_rawfolder.setText(folder_path)
            self.cache_db = build_cache_database(folder_path)
            self.proxy_model.update_cache_db(self.cache_db)
            prefix_db = self.cache_db["prefix_db"]

            self.comboBox_fileindex_prefix.clear()
            self.comboBox_fileindex_prefix.addItems(list(prefix_db.keys()))
            self.comboBox_fileindex_prefix.setCurrentIndex(0)

            fs_root_index = self.model.index(folder_path)
            proxy_root_index = self.proxy_model.mapFromSource(fs_root_index)
            self.treeView_fs.setRootIndex(proxy_root_index)
            self.build_cache()

    def update_fileindex(self):
        current_prefix = self.comboBox_fileindex_prefix.currentText()
        file_indexes = self.cache_db["prefix_db"][current_prefix]["exafs"]
        self.spinBox_fileindex_min.setValue(min(file_indexes))
        self.spinBox_fileindex_max.setValue(max(file_indexes))
    
    def build_cache(self, num_workers=None):
        if num_workers is None:
            num_workers = max(2, os.cpu_count() // 2)

        file_paths = [k for k, v in self.cache_db["scan_type"].items() 
                      if v in ("exafs", "laserd")]

        if len(file_paths) > 0:
            num_workers = min(num_workers, len(file_paths))
            self.cache_worker = CacheWorker(file_paths, num_workers)
            self.cache_worker.start()

    def select_savefname(self):
        """
        Opens a QFileDialog to allow the user to select a save location for an NPZ file.
        Returns the selected file path with a '.npz' extension.
        """
        if self.is_processing:
            return

        file_filter = "NumPy Compressed File (*.npz)"

        # Open the file dialog
        filename, _ = QFileDialog.getSaveFileName(
            None,  # Parent widget (None for standalone)
            "Save File",  # Dialog title
            "",  # Default directory
            file_filter,  # Filter to only show .npz files
        )

        norm_kwargs = self.get_normalization_subgs_kwargs()
        # norm_kwargs['aft_avg_bunches'] = 1
        kwargs = {
            "target": "normalized-GS",
            "norm_kwargs": norm_kwargs
        }

        if filename and not filename.endswith(".npz"):
            filename += ".npz"
        if filename:
            self.avg_worker.dset_manager.save_results(filename, **kwargs)
        
    def closeEvent(self, event):
        if self.is_processing:
            return
        self.avg_worker.quit()
        self.avg_worker.stop_worker.emit()  # Tell the worker to stop
        self.thread.quit()  # Quit the thread event loop
        self.thread.wait()  # Wait for thread to finish
        event.accept()  # Allow closing


def main_gui(rawfolder=None):
    app = QApplication(sys.argv)
    window = TrXASViewer(rawfolder=rawfolder)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_gui()