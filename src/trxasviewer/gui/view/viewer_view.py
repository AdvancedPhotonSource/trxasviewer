import os
import sys
import json
import logging
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QByteArray, QDir, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFileSystemModel,
    QLineEdit,
    QMainWindow,
    QRadioButton,
    QSpinBox,
    QTabWidget,
)

from trxasviewer import __version__
from trxasviewer.core.utilities import format_time
from trxasviewer.gui.view.generated_ui import Ui_MainWindow
from trxasviewer.gui.view.widgets import (
    VlockedRectROI,
    SaveOptionsDialog,
    DatasetFilterModel,
    show_error_dialog,
    show_warning_dialog,
)
from trxasviewer.gui.view.pg_plot import plot_kinetics_profile, plot_kinetics_error

logger = logging.getLogger(__name__)

CONFIG_FILE = Path.home() / ".trxasviewer" / "config.json"
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

PGCOLORS = ("r", "b", "k", "m", "g", "m", "y")
PGSYMBOLS = ("o", "s", "t", "d", "+", "*", "x", "p", "h")

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")
pg.setConfigOptions(antialias=True)
pg.setConfigOptions(imageAxisOrder="row-major")


class ViewerView(QMainWindow, Ui_MainWindow):
    # Signals emitted by the view for controller to handle
    folder_selected = Signal(Path)
    files_selected = Signal(list)
    replot_requested = Signal()
    save_requested = Signal(dict)

    def __init__(self, syncbunch=None, autoload=False, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.image = None
        self.results = None
        self.last_position = None
        self.roi = None
        self.dtype_db = None
        self.kinetics_roi = {}
        self.is_processing = False
        self.modeler = None
        self.auto_save_load = autoload
        self.setWindowTitle(f"TrXASViewer v{__version__}")

        self.setup_imageview()
        self.update_colormap()
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.homePath())
        self.proxy_model = DatasetFilterModel()
        self.proxy_model.setSourceModel(self.fs_model)
        self.treeView_fs.setModel(self.proxy_model)
        self.treeView_fs.setColumnWidth(0, 200)
        self.treeView_fs.setSortingEnabled(True)

        # Widget → Signal connections
        self.pushButton_select_rawfolder.clicked.connect(self._on_folder_button_clicked)
        self.treeView_fs.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.comboBox_cmap.currentIndexChanged.connect(self.update_colormap)
        self.spinBox_roix.valueChanged.connect(self.update_roi)
        self.spinBox_roiy.valueChanged.connect(self.update_roi)
        self.comboBox_channel_num.currentIndexChanged.connect(lambda _: self.replot_requested.emit())
        self.comboBox_target.currentIndexChanged.connect(lambda _: self.replot_requested.emit())
        self.pushButton_replot.clicked.connect(self._on_replot_clicked)
        self.pushButton_select_savefname.clicked.connect(self._on_save_clicked)
        self.comboBox_fileindex_prefix.currentIndexChanged.connect(self.update_fileindex)
        self.toolButton_refresh.clicked.connect(self.reload_rawfolder)
        self.spinBox_syncbunch_number.editingFinished.connect(self._on_sync_param_changed)
        self.spinBox_syncbunch_number.editingFinished.connect(self.update_groundstate_label)
        self.doubleSpinBox_sync_time_us.valueChanged.connect(self._on_sync_param_changed)
        self.radioButton_sync_time.toggled.connect(self._on_sync_param_changed)
        self.pushButton_select_savefname.setDisabled(True)
        self.comboBox_groundstate_method.currentIndexChanged.connect(
            self.update_groundstate_label
        )
        self.pushButton_model.clicked.connect(self._on_model_button_clicked)

        for n in range(5):
            def callback(index=n):
                self.update_binning_params(index=index)
            self.__dict__[f"spinBox_anchor{n}"].editingFinished.connect(callback)
            self.__dict__[f"spinBox_numb{n}"].editingFinished.connect(callback)

        self.setup_tooltips()

        if autoload:
            self.save_load_settings(mode="load")
        if syncbunch:
            self.spinBox_syncbunch_number.setValue(syncbunch)
        self.update_kinetics_signal()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_filesystem)
        self.timer.start()

    # -------------------------------------------------------------------------
    # Display methods — called by controller via model signals
    # -------------------------------------------------------------------------

    def update_image(self, results: dict):
        if results is None:
            return
        if results.get("target") == "normalized-GS":
            self.pushButton_select_savefname.setEnabled(True)
        else:
            self.pushButton_select_savefname.setEnabled(False)
        self.results = results
        self._update_sync_timing_display(results)
        data = self.results["diff"].T
        if self.image is None or data.shape != self.image.shape:
            if self.roi is not None:
                self.pg_hdl_img2d.removeItem(self.roi)
                self.roi = None
            self.spinBox_roix.setValue(data.shape[1] // 10)
            self.spinBox_roiy.setValue(data.shape[0] // 10)
        if self.comboBox_target.currentText() == "normalized-GS":
            vmin, vmax = np.nanpercentile(data.ravel(), [0.2, 99.8])
            vmax = max(abs(vmax), abs(vmin))
            vmin = -vmax
        else:
            vmin, vmax = np.nanpercentile(data.ravel(), [0, 100])
        self.image, prev_image = np.flipud(data), self.image
        self.pg_hdl_img2d.setImage(self.image, levels=(vmin, vmax))
        if (
            prev_image is None
            or prev_image.shape[0] != self.image.shape[0]
            or self.results["dset_type"] != "EXAFS"
        ):
            self.remove_kinetics_ROIs()
        if not self.kinetics_roi:
            self.create_kinetics_ROIs()
        self.mouse_clicked()
        self.update_groundstate_label()

    def update_kinetics(self, results: dict):
        if not results or not results.get("kinetics"):
            return
        use_errorbar = self.checkBox_kinetics_errorbar.isChecked()
        plot_kinetics_profile(results, self.pg_hdl_kinetics, use_errorbar=use_errorbar)
        plot_kinetics_error(results, self.pg_hdl_kinetics_err)

    def update_sync_timing(self, results: dict):
        """Public display method called by controller after new results arrive."""
        if results is None:
            return
        self._update_sync_timing_display(results)

    def _update_sync_timing_display(self, results: dict):
        """Internal helper: updates the timing group-box title from results."""
        bunch_mode = results["bunch_mode"]
        dt_ns = results["delta_t_s"] * 1e9
        self.groupBox_timing.setTitle(
            f"Sync Timing: [{bunch_mode}-bunch]:[{dt_ns:.3f} ns]"
        )

    def clear_display(self):
        self.image = None
        self.results = None

    def set_loading(self, loading: bool):
        self.is_processing = loading
        self.pushButton_replot.setText("Processing..." if loading else "Process")
        self.pushButton_replot.setDisabled(loading)

    def update_progress_bar(self, value: int):
        self.progressBar.setValue(value)

    def update_status(self, msg: str, timeout: int = 5000):
        self.statusBar().showMessage(msg, timeout)

    def show_error(self, title: str, message: str):
        show_error_dialog(self, title, message)

    def show_warning(self, title: str, message: str):
        show_warning_dialog(self, title, message)
        self.update_status(message, timeout=8000)

    def update_folder_ui(self, path: Path, combos: list, dtype_db):
        self.lineEdit_rawfolder.setText(str(path))
        self.dtype_db = dtype_db
        self.proxy_model.update_cache_db(dtype_db)
        self.comboBox_fileindex_prefix.clear()
        self.comboBox_fileindex_prefix.addItems(combos)
        self.comboBox_fileindex_prefix.setCurrentIndex(0)
        new_index = self.fs_model.setRootPath(str(path))
        proxy_new_root = self.proxy_model.mapFromSource(new_index)
        self.treeView_fs.setRootIndex(proxy_new_root)
        self.treeView_fs.sortByColumn(0, Qt.AscendingOrder)

    # -------------------------------------------------------------------------
    # Widget-state reader methods — called by controller to build kwargs
    # -------------------------------------------------------------------------

    def get_channel(self) -> int:
        return int(self.comboBox_channel_num.currentText())

    def get_target(self) -> str:
        return self.comboBox_target.currentText()

    def get_preprocessing_kwargs(self):
        remove_outlier = self.checkBox_outlier.isChecked()
        if remove_outlier:
            outlier_method = self.comboBox_outlier_method.currentText()
        else:
            outlier_method = None
        outlier_threshold = self.doubleSpinBox_outlier_threshold.value()
        return {
            "outlier_method": outlier_method,
            "outlier_threshold": outlier_threshold,
        }

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
            "gs_method": self.comboBox_groundstate_method.currentText(),
            "gs_value": self.spinBox_groundstate_number.value(),
        }
        return norm_kwargs

    def get_kinetics_kwargs(self):
        roi_kwargs = {}
        for n in range(1, 5):
            label = f"ROI{n}"
            roi_kwargs[label] = {
                "center_energy": getattr(
                    self, f"doubleSpinBox_kinetics_ecenter{n}"
                ).value(),
                "delta_energy": getattr(
                    self, f"doubleSpinBox_kinetics_edelta{n}"
                ).value(),
                "enabled": getattr(self, f"checkBox_kinetics_roi{n}").isChecked(),
                "label": label,
            }
        return roi_kwargs

    def get_binning_kwargs(self):
        current_tab_index = self.tabWidget_binning.currentIndex()
        method = self.tabWidget_binning.tabText(current_tab_index)
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

    # -------------------------------------------------------------------------
    # Private signal-emitting slots
    # -------------------------------------------------------------------------

    def _on_folder_button_clicked(self, placeholder=None):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder_path:
            self.folder_selected.emit(Path(folder_path))

    def _on_selection_changed(self, selected, deselected):
        if not self.radioButton_selection_by_mouse.isChecked():
            return
        indexes = self.treeView_fs.selectionModel().selectedIndexes()
        file_paths = []
        for proxy_index in indexes:
            if proxy_index.column() != 0:
                continue
            source_index = self.proxy_model.mapToSource(proxy_index)
            if source_index.isValid():
                file_paths.append(self.fs_model.filePath(source_index))
        self.files_selected.emit(file_paths)

    def _on_save_clicked(self):
        if self.is_processing or self.results is None:
            self.update_status("No data to save.", 3000)
            return
        prefix = self.results["label"]
        dialog = SaveOptionsDialog(parent=self, prefix=prefix)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.save_requested.emit(dialog.get_selected_options())

    def _on_model_button_clicked(self):
        from trxasviewer.modeling_gui.trxas_modeling import TrXASModeler
        from trxasviewer.core.result import TrXASResult
        if self.modeler is None:
            self.modeler = TrXASModeler()
            self.modeler.closed.connect(self._on_modeler_closed)
            self.modeler.show()
        else:
            self.modeler.raise_()
            self.modeler.activateWindow()
        if self.results is not None:
            res_dset = TrXASResult(self.results)
            self.modeler.select_dataset(res_dset)

    def _on_modeler_closed(self):
        self.modeler = None

    def _on_replot_clicked(self):
        if self.radioButton_selection_by_index.isChecked():
            self.process_range()
        else:
            self.replot_requested.emit()

    def _on_sync_param_changed(self):
        self.replot_requested.emit()

    # -------------------------------------------------------------------------
    # UI helpers — kept from TrXASViewer unchanged
    # -------------------------------------------------------------------------

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

    def update_groundstate_label(self):
        text = self.comboBox_groundstate_method.currentText()
        sync_is_bunch = self.radioButton_sync_bunch.isChecked()
        sync_bunch_val = self.spinBox_syncbunch_number.value()
        if text == "orbital-average":
            self.label_groundstate_num.setText("Number of orbitals:")
            if sync_is_bunch and self.results is not None:
                num_bunches = self.results.get("bunch_mode", None)
                if num_bunches:
                    max_orbitals = max(1, sync_bunch_val // num_bunches)
                    self.spinBox_groundstate_number.setMaximum(max_orbitals)
                    if self.spinBox_groundstate_number.value() > max_orbitals:
                        self.spinBox_groundstate_number.setValue(max_orbitals)
                else:
                    self.spinBox_groundstate_number.setMaximum(999999)
            else:
                self.spinBox_groundstate_number.setMaximum(999999)
        elif text == "bunch-average":
            self.label_groundstate_num.setText("Number of bunches:")
            if sync_is_bunch:
                self.spinBox_groundstate_number.setMaximum(sync_bunch_val)
                if self.spinBox_groundstate_number.value() > sync_bunch_val:
                    self.spinBox_groundstate_number.setValue(sync_bunch_val)

    def reload_rawfolder(self):
        raw_folder = self.lineEdit_rawfolder.text()
        self.fs_model.setRootPath("")
        self.fs_model.setRootPath(raw_folder)
        self.refresh_filesystem()

    def refresh_filesystem(self):
        self.proxy_model.invalidate()

    def show_status(self, msg, level=logging.INFO, timeout=5000):
        """Internal alias kept for backward compatibility (e.g. worker error callbacks)."""
        logger.log(level, msg)
        self.statusBar().showMessage(msg, timeout)

    def update_kinetics_signal(self):
        for n in range(1, 5):
            def signal_func(value=None, target=n):
                return self.update_kinetics_ROI(target=target, mode="value-roi")

            widget = getattr(self, f"doubleSpinBox_kinetics_ecenter{n}")
            widget.editingFinished.connect(signal_func)
            widget = getattr(self, f"doubleSpinBox_kinetics_edelta{n}")
            widget.editingFinished.connect(signal_func)
            widget = getattr(self, f"checkBox_kinetics_roi{n}")
            widget.toggled.connect(signal_func)

    def update_binning_params(self, index=0, prev_enable=True):
        if index >= 5:
            return

        length = self.__dict__[f"spinBox_numb{index}"].value()
        anchor = self.__dict__[f"spinBox_anchor{index}"].value()
        label_widget = self.__dict__[f"label_rtime{index}"]

        if index == 0:
            prev_anchor = 0
        else:
            prev_anchor = self.__dict__[f"spinBox_anchor{index - 1}"].value()
        if length == -1 or not prev_enable:
            self.__dict__[f"spinBox_anchor{index}"].setEnabled(False)
            self.update_binning_params(index=index + 1, prev_enable=False)
            label_widget.setText("∞")
            return
        else:
            self.__dict__[f"spinBox_anchor{index}"].setEnabled(True)
            total_size = max(1, anchor - prev_anchor)
            if length == 0:
                length = 1
            fit_size = (total_size + length - 1) // length * length
            fit_anchor = prev_anchor + fit_size
            if fit_anchor != anchor:
                self.__dict__[f"spinBox_anchor{index}"].setValue(fit_anchor)
            if self.results is not None:
                rtime = self.results["delta_t_s"] * fit_anchor * 1e6  # us
                label_widget.setText(f"{rtime:.3f}")
            self.update_binning_params(index=index + 1, prev_enable=True)

    def setup_imageview(self):
        self.pg_hdl_img2d.getView().setAspectLocked(False)

        self.view = self.pg_hdl_img2d.getView()
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("r"))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("b"))
        self.view.addItem(self.vLine, ignoreBounds=True)
        self.view.addItem(self.hLine, ignoreBounds=True)
        self.h_curve = self.pg_hdl_hline.plot(pen="b")
        self.pg_hdl_hline.setLabel("bottom", "Energy", units="keV")
        self.pg_hdl_hline.setLabel("left", "Intensity (a.u.)")
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
        roi_size = (self.spinBox_roix.value(), self.spinBox_roiy.value())
        if self.roi is None:
            self.roi = pg.RectROI(
                [0, 0], roi_size, pen="k", hoverPen="k", sideScalers=False
            )
            self.roi.mouseClickEvent = lambda ev: ev.ignore()
            self.pg_hdl_img2d.addItem(self.roi)

        if self.roi.size() != roi_size:
            self.roi.setSize(roi_size)

        if position is not None and self.roi.pos() != position:
            self.roi.setPos(
                (position[0] - roi_size[0] / 2, position[1] - roi_size[1] / 2)
            )

    def compute_ROI_geometry(self, center, delta):
        energy = self.results["x_axis"]["value"]
        idx = np.argmin(np.abs(energy - center))
        v_size = self.image.shape[0]
        e0, e1 = center - delta, center + delta
        h_size = np.argmin(np.abs(energy - e1)) - np.argmin(np.abs(energy - e0))
        pos = (idx - h_size // 2, 0)
        size = (h_size, v_size)
        return pos, size

    def compute_energy_bounds(self, pos, size):
        energy = self.results["x_axis"]["value"]
        e0 = energy[max(0, int(pos[0]))]
        e1 = energy[min(int(pos[0] + size[0]), len(energy) - 1)]
        center_energy = (e0 + e1) / 2.0
        delta_energy = (e1 - e0) / 2.0
        return center_energy, delta_energy

    def create_kinetics_ROIs(self):
        if (
            self.kinetics_roi
            or not self.results
            or self.results["dset_type"] != "EXAFS"
        ):
            return False

        for label, kwargs in self.get_kinetics_kwargs().items():
            target = int(label[-1])
            pos, size = self.compute_ROI_geometry(
                kwargs["center_energy"], kwargs["delta_energy"]
            )
            color = PGCOLORS[(target - 1) % len(PGCOLORS)]
            pen = pg.mkPen(color, width=2, style=Qt.PenStyle.DotLine)
            handle_pen = pg.mkPen(color=color, width=3)
            handlehover_pen = pg.mkPen(color=color, width=5)
            hover_pen = pg.mkPen(color=color, width=5, style=Qt.PenStyle.DotLine)
            roi = VlockedRectROI(
                pos,
                size,
                pen=pen,
                hoverPen=hover_pen,
                handlePen=handle_pen,
                handleHoverPen=handlehover_pen,
            )
            roi.setVisible(kwargs["enabled"])
            roi.mouseClickEvent = lambda ev: ev.ignore()
            self.kinetics_roi[target] = roi
            self.pg_hdl_img2d.addItem(roi)

            def update_values(value=None, target=target):
                self.update_kinetics_ROI(mode="roi-value", target=target)

            roi.sigRegionChanged.connect(update_values)
        return True

    def remove_kinetics_ROIs(self):
        for roi in self.kinetics_roi.values():
            self.pg_hdl_img2d.removeItem(roi)
        self.kinetics_roi = {}

    def update_kinetics_ROI(self, mode="roi-value", target=None):
        if (
            self.kinetics_roi is None
            or self.results is None
            or self.results["dset_type"] != "EXAFS"
        ):
            return
        if target not in (1, 2, 3, 4):
            return

        if mode == "value-roi":
            kwargs = self.get_kinetics_kwargs()[f"ROI{target}"]
            pos, size = self.compute_ROI_geometry(
                kwargs["center_energy"], kwargs["delta_energy"]
            )
            self.kinetics_roi[target].setPos(pos)
            self.kinetics_roi[target].setSize(size)
            self.kinetics_roi[target].setVisible(kwargs["enabled"])
        elif mode == "roi-value":
            roi = self.kinetics_roi[target]
            center_energy, delta_energy = self.compute_energy_bounds(
                roi.pos(), roi.size()
            )
            (
                getattr(self, f"doubleSpinBox_kinetics_ecenter{target}").setValue(
                    center_energy
                ),
            )
            (
                getattr(self, f"doubleSpinBox_kinetics_edelta{target}").setValue(
                    delta_energy
                ),
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
            self.vLine.setPos(mouse_point.x())
            self.hLine.setPos(mouse_point.y())
            x = int(mouse_point.x())
            y = int(mouse_point.y())
            if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
                horizontal_data = self.image[y, :]
                vertical_data = self.image[:, x]
                x_positions = self.results["x_axis"]["value"][0 : horizontal_data.size]
                y_positions = self.results["t_axis"][0 : vertical_data.size]
                y_positions = y_positions[::-1]

                self.h_curve.setData(x_positions, horizontal_data)
                self.v_curve.setData(vertical_data, y_positions)
                self.update_roi(None, position=(x, y))

                pos_value = self.results["x_axis"]["value"][x]
                pos_time = y_positions[y]
                unit = self.results["x_axis"]["unit"]
                label = self.results["x_axis"]["label"]

                if label == "Energy":
                    self.groupBox_vlinecut.setTitle(
                        f"Vertical Cut @ Energy={pos_value:.4f} {unit}"
                    )
                    self.groupBox_hlinecut.setTitle(
                        f"Horizontal Cut @ Time={format_time(pos_time)}"
                    )
                    self.groupBox_data.setTitle(
                        f"Data @ Energy={pos_value:.4f} {unit}, Time={format_time(pos_time)}"
                    )
                    self.pg_hdl_hline.setLabel("bottom", "Energy", units="keV")
                elif label == "Delay":
                    self.groupBox_vlinecut.setTitle(
                        f"Vertical Cut @ Delay={format_time(pos_value)}"
                    )
                    self.groupBox_hlinecut.setTitle(
                        f"Horizontal Cut @ Time={format_time(pos_time)}"
                    )
                    self.groupBox_data.setTitle(
                        f"Data @ Delay={format_time(pos_value)}, Time={format_time(pos_time)}"
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

    def update_fileindex(self):
        selection = self.comboBox_fileindex_prefix.currentText()
        if selection and self.dtype_db is not None:
            current_prefix, scan_type = selection.split("@")
            vbeg, vend = self.dtype_db.get_index_range(current_prefix, scan_type)
            self.spinBox_fileindex_min.setValue(vbeg)
            self.spinBox_fileindex_max.setValue(vend)

    def process_range(self):
        """Emit files_selected for the index-based file selection mode."""
        if not self.radioButton_selection_by_index.isChecked():
            return
        idx_min = self.spinBox_fileindex_min.value()
        idx_max = self.spinBox_fileindex_max.value()
        selection = self.comboBox_fileindex_prefix.currentText()
        current_prefix, scan_type = selection.split("@")
        file_paths = self.dtype_db.get_valid_filepaths_with_condition(
            current_prefix, scan_type, idx_min, idx_max
        )
        if file_paths:
            self.files_selected.emit(file_paths)

    def save_load_settings(self, mode="save"):
        keys = [
            "comboBox_cmap",
            "comboBox_target",
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
            "tabWidget_binning",
        ]
        keys += [f"spinBox_anchor{n}" for n in range(5)]
        keys += [f"spinBox_numb{n}" for n in range(5)]
        keys += [f"doubleSpinBox_kinetics_ecenter{n}" for n in range(1, 5)]
        keys += [f"doubleSpinBox_kinetics_edelta{n}" for n in range(1, 5)]
        keys += [f"checkBox_kinetics_roi{n}" for n in range(1, 5)]

        if mode == "save":
            config = {}

            for key in keys:
                widget = getattr(self, key, None)
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
                elif isinstance(widget, QTabWidget):
                    config[key] = widget.currentIndex()

            config["main_geometry"] = self.saveGeometry().toBase64().data().decode()
            if hasattr(self, "splitter"):
                config["splitter_state"] = (
                    self.splitter.saveState().toBase64().data().decode()
                )
            if hasattr(self, "splitter_2"):
                config["splitter_2_state"] = (
                    self.splitter_2.saveState().toBase64().data().decode()
                )

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved configuration to [{CONFIG_FILE}]")

        elif mode == "load":
            if CONFIG_FILE.is_file():
                logger.info(f"Loading configuration from [{CONFIG_FILE}]")
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)

                for key, value in config.items():
                    widget = getattr(self, key, None)
                    if key == "main_geometry":
                        self.restoreGeometry(QByteArray.fromBase64(value.encode()))
                    elif key == "splitter_state" and hasattr(self, "splitter"):
                        self.splitter.restoreState(
                            QByteArray.fromBase64(value.encode())
                        )
                    elif key == "splitter_2_state" and hasattr(self, "splitter_2"):
                        self.splitter_2.restoreState(
                            QByteArray.fromBase64(value.encode())
                        )
                    elif isinstance(widget, QLineEdit):
                        widget.setText(value)
                    elif isinstance(widget, QRadioButton):
                        widget.setChecked(value)
                    elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                        widget.setValue(value)
                    elif isinstance(widget, QComboBox):
                        widget.setCurrentIndex(value)
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(value)
                    elif isinstance(widget, QTabWidget):
                        widget.setCurrentIndex(value)
            else:
                logger.error(f"Configuration file [{CONFIG_FILE}] not found.")

    def closeEvent(self, event):
        if self.is_processing:
            return
        if hasattr(self, "_controller"):
            self._controller.shutdown()
        if self.auto_save_load:
            self.save_load_settings(mode="save")
        event.accept()


def main_gui(rawfolder=None, syncbunch=None, autoload=True, reset_cache=False, cache_folder=None):
    from trxasviewer.gui.model.viewer_model import ViewerModel
    from trxasviewer.gui.control.viewer_controller import ViewerController

    if cache_folder is not None:
        cache_folder = Path(cache_folder)
        try:
            cache_folder.mkdir(parents=True, exist_ok=True)
            if not os.access(cache_folder, os.W_OK):
                raise PermissionError(f"no write permission on {cache_folder}")
        except Exception as e:
            logger.warning(f"Cache folder {cache_folder} is not usable ({e}); caching disabled.")
            cache_folder = None

    app = QApplication.instance() or QApplication(sys.argv)
    model = ViewerModel(reset_cache=reset_cache, cache_folder=cache_folder)
    view = ViewerView(syncbunch=syncbunch, autoload=autoload)
    controller = ViewerController(model, view)
    view._controller = controller
    if rawfolder:
        controller.on_folder_selected(Path(rawfolder))
    view.show()
    return app.exec()
