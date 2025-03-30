import os
import sys
import argparse
import time
import numpy as np
import json
import pyqtgraph as pg
from pathlib import Path
import traceback
from multiprocessing import Process
from .generated_ui import Ui_MainWindow
from PySide6.QtCore import (
    QDir,
    QSortFilterProxyModel,
    Qt,
    Signal,
    Slot,
    QObject,
    QThread,
    QTimer,
)

from PySide6.QtWidgets import QApplication, QFileDialog, QFileSystemModel, QMainWindow
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QCheckBox,
)

from .trxas_dataset import (
    TrXASDatasetManager,
    create_trxas_cache_from_flist,
    build_cache_database,
)
from .utilities import get_scan_type
import logging
from . import __version__

CONFIG_FILE = Path.home() / ".trxasviewer" / "config.json"
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")
pg.setConfigOptions(antialias=True)
pg.setConfigOptions(imageAxisOrder="row-major")


def get_human_readable_size(full_path):
    size = os.path.getsize(full_path)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"  # fallback for extremely large files


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
        # scan_type = self.cache_db["scan_type"].get(full_path, None)
        # if scan_type in (None, "writing"):
        scan_type = get_scan_type(full_path)
        # if scan_type in ["exafs", "laserd"]:
        #     self.cache_db["scan_type"][full_path] = scan_type
        # show the directory and parent directory
        return scan_type != "invalid"

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        # Check if the requested column is the "Type" column (column 2 in QFileSystemModel)
        if index.column() == 2 and role == Qt.DisplayRole:
            source_index = self.mapToSource(index)
            full_path = self.sourceModel().filePath(source_index)  # Get full path
            scan_type = self.cache_db["scan_type"].get(full_path, None)
            return scan_type

        if role == Qt.DisplayRole and index.column() == 1:  # Size column
            source_index = self.mapToSource(index)
            full_path = self.sourceModel().filePath(source_index)
            try:
                return get_human_readable_size(full_path)
            except OSError:
                return 0
        return super().data(index, role)  # Default behavior


class AverageWorker(QObject):
    finished = Signal()
    progress = Signal(int)
    start_task = Signal()
    stop_worker = Signal()
    error = Signal(str)

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
        try:
            self.results = self.dset_manager.get_energy_vs_time(
                progress=self.progress, **self.kwargs
            )
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error in AverageWorker.run: {e}")
            self.results = None
            self.error.emit(str(e))
        self.finished.emit()
        t1 = time.perf_counter()
        logger.info(
            f"AverageWorker.run finished in {t1 - t0:.3f} seconds on {len(self.flist)} files"
        )

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
        self.is_done = False

    def run(self):
        t0 = time.perf_counter()
        k, m = divmod(len(self.file_list), self.number_of_processes)
        flist_parts = [
            self.file_list[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)]
            for i in range(self.number_of_processes)
        ]
        logger.info(
            f"Starting CacheWorker with {self.number_of_processes} processes to prepare {len(self.file_list)} datasets."
        )

        for part in flist_parts:
            process = Process(target=create_trxas_cache_from_flist, args=(part,))
            process.start()
            self.processes.append(process)

        for process in self.processes:
            process.join()  # Wait for each process to finish (in background thread)

        self.finished.emit()
        self.is_done = True
        t1 = time.perf_counter()
        logger.info(f"CacheWorker.run finished in {t1 - t0:.3f} seconds")


