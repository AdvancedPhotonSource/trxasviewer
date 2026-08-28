import logging
import random
import sys
import json
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
import pyqtgraph as pg
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QMainWindow,
    QSizePolicy,
    QFileDialog,
)

from trxasviewer import __version__
from trxasviewer.core.constants import TIME_SCALES
from trxasviewer.core.fitting import run_single_optimization
from trxasviewer.modeling_gui.generated_modeling_ui import Ui_MainWindow
from trxasviewer.gui.view.pg_plot import plot_kinetics_profile
from trxasviewer.core.graph import render_decay_graph
from trxasviewer.core.result import TrXASResult
from trxasviewer.core.utilities import NumpyEncoder
from trxasviewer.gui.view.widgets import (
    ParameterTableModel,
    TrXASResultTableModel,
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


def load_trxas_result(npz_filename):
    npz_file = np.load(npz_filename, allow_pickle=True)
    raw = dict(npz_file)
    data = {
        k: (v.item() if isinstance(v, np.ndarray) and v.shape == () else v)
        for k, v in raw.items()
    }
    return TrXASResult(data)


def init_plots(pg_gfit_svd, pg_gfit_display, pg_pfit_display):
    """
    Initializes a 2x3 grid of plots in a GraphicsLayoutWidget,
    with consistent column widths and labels for all plots/images.
    """
    #
    img_hdl = {}

    # Add the SVD plot/image
    plot = pg_gfit_svd.addPlot(title="SVD")
    img_hdl["svd_spectrum"] = plot

    # Add the concentration and spectra plots/images
    labels = [
        "concentration",
        "spectra",
    ]
    for i in range(len(labels)):
        plot = pg_gfit_display.addPlot(title=labels[i].capitalize())
        img_hdl[labels[i]] = plot

    # add profile fitting plots
    # Add the SVD plot/image
    plot = pg_pfit_display.addPlot()
    img_hdl["kinetics_profiles"] = plot

    return img_hdl


class FitWorker(QObject):
    finished = Signal(object)
    progress = Signal(int, int)  # completed, total
    error = Signal(str)

    def __init__(
        self,
        dset,
        state_matrix,
        bounds,
        fit_trange=None,
        num_tries=100,
        method="L-BFGS-B",
        num_workers=4,
        tolerance=1e-6,
        dset_kwargs=None,
    ):
        super().__init__()
        self.dset = dset
        self.state_matrix = state_matrix
        self.bounds = bounds
        self.fit_trange = fit_trange
        self.num_tries = num_tries
        self.num_workers = num_workers
        self.method = method
        self.tolerance = tolerance
        self.dset_kwargs = dset_kwargs

    @Slot()
    def run(self):
        fit_pack = self.dset.get_kinetic_data(**self.dset_kwargs)
        total_run = fit_pack["num_payloads"] * self.num_tries
        payloads = fit_pack.pop("payloads")
        try:
            for index, (key, value) in enumerate(payloads.items()):
                fit_result = self.single_run(
                    value["t_axis"],
                    value["diff"],
                    self.fit_trange,
                    self.num_tries * index,
                    total_run,
                )
                self.dset.append_fitting_result(key, fit_result, fit_pack)
            self.finished.emit("Done")
        except Exception as e:
            self.error.emit(str(e))
            traceback.print_exc()
        logger.info("Fitting process finished")

    def single_run(self, t_axis, diff_map, fit_trange, offset, total_run):
        OPT_METHODS = ["L-BFGS-B", "TNC", "SLSQP", "Powell", "trust-constr"]
        best_loss = np.inf
        best_opt_params = None
        best_final_concentrations = None
        best_final_spectra = None
        completed = 0
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [
                executor.submit(
                    run_single_optimization,
                    t_axis,
                    diff_map,
                    self.state_matrix,
                    self.bounds,
                    fit_trange,
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
                    traceback.print_exc()
                finally:
                    completed += 1
                    self.progress.emit(completed + offset, total_run)

        return {
            "params": best_opt_params,
            "concentrations": best_final_concentrations,
            "spectra": best_final_spectra,
            "fitted": best_final_concentrations @ best_final_spectra,
        }


class TrXASModeler(QMainWindow, Ui_MainWindow):
    closed = Signal()

    def __init__(self):
        super(TrXASModeler, self).__init__()
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(imageAxisOrder="row-major")
        self.setupUi(self)
        self._init_graph_canvas()
        self._init_state_matrix_tooltips()
        self.setWindowTitle(f"TrXASModeler v{__version__}")
        self.model = TrXASResultTableModel()
        self.tableView.setModel(self.model)
        # Stretch both columns to fill the full width
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.img_hdl = init_plots(
            self.pg_gfit_svd, self.pg_gfit_display, self.pg_pfit_display
        )
        # self.preview_hdl = init_preview_plots(self.pg_preview)
        self.pg_diff.getView().setAspectLocked(False)
        self.pg_diff.setColorMap(pg.colormap.get("CET-D1A"))

        self.pushButton_load.clicked.connect(self.load_dset)
        self.pushButton_plot.clicked.connect(self.on_fit_finished)
        self.pushButton_save_model.clicked.connect(self.save_model)
        self.pushButton_load_model.clicked.connect(self.load_model)
        self.comboBox_model.currentIndexChanged.connect(self.change_model)
        self.pushButton_updatemodel.clicked.connect(self.draw_graph)
        self.pushButton_fit.clicked.connect(self.fit_data)
        self.spinBox_nstates.valueChanged.connect(self.change_model)
        self.tableView.doubleClicked.connect(self.mouse_select_dataset)
        self.change_model()
        self.fit_param_model = None
        self.fit_param = None
        self.curr_dset = None
        self.progressBar_fit.setValue(0)
        self.thread = None
        self.is_fitting_running = False

    def closeEvent(self, event):
        self.closed.emit()  # Let the main window know we closed
        super().closeEvent(event)

    def _init_graph_canvas(self):
        """Replace the static label_graph placeholder with a live matplotlib canvas."""
        self.graph_figure = Figure()
        self.graph_ax = self.graph_figure.add_subplot(111)
        self.graph_canvas = FigureCanvasQTAgg(self.graph_figure)
        self.graph_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = self.label_graph.parentWidget().layout()
        layout.replaceWidget(self.label_graph, self.graph_canvas)
        self.label_graph.deleteLater()
        del self.label_graph

        # groupBox_3 (the graph's container) and its row in gridLayout_2 default
        # to a size-hint-based policy/stretch, so the canvas would otherwise be
        # squeezed to a small fixed area instead of filling available space.
        self.groupBox_3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.gridLayout_2.setRowStretch(1, 1)

    def _init_state_matrix_tooltips(self):
        """Explain the physical meaning of each State-Matrix checkbox.

        checkBox_m{n+1}{m+1} follows the same (row=n, col=m) convention used
        throughout this class (e.g. get_state_mat, build_parameter): m<n is a
        transfer State(m+1)->State(n+1), n==m is the diagonal "state is active"
        flag, and n==ground_row is the decay/recovery pathway to the ground state.
        """
        ground_row = MAX_STATES - 1
        for n in range(MAX_STATES):
            for m in range(n + 1):
                widget = getattr(self, f"checkBox_m{n + 1}{m + 1}", None)
                if widget is None:
                    continue

                if n == ground_row:
                    summary = f"State {m + 1} → Ground State (recovery)"
                    detail = (
                        f"Adds fit parameter t_{m + 1}0: lifetime of State {m + 1} "
                        "decaying back to the ground state (rate = 1/t)."
                    )
                elif n == m:
                    summary = f"State {n + 1} is an active/source state"
                    detail = (
                        f"Marks State {n + 1} as independently populated at t=0. "
                        "Does not add a fit parameter."
                    )
                else:
                    summary = f"State {m + 1} → State {n + 1}"
                    detail = (
                        f"Adds fit parameter t_{m + 1}{n + 1}: lifetime for "
                        f"population transfer from State {m + 1} into "
                        f"State {n + 1} (rate = 1/t)."
                    )

                widget.setToolTip(f"{summary}\n{detail}")
                widget.setStatusTip(f"{summary} — {detail}")

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
                    flag = bool(state_mat[n, m])
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

    def set_state_mat(self, mat):
        full_state = np.zeros((MAX_STATES, MAX_STATES), dtype=bool)
        full_state[0 : mat.shape[0] - 1, 0 : mat.shape[1]] = mat[0:-1]
        full_state[-1, 0 : mat.shape[1]] = mat[-1]
        for n in range(MAX_STATES):
            for m in range(n + 1):
                widget = getattr(self, f"checkBox_m{n+1}{m+1}", None)
                if widget:
                    if full_state[n, m]:
                        widget.setChecked(True)
                    else:
                        widget.setChecked(False)

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
        # visualize the graph directly onto the live canvas
        flag, msg = render_decay_graph(self.graph_ax, adj_matrix)
        if not flag:
            self.graph_ax.clear()
            self.graph_ax.axis("off")
            self.graph_canvas.draw_idle()
            show_error_dialog(self, title="Failed to generate graph", message=msg)
            return

        self.graph_figure.tight_layout()
        self.graph_canvas.draw_idle()

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

    def get_fit_parameters_bounds(self):
        bounds = list(zip(self.fit_param["Min"].values, self.fit_param["Max"].values))
        scale = [TIME_SCALES[unit] for unit in self.fit_param["Unit"]]
        bounds = np.array(bounds) * np.array(scale).reshape(-1, 1)
        return bounds

    def save_model(self):
        if self.fit_param is not None:
            fit_param = self.fit_param.to_dict()
        else:
            fit_param = None
        state_mat = self.get_state_mat()
        model = {
            "fit_param": fit_param,
            "state_mat": state_mat,
            "num_states": self.spinBox_nstates.value(),
            "model_type": self.comboBox_model.currentText(),
        }
        file_filter = "JSON File (*.json);;Text File (*.txt);;All Files (*)"
        save_fname, _ = QFileDialog.getSaveFileName(
            self,
            "Save Model to File As",
            "",  # use last location
            file_filter,
        )
        if save_fname:
            with open(save_fname, "w") as fp:
                json.dump(model, fp, indent=4, cls=NumpyEncoder)

    def load_model(self):
        open_fname, _ = QFileDialog.getOpenFileName(
            self,
            "Select a Model File to Load",
            "",  # use last location
            "JSON File (*.json);;Text File (*.txt);;All Files (*)",
        )
        if open_fname:
            with open(open_fname, "r") as fp:
                model = json.load(fp)
            model["state_mat"] = np.array(model["state_mat"], dtype=bool)
            model_type = model.get("model_type")
            type_index = {"parallel": 0, "sequential": 1, "advanced": 2}[model_type]
            self.comboBox_model.setCurrentIndex(type_index),
            self.spinBox_nstates.setValue(model["num_states"])
            if model_type == "advanced":
                self.set_state_mat(model["state_mat"])

            self.draw_graph()
            if model["fit_param"] not in [None, "none"]:
                self.fit_param = pd.DataFrame(model["fit_param"])
                self.fit_param_model = ParameterTableModel(self.fit_param)
                self.tableView_parameters.setModel(self.fit_param_model)

    def fit_data(self):
        if self.fit_param is None or self.curr_dset is None or self.is_fitting_running:
            return

        num_cores = psutil.cpu_count(logical=False)
        num_workers = min(num_cores, self.spinBox_num_workers.value() or num_cores)

        fit_tscale = TIME_SCALES[self.comboBox_fit_tunit.currentText()]
        fit_trange = (
            [
                self.doubleSpinBox_fit_tmin.value() * fit_tscale,
                self.doubleSpinBox_fit_tmax.value() * fit_tscale,
            ]
            if self.checkBox_fit_trange.isChecked()
            else [0, np.inf]
        )

        bsl_tscale = TIME_SCALES[self.comboBox_bsl_tunit.currentText()]

        opt_kwargs = {
            "num_workers": num_workers,
            "num_tries": self.spinBox_num_tries.value(),
            "method": self.comboBox_opt_method.currentText(),
            "fit_trange": fit_trange,
        }
        dset_kwargs = {
            "bsl_trange": [
                self.doubleSpinBox_bsl_tmin.value() * bsl_tscale,
                self.doubleSpinBox_bsl_tmax.value() * bsl_tscale,
            ],
            "bsl_mode": self.comboBox_bsl_trange.currentText(),
            "fit_method": self.comboBox_fit_method.currentText(),
        }
        logger.info(f"{opt_kwargs=}")
        logger.info(f"{dset_kwargs=}")

        logger.info(
            f"start fitting with {num_workers} workers and {opt_kwargs['num_tries']} total tries"
        )

        self.is_fitting_running = True
        self.pushButton_fit.setDisabled(True)
        self.progressBar_fit.setMaximum(100)
        self.progressBar_fit.setValue(0)

        self.thread = QThread()
        self.worker = FitWorker(
            self.curr_dset,
            self.get_state_mat(),
            self.get_fit_parameters_bounds(),
            dset_kwargs=dset_kwargs,
            **opt_kwargs,
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

    def on_fit_finished(self, placeholder=None):
        self.pushButton_fit.setEnabled(True)
        self.is_fitting_running = False
        scale = [TIME_SCALES[unit] for unit in self.fit_param["Unit"]]
        self.fit_param["Fit Value"] = (
            self.curr_dset.fitting_results["global"]["params"] / scale
        )
        self.fit_param_model.layoutChanged.emit()

        payload = self.curr_dset.fitting_results.get("global", None)
        if payload:
            self.plot_global_fitting(payload["concentrations"], payload["spectra"])
        fitted_data = self.curr_dset.get_fitted_kinetic_profiles()
        if fitted_data:
            self.plot_profile_fitting(fitted_data)

    def load_dset(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Load Dataset", "", "NumPy Archive (*.npz)"
        )
        # f = "/Users/mqichu/Documents/trxas_data/kinetics_results/result_setup-full-00242-00258/results.npz"
        if f:
            dset = load_trxas_result(f)
            self.select_dataset(dset)

    def select_dataset(self, dset, append=True):
        if dset is None:
            return
        self.curr_dset = dset

        if append:
            self.model.add_data(dset)

        tmin, tmax, tunit = dset.get_time_range_and_unit()
        self.doubleSpinBox_bsl_tmin.setValue(tmin)
        self.doubleSpinBox_bsl_tmax.setValue(0.0)
        self.doubleSpinBox_fit_tmin.setValue(0.0)
        self.doubleSpinBox_fit_tmax.setValue(tmax)
        index = self.comboBox_bsl_tunit.findText(tunit, Qt.MatchFixedString)
        self.comboBox_bsl_tunit.setCurrentIndex(index)
        self.comboBox_fit_tunit.setCurrentIndex(index)
        self.update_plot()
    
    def mouse_select_dataset(self, event):
        if self.model is not None:
            self.select_dataset(self.model.get_data(event.row()), append=False)

    def update_plot(self):
        pen = pg.mkPen(color="blue", width=5)
        self.img_hdl["svd_spectrum"].plot(
            self.curr_dset.get_svd_spectrum(), pen=pen, symbol="o"
        )
        self.img_hdl["svd_spectrum"].setLabel("bottom", "Component Index")
        self.img_hdl["svd_spectrum"].setLabel("left", "SVD Magnitude")

        cdata, levels = self.curr_dset.combined_fitting_data(None, None)

        self.pg_diff.clear()
        plot_item = self.pg_diff.getView()
        items_to_remove = []

        # Iterate through all items currently in the PlotItem
        for item in plot_item.addedItems:
            # Check if the item is a TextItem (or a subclass of it)
            if isinstance(item, pg.TextItem):
                items_to_remove.append(item)

        # Remove them after iterating to avoid modifying list during iteration
        for item in items_to_remove:
            plot_item.removeItem(item)

        self.pg_diff.setImage(cdata, levels=levels)
        vsize, hsize = cdata.shape[0] + 3, cdata.shape[1] // 3
        labels_info = [
            ("Raw", hsize * 0.5, (255, 0, 0)),  # Yellow
            ("Fit", hsize * 1.5, (0, 255, 0)),  # Cyan
            ("Residual", hsize * 2.5, (0, 0, 255)),  # Magenta
        ]
        # Add text labels using a for loop
        for text_str, x_pos, color in labels_info:
            text_item = pg.TextItem(text_str, color=color)
            text_item.setPos(x_pos, vsize)
            text_item.setAnchor((0.5, 0.5))  # Left-middle anchor
            plot_item.addItem(text_item)

        self.img_hdl["kinetics_profiles"].clear()
        if self.checkBox_kinetics_profiles.isChecked():
            self.groupBox_kprofiles.show()
            plot_kinetics_profile(self.curr_dset, self.img_hdl["kinetics_profiles"])
        else:
            self.groupBox_kprofiles.hide()

    def plot_global_fitting(self, concentration, spectra):
        show_groundstate = self.checkBox_show_groundstate.isChecked()
        num_states = concentration.shape[1]
        names = [f"state_{idx}" for idx in list(range(1, num_states)) + [0]]

        if not show_groundstate:
            concentration = concentration[:, :-1]
            spectra = spectra[0:-1]

        self.img_hdl["concentration"].clear()
        self.img_hdl["concentration"].addLegend()
        for idx, line in enumerate(concentration.T):
            color = PGCOLORS[idx % len(PGCOLORS)]  # Generate a
            pen = pg.mkPen(color=color, width=5)
            self.img_hdl["concentration"].plot(
                self.curr_dset.t_axis, line, pen=pen, name=names[idx]
            )
        self.img_hdl["concentration"].setLabel("bottom", "Time", unit="s")
        self.img_hdl["concentration"].setLabel("left", "Concentration")

        self.img_hdl["spectra"].clear()
        self.img_hdl["spectra"].addLegend()
        for idx, line in enumerate(spectra):
            color = PGCOLORS[idx % len(PGCOLORS)]  # Generate a
            pen = pg.mkPen(color=color, width=5)
            self.img_hdl["spectra"].plot(line, pen=pen, name=names[idx])
        self.img_hdl["spectra"].setLabel("bottom", "Energy Index")
        self.img_hdl["spectra"].setLabel("left", "Absorption Coefficient")

        cdata, levels = self.curr_dset.combined_fitting_data(concentration, spectra)
        self.pg_diff.setImage(cdata, levels=levels)

    def plot_profile_fitting(self, fitted_data):
        plot_kinetics_profile(
            self.curr_dset,
            self.img_hdl["kinetics_profiles"],
            fit_data=fitted_data,
            points_only=True,
        )


def main_modeling_gui(args, **kwargs):
    if sys.platform.startswith('win'):
        # This is required for multiprocessing to work correctly on Windows
        from multiprocessing import freeze_support
        freeze_support()
    app = QApplication(sys.argv)
    window = TrXASModeler()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_modeling_gui(None)
