import os
import sys
import time
import numpy as np
import json
import pyqtgraph as pg
from pathlib import Path
import traceback
from multiprocessing import Process
from .generated_modeling_ui import Ui_MainWindow
from .trxas_graph import (
    draw_decay_graph_with_top_nodes,
    find_initial_states,
    verify_decay_paths,
)
from PySide6.QtCore import (
    QDir,
    QSortFilterProxyModel,
    Qt,
    Signal,
    Slot,
    QObject,
    QThread,
    QTimer,
    QByteArray,
)

from PySide6.QtWidgets import (
    QSizePolicy,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QCheckBox,
    QTabWidget,
    QDialog,
    QApplication,
    QFileDialog,
    QFileSystemModel,
    QMainWindow,
    QHeaderView,
)

from .trxas_dataset import (
    TrXASDatasetManager,
    create_trxas_cache_from_flist,
)
from .utilities import format_time
from .widgets import (
    VlockedRectROI,
    SaveOptionsDialog,
    show_error_dialog,
    TrXASResultTableModel,
    ParameterTableModel,
)

from PySide6.QtGui import QPixmap
from PySide6.QtCore import QBuffer, QByteArray, QIODevice

from .dtype_cache import DataTypeCache
import logging
from . import __version__

CONFIG_FILE = Path.home() / ".trxasviewer" / "config.json"
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
PGCOLORS = ("r", "b", "k", "m", "g", "m", "y")
PGSYMBOLS = ("o", "s", "t", "d", "+", "*", "x", "p", "h")

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

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow


def convert_npz_to_dict(npz_filename):
    npz_file = np.load(npz_filename, allow_pickle=True)
    raw = dict(npz_file)
    return {
        k: (v.item() if isinstance(v, np.ndarray) and v.shape == () else v)
        for k, v in raw.items()
    }


def init_plots(graph_widget):
    img_hdl = []
    for _ in range(3):
        view = graph_widget.addViewBox(lockAspect=True)
        img = pg.ImageItem()
        view.addItem(img)
        img_hdl.append(img)

    graph_widget.nextRow()
    # Second row: 3 plot widgets
    for _ in range(3):
        plot = graph_widget.addPlot()
        img_hdl.append(plot)

    # Example: set image and line plot
    dummy_img = np.random.rand(100, 100)
    for img in img_hdl[0:3]:
        img.setImage(dummy_img)

    for plot in img_hdl[3:]:
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        plot.plot(x, y)
    return img_hdl


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
        self.spinBox_nstates.valueChanged.connect(self.change_model)
        self.fit_param_model = None
        self.fit_param = None

    def closeEvent(self, event):
        self.closed.emit()  # Let the main window know we closed
        super().closeEvent(event)

    def change_model(self):
        MAX_STATES = 6  # including ground state
        num_states = self.spinBox_nstates.value()
        model = self.comboBox_model.currentText()
        state_mat = self.gen_state_mat(num_states, model)
        for n in range(1, MAX_STATES + 1):
            for m in range(1, min(n + 1, MAX_STATES)):
                widget = getattr(self, f"checkBox_m{n}{m}")
                if n > num_states and n != MAX_STATES:
                    widget.setChecked(False)
                    widget.setEnabled(False)
                else:
                    if model in ("parallel", "sequential"):
                        flag = state_mat[n - 1, m - 1]
                        widget.setChecked(flag)
                        widget.setEnabled(flag)
                    else:
                        widget.setEnabled(True)
        self.draw_graph()

    def gen_state_mat(self, num_states, model="parallel"):
        state = np.zeros((6, 5), dtype=bool)
        if model == "parallel":
            state[np.diag_indices(num_states)] = True
            state[-1, :] = True
        elif model == "sequential":
            for n in range(num_states):
                for m in range(max(0, n - 1), n + 1):
                    state[n, m] = True
            # this is the sink state
            state[-1, num_states - 1] = True
        return state

    def get_state_mat(self):
        state = np.zeros((6, 5), dtype=bool)
        for n in range(1, 7):
            for m in range(1, min(n + 1, 6)):
                widget = getattr(self, f"checkBox_m{n}{m}")
                state[n - 1, m - 1] = widget.isChecked()
        return state

    def draw_graph(self):
        state_mat = self.get_state_mat()
        pos_idx = np.where(np.sum(state_mat[0:-1], axis=1) > 0)[0]
        if len(pos_idx) == 0:
            return
        else:
            max_idx = np.max(pos_idx) + 1

        adj_matrix = np.zeros((max_idx + 1, max_idx + 1))
        adj_matrix[0:max_idx, 0:max_idx] = state_mat[0:max_idx, 0:max_idx]
        # append ground state connections
        adj_matrix[-1][0:max_idx] = state_mat[-1][0:max_idx]

        self.build_parameter(adj_matrix)

        # visualize the graph
        graph_bytes = draw_decay_graph_with_top_nodes(adj_matrix, output="bytes")
        # Convert image bytes to QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(graph_bytes), "PNG")
        # QLabel to display image
        self.label_graph.setPixmap(pixmap)
        self.label_graph.setScaledContents(True)
        # This will scale the pixmap to fit the label size
        # Set size policy to maintain aspect ratio
        self.label_graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def build_parameter(self, adj_matrix):
        num_states = adj_matrix.shape[0]
        adj_matrix[-1, -1] = False
        initial_states = find_initial_states(adj_matrix)
        initial_value = np.zeros(num_states)
        initial_states_idx = [int(s[1:]) - 1 for s in initial_states]
        initial_value[initial_states_idx] = 1.0

        num_params = np.sum(adj_matrix).astype(np.int32)
        idx_matrix = np.zeros_like(adj_matrix, dtype=np.int32) - 1
        index = np.arange(num_params)
        nz_coord = np.nonzero(adj_matrix == True)
        idx_matrix[nz_coord] = index
        constraints = []

        def create_dynamic_eq_constraint(indices):
            return {"type": "eq", "fun": lambda x: np.sum(x[indices])}

        for n in range(adj_matrix.shape[1]):
            column = idx_matrix[:, n]
            values = column[column >= 0]
            if len(values) >= 1:
                cs = create_dynamic_eq_constraint(values)
                constraints.append(cs)
            if len(values) == 1:
                raise ValueError(f"No parent states found for state S{n+1}")

        self.fit_param = []
        for i in range(nz_coord[0].shape[0]):
            i, j = nz_coord[0][i] + 1, nz_coord[1][i] + 1
            if i == adj_matrix.shape[0]:
                i = "g"
            if i == j:
                self.fit_param.append([f"t_{j}{i}", "us", -10, 0.0, -5])
            else:
                self.fit_param.append([f"t_{j}{i}", "us", 0, 10.0, 5])

        headers = ["Name", "Unit", "Min", "Max", "Fit Value"]
        # Data structure: [name, unit, min, max, fit_value]
        self.fit_param_model = ParameterTableModel(self.fit_param, headers)
        self.tableView_parameters.setModel(self.fit_param_model)
        header = self.tableView_parameters.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    def load_dset(self):
        # f, _ = QFileDialog.getOpenFileName(
        #     self, "Load Dataset", "", "NumPy Archive (*.npz)"
        # )
        f = "/Users/mqichu/Documents/trxas_data/kinetics_results/result_setup-full-00242-00258/results.npz"
        if f:
            data = convert_npz_to_dict(f)
            self.model.add_data(data)

    def plot_data(self, index):
        pass


def main_modeling_gui(args, **kwargs):
    app = QApplication(sys.argv)
    window = TrXASModeler()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_modeling_gui()
