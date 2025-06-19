import json
import logging
import os
import sys
import time
import psutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import random

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import (
    QBuffer,
    QByteArray,
    QDir,
    QIODevice,
    QObject,
    QSortFilterProxyModel,
    Qt,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFileSystemModel,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
)

from . import __version__
from .constants import TIME_SCALES
from .fitting import run_single_optimization
from .pg_plot import plot_kinetics_profile, plot_kinetics_error
from .generated_modeling_ui import Ui_MainWindow
from .trxas_graph import draw_decay_graph_with_top_nodes
from .trxas_result import TrXASResult
from .utilities import format_time
from .widgets import (
    ParameterTableModel,
    SaveOptionsDialog,
    TrXASResultTableModel,
    VlockedRectROI,
    show_error_dialog,
)

CONFIG_FILE = Path.home() / ".trxasviewer" / "config.json"
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
PGCOLORS = ("r", "b", "k", "m", "g", "m", "y")
PGSYMBOLS = ("o", "s", "t", "d", "+", "*", "x", "p", "h")
MAX_STATES = 6  # including ground state

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


def load_trxas_result(npz_filename):
    npz_file = np.load(npz_filename, allow_pickle=True)
    raw = dict(npz_file)
    data = {
        k: (v.item() if isinstance(v, np.ndarray) and v.shape == () else v)
        for k, v in raw.items()
    }
    return TrXASResult(data)


def init_plots(graph_widget):
    """
    Initializes a 2x3 grid of plots in a GraphicsLayoutWidget,
    with consistent column widths and labels for all plots/images.
    """
    import pyqtgraph as pg

    img_hdl = {}
    labels = [
        "diff",
        "fit",
        "residual",
        "svd_spectrum",
        "concentration",
        "spectra",
    ]

    # First Row: PlotItems with ImageItems inside
    for i in range(3):
        plot = graph_widget.addPlot()
        plot.setTitle(labels[i].capitalize())
        plot.getViewBox().setAspectLocked(False)
        plot.hideAxis("left")
        plot.hideAxis("bottom")
        img = pg.ImageItem()
        plot.addItem(img)
        img_hdl[labels[i]] = img

    graph_widget.nextRow()

    # Second Row: PlotItems with axis/labels
    for i in range(3):
        plot = graph_widget.addPlot(title=labels[i + 3].capitalize())
        img_hdl[labels[i + 3]] = plot

    return img_hdl


class FitWorker(QObject):
    finished = Signal(object, object, object)  # opt_param, concentrations, spectra
    progress = Signal(int, int)  # completed, total
    error = Signal(str)

    def __init__(
        self,
        fit_param,
        curr_dset,
        get_state_mat,
        num_tries=100,
        method="L-BFGS-B",
        num_workers=4,
        tolerance=1e-6,
    ):
        super().__init__()
        self.fit_param = fit_param
        self.curr_dset = curr_dset
        self.get_state_mat = get_state_mat
        self.num_tries = num_tries
        self.num_workers = num_workers
        self.method = method
        self.tolerance = tolerance

    @Slot()
    def run(self):
        OPT_METHODS = ["L-BFGS-B", "TNC", "SLSQP", "Powell", "trust-constr"]
        try:
            bounds = list(
                zip(self.fit_param["Min"].values, self.fit_param["Max"].values)
            )
            scale = [TIME_SCALES[unit] for unit in self.fit_param["Unit"]]
            bounds = np.array(bounds) * np.array(scale).reshape(-1, 1)
            adj_matrix = self.get_state_mat()

            best_loss = np.inf
            best_opt_params = None
            best_final_concentrations = None
            best_final_spectra = None
            completed = 0

            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                futures = [
                    executor.submit(
                        run_single_optimization,
                        self.curr_dset.t_axis,
                        self.curr_dset.diff,
                        adj_matrix,
                        bounds,
                        self.tolerance,
                        (
                            random.choice(OPT_METHODS)
                            if self.method == "RandomChoice"
                            else self.method
                        ),
                        i,
                    )
                    for i in range(self.num_tries)
                ]

                for completed, future in enumerate(as_completed(futures), start=1):
                    try:
                        loss, opt_params, final_conc, final_spec, res = future.result()
                        if loss < best_loss:
                            best_loss = loss
                            best_opt_params = opt_params
                            best_final_concentrations = final_conc
                            best_final_spectra = final_spec
                    except Exception as exc:
                        logger.error(f"A run failed: {exc}")
                    finally:
                        completed += 1
                        self.progress.emit(completed, self.num_tries)

            self.finished.emit(
                best_opt_params, best_final_concentrations, best_final_spectra
            )

        except Exception as e:
            self.error.emit(str(e))