class TrXASViewer(QMainWindow, Ui_MainWindow):
    def __init__(self, rawfolder=None, syncbunch=None, autoload=False):
        super(TrXASViewer, self).__init__()
        self.setupUi(self)
        self.image = None
        self.results = None
        self.last_position = None
        self.roi = None
        self.cache_db = {}
        self.kinetics_roi = {}
        self.setWindowTitle(f"TrXASViewer v{__version__}")

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
        self.treeView_fs.setSortingEnabled(True)

        self.pushButton_select_rawfolder.clicked.connect(self.select_rawfolder)
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
        self.comboBox_fileindex_prefix.currentIndexChanged.connect(
            self.update_fileindex
        )
        self.toolButton_refresh.clicked.connect(self.reload_rawfolder)
        self.spinBox_syncbunch_number.valueChanged.connect(
            self.update_sync_timing_parameters
        )
        self.doubleSpinBox_sync_time_us.valueChanged.connect(
            self.update_sync_timing_parameters
        )
        self.radioButton_sync_time.toggled.connect(self.update_sync_timing_parameters)

        for n in range(5):

            def callback(index=n):
                self.update_binning_params(index=index)

            self.__dict__[f"spinBox_anchor{n}"].editingFinished.connect(callback)
            self.__dict__[f"spinBox_numb{n}"].editingFinished.connect(callback)

        self.setup_tooltips()

        self.auto_save_load = autoload
        if autoload:
            self.save_load_settings(mode="load")
        if rawfolder:
            self.select_rawfolder(folder_path=rawfolder)
        if syncbunch:
            self.spinBox_syncbunch_number.setValue(syncbunch)
        self.update_kinetics_signal()

        self.is_processing = False
        self.thread = QThread()
        self.avg_worker = AverageWorker()
        self.avg_worker.progress.connect(self.update_progress_bar)
        self.avg_worker.finished.connect(self.plot_results)
        self.avg_worker.error.connect(self.show_status)
        self.progressBar.setValue(0)
        self.avg_worker.moveToThread(self.thread)
        self.thread.started.connect(lambda: logger.info("Starting AverageWorker..."))
        self.thread.start()

        # Create a QTimer
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 1000 ms = 1 second
        self.timer.timeout.connect(self.refresh_filesystem)
        self.timer.start()

    def save_load_settings(self, mode="save"):
        keys = [
            "lineEdit_rawfolder",
            "radioButton_sync_time",
            "doubleSpinBox_sync_time_us",
            "radioButton_sync_bunch",
            "spinBox_syncbunch_number",
            "comboBox_groundstate_method",
            "spinBox_orbitals_number",
            "spinBox_binning_linnum",
            "spinBox_binning_lognum",
            "radioButton_selection_by_mouse",
            "radioButton_selection_by_index",
        ]
        keys += [f"spinBox_anchor{n}" for n in range(5)]
        keys += [f"spinBox_numb{n}" for n in range(5)]
        keys += [f"doubleSpinBox_kinetics_ecenter{n}" for n in range(1, 5)]
        keys += [f"doubleSpinBox_kinetics_edelta{n}" for n in range(1, 5)]
        keys += [f"checkBox_kinetics_roi{n}" for n in range(1, 5)]
        if mode == "save":
            config = {}
            for key in keys:
                widget = getattr(self, key)
                if isinstance(widget, QLineEdit):
                    config[key] = widget.text()
                elif isinstance(widget, QRadioButton):
                    config[key] = widget.isChecked()
                elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                    config[key] = widget.value()
                elif isinstance(widget, QComboBox):
                    config[key] = widget.currentIndex()
                elif isinstance(widget, QCheckBox):
                    config[key] = widget.isChecked()
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saving to configuration file [{CONFIG_FILE}]")

        elif mode == "load":
            if CONFIG_FILE.is_file():
                logger.info(f"Loading configuration file [{CONFIG_FILE}]")
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                for key, value in config.items():
                    widget = self.__dict__.get(key)
                    if isinstance(widget, QLineEdit):
                        widget.setText(value)
                    elif isinstance(widget, QRadioButton):
                        widget.setChecked(value)
                    elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                        widget.setValue(value)
                    elif isinstance(widget, QComboBox):
                        widget.setCurrentIndex(value)
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(value)
            else:
                logger.error(f"Configuration file [{CONFIG_FILE}] not found.")

    def setup_tooltips(self):
        self.label_binbunches.setToolTip(
            """ Number of bunches to bin:
            -1: disable this level and beyond.
            0: do not bin/average the lasered/delayed branches.
            1: bin all lasered/delayed branches into one bunch.
            N>=2: bin all lasered delayed branches as one bunch and then 
            bin N bunches into one.
            """
        )
        self.label_anchorbunch.setToolTip(
            """ Index of bunch to anchor:
            Laser trigggered at bunch of 0. The binning happens between the
            anchor of the previous level [inclusive] (0 if it's the first level)
            and the anchor of the current level [exclusive], using the number
            of "Bin Bunches" defined below.
            """
        )

    def reload_rawfolder(self):
        raw_folder = self.lineEdit_rawfolder.text()
        if raw_folder and self.cache_worker and self.cache_worker.is_done:
            self.select_rawfolder(placeholder=None, folder_path=raw_folder)
            self.show_status(f"Reloaded raw folder: {raw_folder}")

    def refresh_filesystem(self):
        self.proxy_model.invalidate()
        self.proxy_model.layoutChanged.emit()
        # self.model.layoutChanged.emit()
        # self.model.setRootPath(self.model.rootPath())  # Refresh the model

    def show_status(self, msg, level=logging.INFO, timeout=5000):
        logger.log(level, msg)
        self.statusBar().showMessage(msg, timeout)

    def update_kinetics_signal(self):
        for n in range(1, 5):
            signal_func = lambda: self.update_kinetics_ROI(target=n, mode="value-roi")
            widget = getattr(self, f"doubleSpinBox_kinetics_ecenter{n}")
            widget.editingFinished.connect(signal_func)
            widget = getattr(self, f"doubleSpinBox_kinetics_edelta{n}")
            widget.editingFinished.connect(signal_func)
            widget = getattr(self, f"checkBox_kinetics_roi{n}")
            widget.stateChanged.connect(signal_func)

    def update_binning_params(self, index=0, prev_enable=True):
        if index >= 5:
            return

        length = self.__dict__[f"spinBox_numb{index}"].value()
        anchor = self.__dict__[f"spinBox_anchor{index}"].value()
        label_widget = self.__dict__[f"label_rtime{index}"]

        if index == 0:
            prev_anchor = 0
        else:
            prev_anchor = self.__dict__[f"spinBox_anchor{index-1}"].value()
        if length == -1 or not prev_enable:
            self.__dict__[f"spinBox_anchor{index}"].setEnabled(False)
            self.update_binning_params(index=index + 1, prev_enable=False)
            label_widget.setText("∞")
            return
        else:
            self.__dict__[f"spinBox_anchor{index}"].setEnabled(True)
            total_size = max(1, anchor - prev_anchor)
            if length == 0:
                length = 1  # length = 0 means do not bin lasered
            fit_size = (total_size + length - 1) // length * length
            fit_anchor = prev_anchor + fit_size
            if fit_anchor != anchor:
                self.__dict__[f"spinBox_anchor{index}"].setValue(fit_anchor)
            if self.results is not None:
                rtime = self.results["delta_t_s"] * fit_anchor * 1e6  # us
                label_widget.setText(f"{rtime:.3f}")
            self.update_binning_params(index=index + 1, prev_enable=True)

    def process(self):
        if self.is_processing:
            return
        if self.radioButton_selection_by_mouse.isChecked():
            self.process_selection(None, None)
        elif self.radioButton_selection_by_index.isChecked():
            self.process_range()
        else:
            self.show_message("No selection method selected", logging.ERROR)

    def process_selection(self, selected, deselected):
        if not self.radioButton_selection_by_mouse.isChecked():
            return
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
        idx_min = self.spinBox_fileindex_min.value()
        idx_max = self.spinBox_fileindex_max.value()
        raw_folder = self.lineEdit_rawfolder.text()

        selection = self.comboBox_fileindex_prefix.currentText()
        current_prefix, scan_type = selection.split("@")
        file_indexes = self.cache_db["prefix_db"][current_prefix][scan_type]

        file_paths = []
        for idx in range(idx_min, idx_max + 1):
            if idx in file_indexes:
                full_path = Path(raw_folder) / f"{current_prefix}{idx:05d}"
                file_paths.append(full_path)
        if file_paths:
            self.process_flist(file_paths)

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
        self.pg_hdl_hline.setLabel(
            "left",
            "Intensity (a.u.)",
        )
        self.v_curve = self.pg_hdl_vline.plot(pen="r")
        self.pg_hdl_vline.setLabel("left", "Time", units="s")
        self.pg_hdl_vline.setLabel("bottom", "Intensity (a.u.)")
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
            self.roi = pg.RectROI(
                [0, 0], roi_size, pen="k", hoverPen="k", sideScalers=False
            )
            self.roi.mouseClickEvent = lambda ev: ev.ignore()
            self.pg_hdl_img2d.addItem(self.roi)

        # update size
        if self.roi.size() != roi_size:
            self.roi.setSize(roi_size)

        if position is not None and self.roi.pos() != position:
            self.roi.setPos(
                (position[0] - roi_size[0] / 2, position[1] - roi_size[1] / 2)
            )

    def compute_ROI_geometry(self, center, delta):
        energy = self.results["x_axis"]["value"]
        idx = np.argmin(np.abs(energy - center))
        v_size = self.image.shape[1]
        e0, e1 = center - delta, center + delta
        h_size = np.argmin(np.abs(energy - e1)) - np.argmin(np.abs(energy - e0))
        pos = (idx - h_size // 2, 0)
        size = (h_size, v_size)
        return pos, size

    def compute_energy_bounds(self, pos, size):
        energy = self.results["x_axis"]["value"]
        e0 = energy[int(pos[0])]
        e1 = energy[int(pos[0] + size[0])]
        center_energy = (e0 + e1) / 2.0
        delta_energy = (e1 - e0) / 2.0
        return center_energy, delta_energy

    def update_kinetics_ROI(self, mode="roi-value", target=None):
        if self.results is None or target is None:
            return
        assert target in (1, 2, 3, 4)  # for kinetics ROI 1, 2, 3, 4
        if mode == "value-roi":
            kwargs = self.get_kinetics_kwargs()[target - 1]  # target is 1-based
            pos, size = self.compute_ROI_geometry(
                kwargs["center_energy"], kwargs["delta_energy"]
            )
            if target not in self.kinetics_roi:
                roi = pg.RectROI(pos, size, pen="k", hoverPen="k", sideScalers=False)
                self.kinetics_roi[target] = roi
                self.pg_hdl_img2d.addItem(roi)
                print(pos, size)
            else:
                self.kinetics_roi[target].setPos(pos)
                self.kinetics_roi[target].setSize(size)
            if not kwargs["enabled"]:
                pass
                # self.kinetics_roi[target].hide()
        elif mode == "roi-value":
            roi = self.kinetics_roi[target]
            center_energy, delta_energy = self.compute_energy(roi.pos(), roi.size())
            getattr(self, f"doubleSpinBox_kinetics_ecenter{target}").setValue(
                center_energy
            ),
            getattr(self, f"doubleSpinBox_kinetics_edelta{target}").setValue(
                delta_energy
            ),

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
                x_positions = self.results["x_axis"]["value"][0 : horizontal_data.size]
                y_positions = self.results["t_axis"][0 : vertical_data.size]
                y_positions = y_positions[::-1]

                # Update horizontal cut
                self.h_curve.setData(x_positions, horizontal_data)
                self.v_curve.setData(vertical_data, y_positions)
                self.update_roi(None, position=(x, y))

                pos_value = self.results["x_axis"]["value"][x]
                pos_time = y_positions[y]
                unit = self.results["x_axis"]["unit"]
                label = self.results["x_axis"]["label"]
                if label == "Energy":
                    self.pg_hdl_zoomin.setTitle(
                        f"Energy: {pos_value:.4f} {unit}, Time: {pos_time:.3e} s"
                    )
                    self.pg_hdl_hline.setLabel("bottom", "Energy", units="keV")
                elif label == "Delay":
                    self.pg_hdl_zoomin.setTitle(
                        f"Delay: {pos_value:.3e} {unit}, Time: {pos_time:.3e} s"
                    )
                    self.pg_hdl_hline.setLabel("bottom", "Delay", units=unit)
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
        if not flist:
            return

        kwargs = {
            "channel": int(self.comboBox_channel_num.currentText()),
            "target": self.comboBox_target.currentText(),
        }
        # if kwargs["target"] == "raw":  # fix me; disable raw plotting
        #     return

        if kwargs["target"] in ["normalized-GS"]:
            kwargs["norm_kwargs"] = self.get_normalization_subgs_kwargs()
            kwargs["binning_kwargs"] = self.get_binning_kwargs()
            kwargs["kinetics_kwargs"] = self.get_kinetics_kwargs()
        if kwargs["target"] in ["normalized-GS", "normalized"]:
            self.comboBox_channel_num.setEnabled(False)
        else:
            self.comboBox_channel_num.setEnabled(True)

        self.progressBar.setValue(0)
        self.avg_worker.set_kwargs(flist, **kwargs)
        self.is_processing = True
        self.pushButton_replot.setText("Processing...")
        self.pushButton_replot.setDisabled(True)
        self.avg_worker.start_task.emit()

    def update_sync_timing_parameters(self):
        if self.results is None:
            return
        bunch_mode = self.results["bunch_mode"]
        dt_ns = self.results["delta_t_s"] * 1e9
        self.groupBox_timing.setTitle(
            f"Sync Timing: [{bunch_mode}-bunch]:[{dt_ns:.3f} ns]"
        )
        kwargs = self.get_normalization_subgs_kwargs()
        stype, sval = kwargs["sync_type"], kwargs["sync_value"]
        if stype == "time":
            sync_bunch = int(sval / self.results["delta_t_s"])
            self.spinBox_syncbunch_number.setValue(sync_bunch)
        elif stype == "bunch":
            sync_time = sval * self.results["delta_t_s"] * 1e6  # s to us
            self.doubleSpinBox_sync_time_us.setValue(sync_time)

    def get_normalization_subgs_kwargs(self):
        sync_time = self.radioButton_sync_time.isChecked()
        sync_bunch = self.radioButton_sync_bunch.isChecked()
        assert sync_time != sync_bunch, "Please check sync conditions"
        sync_type = "time" if sync_time else "bunch"
        sync_value = (
            self.spinBox_syncbunch_number.value()
            if sync_bunch
            else self.doubleSpinBox_sync_time_us.value() * 1e-6  # us to s
        )
        norm_kwargs = {
            "sync_type": sync_type,
            "sync_value": sync_value,
            "do_perbunch": self.comboBox_groundstate_method.currentText(),
            "pre_avg_orbitals": self.spinBox_orbitals_number.value(),
        }
        return norm_kwargs

    def get_kinetics_kwargs(self):
        roi_list = []
        for n in range(1, 5):
            kwargs = {
                "center_energy": getattr(
                    self, f"doubleSpinBox_kinetics_ecenter{n}"
                ).value(),
                "delta_energy": getattr(
                    self, f"doubleSpinBox_kinetics_edelta{n}"
                ).value(),
                "enabled": getattr(self, f"checkBox_kinetics_roi{n}").isChecked(),
                "label": f"ROI{n}",
            }
            roi_list.append(kwargs)
        return tuple(roi_list)

    def get_binning_kwargs(self):
        current_tab_index = self.tabWidget_binning.currentIndex()
        method = self.tabWidget_binning.tabText(current_tab_index)
        # those are common for all methods
        binning_kwargs = {
            "lin_num": self.spinBox_binning_linnum.value(),
            "log_num": self.spinBox_binning_lognum.value(),
            "method": method,
        }
        if method == "Manual":
            anchors = [self.__dict__[f"spinBox_anchor{n}"].value() for n in range(5)]
            lengths = [self.__dict__[f"spinBox_numb{n}"].value() for n in range(5)]
            binning_kwargs.update(
                {
                    "anchors": tuple(anchors),
                    "lengths": tuple(lengths),
                }
            )
        return binning_kwargs

    def plot_results(self):
        results = self.avg_worker.get_results()
        if results is not None:
            self.results = results
            self.update_sync_timing_parameters()
            data = self.results["avg"].T
            if self.image is None or data.shape != self.image.shape:
                # remove roi
                if self.roi is not None:
                    self.pg_hdl_img2d.removeItem(self.roi)
                    self.roi = None
                # adjust  roi size
                self.spinBox_roix.setValue(data.shape[1] // 10)
                self.spinBox_roiy.setValue(data.shape[0] // 10)

            if self.comboBox_target.currentText() == "normalized-GS":
                vmin, vmax = np.percentile(data.ravel(), [0.5, 99.5])
            else:
                vmin, vmax = np.percentile(data.ravel(), [0, 100])
            self.image = np.flipud(data)
            self.pg_hdl_img2d.setImage(self.image, levels=(vmin, vmax))
            self.mouse_clicked()
            self.plot_kinetics()

        self.is_processing = False
        self.pushButton_replot.setText("Process")
        self.pushButton_replot.setEnabled(True)

    def plot_kinetics(self, x_range=(-1, 10)):
        """Plots the kinetics data."""
        if self.results["kinetics"] is None:
            self.tabWidget_kinetics.setCurrentIndex(0)
            return

        self.tabWidget_kinetics.setCurrentIndex(1)
        self.pg_hdl_kinetics.clear()
        self.pg_hdl_kinetics.addLegend()

        # colors = [pg.intColor(i, hues=4) for i in range(4)]
        colors = ("r", "g", "b", "m", "k", "m", "y")
        for idx, (key, value) in enumerate(self.results["kinetics"].items()):
            data = value["profile"]
            pen = pg.mkPen(colors[idx % len(colors)], width=2)
            self.pg_hdl_kinetics.plot(data[0], data[1], pen=pen)
            scatter_plot = pg.ScatterPlotItem(
                x=data[0],
                y=data[1],
                size=3,
                pen=pen,
                brush=None,
                name=value["long_label"],
            )
            self.pg_hdl_kinetics.addItem(scatter_plot)
            # dt = self.results["delta_t_s"] * np.array(x_range)
            # dt[0] = max(dt[0], np.min(data[:, 0]))
        # self.pg_hdl_kinetics.setXRange(dt[0], dt[1])
        self.pg_hdl_kinetics.setLabel("left", "Intensity (a.u.)")
        self.pg_hdl_kinetics.setLabel("bottom", "Time", units="s")

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
            combos = [f"{key}@exafs" for key in list(prefix_db.keys())]
            combos += [f"{key}@laserd" for key in list(prefix_db.keys())]
            self.comboBox_fileindex_prefix.addItems(combos)
            self.comboBox_fileindex_prefix.setCurrentIndex(0)

            fs_root_index = self.model.index(folder_path)
            proxy_root_index = self.proxy_model.mapFromSource(fs_root_index)
            self.treeView_fs.setRootIndex(proxy_root_index)
            self.treeView_fs.sortByColumn(0, Qt.AscendingOrder)
            self.build_cache()

    def update_fileindex(self):
        selection = self.comboBox_fileindex_prefix.currentText()
        if selection:
            current_prefix, scan_type = selection.split("@")
            file_indexes = self.cache_db["prefix_db"][current_prefix][scan_type]
            if len(file_indexes) > 0:
                vbeg, vend = min(file_indexes), max(file_indexes)
            else:
                vbeg, vend = 0, 0
            self.spinBox_fileindex_min.setValue(vbeg)
            self.spinBox_fileindex_max.setValue(vend)

    def build_cache(self, num_workers=None):
        if num_workers is None:
            num_workers = max(2, os.cpu_count() // 2)

        file_paths = [
            k for k, v in self.cache_db["scan_type"].items() if v in ("exafs", "laserd")
        ]

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

        kwargs = {
            "target": "normalized-GS",
            "norm_kwargs": self.get_normalization_subgs_kwargs(),
            "binning_kwargs": self.get_binning_kwargs(),
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
        if self.auto_save_load:
            self.save_load_settings(mode="save")
        self.thread.quit()  # Quit the thread event loop
        self.thread.wait()  # Wait for thread to finish
        event.accept()  # Allow closing


def main_gui(rawfolder=None, syncbunch=None, autoload=True):
    app = QApplication(sys.argv)
    window = TrXASViewer(rawfolder=rawfolder, syncbunch=syncbunch, autoload=autoload)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_gui()
