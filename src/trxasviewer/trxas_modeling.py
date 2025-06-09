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
)
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


class TrXASModeler(QMainWindow, Ui_MainWindow):
    closed = Signal()

    def __init__(self):
        super(TrXASModeler, self).__init__()
        self.setupUi(self)
        self.setWindowTitle(f"TrXASModeler v{__version__}")
        self.model = TrXASResultTableModel()
        self.tableView.setModel(self.model)

    def closeEvent(self, event):
        self.closed.emit()  # Let the main window know we closed
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = TrXASModeler()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