class TrXASModeler(QMainWindow, Ui_MainWindow):
    closed = Signal()

    def __init__(self):
        super(TrXASModeler, self).__init__()
        self.setupUi(self)
        self.setWindowTitle(f"TrXASModeler v{__version__}")
        self.model = TrXASResultTableModel()
        self.tableView.setModel(self.model)
        # Stretch both columns to fill the full width
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.img_hdl = init_plots(self.display)
        self.pushButton_load.clicked.connect(self.load_dset)
        self.comboBox_model.currentIndexChanged.connect(self.change_model)
        self.pushButton_updatemodel.clicked.connect(self.draw_graph)
        self.pushButton_fit.clicked.connect(self.fit_data)
        self.spinBox_nstates.valueChanged.connect(self.change_model)
        self.fit_param_model = None
        self.fit_param = None
        self.curr_dset = None
        self.progressBar_fit.setValue(0)
        self.thread = None
        self.is_fitting_running = False

    def closeEvent(self, event):
        self.closed.emit()  # Let the main window know we closed
        super().closeEvent(event)

    def change_model(self):
        """
        Updates the state checkboxes based on the selected model and number of states.
        """
        num_states = self.spinBox_nstates.value()
        model = self.comboBox_model.currentText()
        state_mat = self.gen_state_mat(num_states, model)

        for n in range(MAX_STATES):
            for m in range(MAX_STATES):
                widget = getattr(self, f"checkBox_m{n + 1}{m + 1}", None)
                if not widget:
                    continue

                # Determine the state of the widget
                is_enabled = n < num_states or n == MAX_STATES - 1

                # Update widget based on the model
                if model in ("parallel", "sequential"):
                    flag = state_mat[n, m]
                    widget.setChecked(flag)
                    widget.setEnabled(is_enabled and flag)
                else:  # advanced model
                    if is_enabled and m < num_states:
                        widget.setEnabled(True)
                    else:
                        widget.setEnabled(False)

        self.draw_graph()

    def gen_state_mat(self, num_states, model="parallel"):
        state = np.zeros((MAX_STATES, MAX_STATES), dtype=bool)
        if model == "parallel":
            state[np.diag_indices(num_states)] = True
            state[-1, 0:num_states] = True
        elif model == "sequential":
            for n in range(num_states):
                for m in range(max(0, n - 1), n + 1):
                    state[n, m] = True
            # this is the sink state
            state[-1, num_states - 1] = True
        return state

    def get_state_mat(self):
        state = np.zeros((MAX_STATES, MAX_STATES), dtype=bool)
        for n in range(MAX_STATES):
            for m in range(n + 1):
                widget = getattr(self, f"checkBox_m{n+1}{m+1}", None)
                if widget:
                    state[n, m] = widget.isChecked()

        # simplify the matrix by removing unused states
        pos_idx = np.where(np.sum(state[0:-1, 0:-1], axis=1) > 0)[0]
        if len(pos_idx) == 0:
            return None
        else:
            max_idx = np.max(pos_idx) + 1

        adj_matrix = np.zeros((max_idx + 1, max_idx + 1))
        adj_matrix[0:max_idx, 0:max_idx] = state[0:max_idx, 0:max_idx]
        # append ground state connections
        adj_matrix[-1][0:max_idx] = state[-1][0:max_idx]
        return adj_matrix

    def draw_graph(self):
        adj_matrix = self.get_state_mat()
        self.build_parameter(adj_matrix)
        # visualize the graph
        flag, payload = draw_decay_graph_with_top_nodes(adj_matrix, output="bytes")
        if not flag:
            self.label_graph.clear()
            show_error_dialog(self, title="Failed to generate graph", message=payload)
            return
        else:
            graph_bytes = payload

        # Convert image bytes to QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(graph_bytes), "PNG")
        # QLabel to display image
        self.label_graph.setPixmap(pixmap)
        self.label_graph.setScaledContents(True)
        # This will scale the pixmap to fit the label size
        # Set size policy to maintain aspect ratio
        self.label_graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def build_parameter(self, adj_mat):
        num_states = adj_mat.shape[0]
        adj_mat[-1, -1] = False
        rel_mat = np.copy(adj_mat)
        rel_mat[np.diag_indices(num_states)] = 0
        nz_coord = np.nonzero(rel_mat)

        data = []
        for i in range(nz_coord[0].shape[0]):
            i, j = nz_coord[0][i] + 1, nz_coord[1][i] + 1
            if i == num_states:
                i = "0"
            data.append([f"t_{j}{i}", "µs", 0.01, 100.0, np.nan])

        # display fitting parameters
        headers = ["Name", "Unit", "Min", "Max", "Fit Value"]
        self.fit_param = pd.DataFrame(data, columns=headers)
        self.fit_param_model = ParameterTableModel(self.fit_param)
        self.tableView_parameters.setModel(self.fit_param_model)
        header = self.tableView_parameters.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_parameters.setAlternatingRowColors(True)

    def fit_data(self):
        if self.fit_param is None or self.curr_dset is None or self.is_fitting_running:
            return

        num_cores = psutil.cpu_count(logical=False)
        num_workers = min(num_cores, self.spinBox_num_workers.value() or num_cores)

        kwargs = {
            "num_workers": num_workers,
            "num_tries": self.spinBox_num_tries.value(),
            "method": self.comboBox_opt_method.currentText(),
            # "tolerance": self.doubleSpinBox_tolerance.value(),
        }

        logger.info(
            f"start fitting with {num_workers} workers and {kwargs['num_tries']} total tries"
        )

        self.is_fitting_running = True
        self.pushButton_fit.setDisabled(True)
        self.progressBar_fit.setMaximum(100)
        self.progressBar_fit.setValue(0)

        self.thread = QThread()
        self.worker = FitWorker(
            self.fit_param, self.curr_dset, self.get_state_mat, **kwargs
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_fit_finished)
        self.worker.progress.connect(self.on_fit_progress)
        # self.worker.error.connect(self.on_fit_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_fit_progress(self, done, total):
        percent = int(100 * done / max(1, total))
        self.progressBar_fit.setValue(percent)

    def on_fit_finished(self, opt_param, opt_concentrations, opt_spectra):
        self.pushButton_fit.setEnabled(True)
        self.is_fitting_running = False
        scale = [TIME_SCALES[unit] for unit in self.fit_param["Unit"]]
        self.fit_param["Fit Value"] = opt_param / scale
        self.fit_param_model.layoutChanged.emit()
        self.plot_fitting(opt_concentrations, opt_spectra)

    def load_dset(self):
        # f, _ = QFileDialog.getOpenFileName(
        #     self, "Load Dataset", "", "NumPy Archive (*.npz)"
        # )
        f = "/Users/mqichu/Documents/trxas_data/kinetics_results/result_setup-full-00242-00258/results.npz"
        if f:
            dset = load_trxas_result(f)
            self.model.add_data(dset)
            self.curr_dset = dset
            self.update_plot()

    def update_plot(self):
        self.img_hdl["diff"].setImage(self.curr_dset.diff)
        self.img_hdl["diff"].setColorMap(pg.colormap.getFromMatplotlib("viridis"))

        pen = pg.mkPen(color="blue", width=5)
        self.img_hdl["svd_spectrum"].plot(
            self.curr_dset.get_svd_spectrum(), pen=pen, symbol="o"
        )
        self.img_hdl["svd_spectrum"].setLabel("bottom", "Component Index")
        self.img_hdl["svd_spectrum"].setLabel("left", "SVD Magnitude")

    def plot_fitting(self, concentration, spectra):
        self.img_hdl["concentration"].clear()
        self.img_hdl["concentration"].addLegend()
        num_states = concentration.shape[1]
        names = [f"state_{idx}" for idx in list(range(1, num_states)) + [0]]
        for idx, line in enumerate(concentration.T):
            color = PGCOLORS[idx % len(PGCOLORS)]  # Generate a
            pen = pg.mkPen(color=color, width=5)
            self.img_hdl["concentration"].plot(
                self.curr_dset.t_axis, line, pen=pen, name=names[idx]
            )
        self.img_hdl["concentration"].setLabel("bottom", "Time")
        self.img_hdl["concentration"].setLabel("left", "Concentration")

        self.img_hdl["spectra"].clear()
        self.img_hdl["spectra"].addLegend()
        for idx, line in enumerate(spectra):
            color = PGCOLORS[idx % len(PGCOLORS)]  # Generate a
            pen = pg.mkPen(color=color, width=5)
            self.img_hdl["spectra"].plot(line, pen=pen, name=names[idx])
        self.img_hdl["spectra"].setLabel("bottom", "Energy Index")
        self.img_hdl["spectra"].setLabel("left", "Absorption Coefficient")

        res = concentration @ spectra
        self.img_hdl["fit"].clear()
        self.img_hdl["fit"].setImage(res)
        self.img_hdl["fit"].setColorMap(pg.colormap.getFromMatplotlib("viridis"))
        residual = self.curr_dset.diff - res
        self.img_hdl["residual"].clear()
        self.img_hdl["residual"].setImage(residual)
        self.img_hdl["residual"].setColorMap(pg.colormap.getFromMatplotlib("viridis"))


def main_modeling_gui(args, **kwargs):
    app = QApplication(sys.argv)
    window = TrXASModeler()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_modeling_gui()
