# Copyright © UChicago Argonne LLC
# See LICENSE file for details
from pathlib import Path
import pandas as pd
from trxasviewer.gui.control.workers import _SignalLogHandler  # noqa: F401 — re-exported for backward compat

import pyqtgraph as pg
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPointF, Qt, QSortFilterProxyModel, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from trxasviewer.core.file_io import get_scan_type as _get_scan_type
from trxasviewer.core.dataset import CACHE_PATH


class SaveOptionsDialog(QDialog):
    def __init__(self, prefix="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Options")
        self.setMinimumWidth(400)  # Set a minimum width for better layout

        # --- Widgets ---
        self.instruction_label = QLabel("Select the directory and options for saving:")

        # Directory Selection
        self.dir_label = QLabel("Save Directory:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Click 'Browse...' to select a directory")
        self.path_edit.setReadOnly(True)  # Make it read-only, changed via button
        self.path_edit.setToolTip("Selected save directory (read-only; use Browse... to change).")

        self.prefix_label = QLabel("Subdirectory")
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText(
            "Enter a prefix for the files. It will create a folder with this name."
        )
        self.prefix_edit.setText(prefix)
        self.prefix_edit.setToolTip("Subfolder created under the save directory to hold this result's files.")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setToolTip("Choose the directory to save results into.")

        # Checkboxes
        self.cb_image = QCheckBox("Save Image (.png)")
        self.cb_numpy = QCheckBox("Save NumPy (.npy)")
        self.cb_origin = QCheckBox("Save OriginLab (.txt)")
        self.cb_hdf = QCheckBox("Save HDF5 (.hdf)")
        self.cb_image.setToolTip("Save the 2D map as a PNG image.")
        self.cb_numpy.setToolTip("Save the raw result arrays as a NumPy (.npz) archive.")
        self.cb_origin.setToolTip("Save kinetics traces as tab-delimited text for OriginLab.")
        self.cb_hdf.setToolTip("Save the full result set as an HDF5 file.")
        # Set default checked states if desired
        self.cb_image.setChecked(True)
        self.cb_numpy.setChecked(True)
        self.cb_origin.setChecked(True)
        self.cb_hdf.setChecked(True)

        # Overwrite warning
        self.overwrite_label = QLabel("⚠ This folder already contains results and will be overwritten.")
        self.overwrite_label.setStyleSheet("color: orange;")
        self.overwrite_label.setVisible(False)

        # Standard Buttons (OK, Cancel)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # --- Layout ---
        main_layout = QVBoxLayout(self)

        # Directory Row Layout
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.path_edit)
        dir_layout.addWidget(self.browse_button)

        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_label)
        prefix_layout.addWidget(self.prefix_edit)

        cb_layout = QHBoxLayout()
        cb_layout.addWidget(self.cb_image)
        cb_layout.addWidget(self.cb_numpy)
        cb_layout.addWidget(self.cb_origin)
        cb_layout.addWidget(self.cb_hdf)
        # Add widgets to main layout
        main_layout.addWidget(self.instruction_label)
        main_layout.addLayout(dir_layout)
        main_layout.addLayout(prefix_layout)
        main_layout.addWidget(self.overwrite_label)
        main_layout.addLayout(cb_layout)
        main_layout.addWidget(self.button_box)
        # --- Connections ---
        self.browse_button.clicked.connect(self.select_directory)
        self.prefix_edit.textChanged.connect(self._check_overwrite)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # --- Initial State ---
        # Disable OK button until a directory is selected
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setEnabled(False)

    @Slot()
    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Save Directory", str(Path.home()),
        )
        if directory:
            self.path_edit.setText(directory)
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button:
                ok_button.setEnabled(True)
            self._check_overwrite()

    def _check_overwrite(self):
        directory = self.path_edit.text()
        subdirectory = self.prefix_edit.text()
        if directory and subdirectory:
            dest = Path(directory) / subdirectory / "results.npz"
            self.overwrite_label.setVisible(dest.exists())
        else:
            self.overwrite_label.setVisible(False)

    def get_selected_options(self):
        """
        Returns the selected directory path and checkbox states.
        Should only be called after the dialog has been accepted.
        """
        return {
            "directory": self.path_edit.text(),
            "subdirectory": self.prefix_edit.text(),
            "save_image": self.cb_image.isChecked(),
            "save_numpy": self.cb_numpy.isChecked(),
            "save_hdf": self.cb_hdf.isChecked(),
            "save_origin": self.cb_origin.isChecked(),
        }


class VlockedRectROI(pg.RectROI):
    """
    A rectangular ROI that is locked vertically at y=0 and maintains a constant
    height when resized using handles.
    """

    MIN_WIDTH = 1.0  # Minimum width constant

    def __init__(self, pos, size, **kwargs):
        """
        Initialize the ROI.

        Args:
            pos (QPointF or tuple): Initial position (X will be used, Y is ignored and set to 0)
            size (QPointF or tuple): Initial size (Width and Height)
            **kwargs: Additional arguments passed to RectROI
        """
        # Store the initial height. Ensure size is treated correctly.
        initial_size = pg.Point(size)
        self._locked_height = initial_size.y()

        # Adjust initial position to ensure Y is 0
        initial_pos = pg.Point(pos)
        initial_pos.setY(0.0)

        # Call superclass init
        super().__init__(initial_pos, initial_size, centered=True, **kwargs)

    def update_height(self, height):
        """Update the locked height."""
        self._locked_height = height

    def itemChange(self, change, value):
        """Handle position changes to lock Y position."""
        if change == pg.QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Called when the item's position is about to change
            new_pos = value
            # Force Y position to 0, keep the proposed X
            return QPointF(new_pos.x(), 0.0)
        return super().itemChange(change, value)

    def resize(
        self,
        pos,
        size,
        center=(0.5, 0.5),
        lockAspect=None,
        scaleSnap=None,
        snapScreen=None,
        constraint=None,
        finish=True,
    ):
        """
        Override the resize method to maintain constant height.

        Args:
            pos: The proposed new position (often related to handle movement).
            size: The proposed new size tuple (width, height).
            *args, **kwargs: Other arguments passed to the base resize method.
        """
        # Create a new size tuple with the proposed width but the original height
        new_size = pg.Point(size)
        modified_size = pg.Point(new_size.x(), self._locked_height)

        # Ensure minimum width constraint
        if modified_size.x() < self.MIN_WIDTH:
            modified_size.setX(self.MIN_WIDTH)

        # Call the superclass resize method with the modified size
        # Note: Depending on pyqtgraph version and exact interaction, you might need
        # to adjust how 'pos' is handled here if 'centered=True' causes issues.
        # Often, letting the superclass handle position adjustments during resize is fine.
        super().resize(
            pos,
            modified_size,
            center=center,
            lockAspect=lockAspect,
            scaleSnap=scaleSnap,
            snapScreen=snapScreen,
            constraint=constraint,
            finish=finish,
        )

    # Optional: Override setSize to also enforce height if called programmatically
    def setSize(self, size, update=True, finish=True):
        """Override setSize to ensure height consistency."""
        new_size = pg.Point(size)
        modified_size = pg.Point(new_size.x(), self._locked_height)
        if modified_size.x() < self.MIN_WIDTH:
            modified_size.setX(self.MIN_WIDTH)
        super().setSize(modified_size, update=update, finish=finish)


class HlockedRectROI(pg.RectROI):
    """
    A rectangular ROI that is locked horizontally at x=0 and maintains a constant
    width when resized using handles.
    """

    MIN_HEIGHT = 1.0  # Minimum height constant

    def __init__(self, pos, size, **kwargs):
        """
        Initialize the ROI.

        Args:
            pos (QPointF or tuple): Initial position (Y will be used, X is ignored and set to 0)
            size (QPointF or tuple): Initial size (Width and Height)
            **kwargs: Additional arguments passed to RectROI
        """
        # Store the initial width. Ensure size is treated correctly.
        initial_size = pg.Point(size)
        self._locked_width = initial_size.x()

        # Adjust initial position to ensure X is 0
        initial_pos = pg.Point(pos)
        initial_pos.setX(0.0)

        # Call superclass init
        super().__init__(initial_pos, initial_size, centered=True, **kwargs)

    def update_width(self, width):
        """Update the locked width."""
        self._locked_width = width

    def itemChange(self, change, value):
        """Handle position changes to lock X position."""
        if change == pg.QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            # Force X position to 0, keep the proposed Y
            return QPointF(0.0, new_pos.y())
        return super().itemChange(change, value)

    def resize(
        self,
        pos,
        size,
        center=(0.5, 0.5),
        lockAspect=None,
        scaleSnap=None,
        snapScreen=None,
        constraint=None,
        finish=True,
    ):
        """
        Override the resize method to maintain constant width.
        """
        new_size = pg.Point(size)
        modified_size = pg.Point(self._locked_width, new_size.y())

        # Enforce minimum height
        if modified_size.y() < self.MIN_HEIGHT:
            modified_size.setY(self.MIN_HEIGHT)

        super().resize(
            pos,
            modified_size,
            center=center,
            lockAspect=lockAspect,
            scaleSnap=scaleSnap,
            snapScreen=snapScreen,
            constraint=constraint,
            finish=finish,
        )

    def setSize(self, size, update=True, finish=True):
        """Override setSize to ensure width consistency."""
        new_size = pg.Point(size)
        modified_size = pg.Point(self._locked_width, new_size.y())
        if modified_size.y() < self.MIN_HEIGHT:
            modified_size.setY(self.MIN_HEIGHT)
        super().setSize(modified_size, update=update, finish=finish)


def show_error_dialog(parent, title="Error", message="Something went wrong."):
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()


def show_warning_dialog(parent, title="Warning", message=""):
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()


class TrXASResultTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = []  # list of dicts or tuples

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return 2  # label and created time

    def get_data(self, row):
        if 0 <= row < len(self._data):
            return self._data[row]
        else:
            return None

    def add_data(self, data_dict):
        # Allow passing either a single dict or a list of dicts
        start_row = len(self._data)
        end_row = start_row + 1 - 1

        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self._data.append(data_dict)
        self.endInsertRows()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            res_dset = self._data[index.row()]
            col = index.column()
            if col == 0:
                return res_dset.label
            elif col == 1:
                return res_dset.created
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ["Label", "Created"][section]


class ParameterTableModel(QAbstractTableModel):
    """
    Custom table model to manage parameter data from a pandas DataFrame.
    This model handles different data types for display and editing.
    """

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else pd.DataFrame()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns in the model."""
        return self._data.shape[1]

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Returns the header data for the given section."""
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return str(self._data.columns[section])
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        Returns the data for a given index and role.
        Handles displaying data from the DataFrame.
        """
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        value = self._data.iloc[row, col]
        if col == 4:
            value = f"{value:.2f}"

        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)

        if role == Qt.ItemDataRole.EditRole:
            return value

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """
        Sets the data for a given index and role.
        Handles updating the underlying DataFrame.
        """
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        row = index.row()
        col = index.column()

        if col == 1:  # Unit column
            if value not in ["ps", "ns", "µs", "us", "ms", "s"]:
                return False

        # Get the original dtype of the column
        original_dtype = self._data.dtypes.iloc[col]

        try:
            # Attempt to cast the new value to the original type
            # This helps maintain data integrity in the DataFrame (e.g., floats remain floats)
            if pd.api.types.is_numeric_dtype(original_dtype):
                value = float(value)

            self._data.iloc[row, col] = value
            self.dataChanged.emit(index, index, [role])
            return True
        except (ValueError, TypeError):
            # If conversion fails, don't update the data
            return False

    def flags(self, index):
        """
        Returns the item flags for a given index.
        This determines if an item is selectable, editable, etc.
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        # All items are selectable, enabled, and editable by default
        return (
            Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsEditable
        )


def get_human_readable_size(full_path):
    """
    Get the size of a file in a human-readable format.
    """
    size = Path(full_path).stat().st_size
    if size <= 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"  # fallback for extremely large files


class DatasetFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._type_db: dict = {}

    def update_type_db(self, type_db: dict):
        self._type_db = type_db

    def filterAcceptsRow(self, source_row, source_parent):
        """Override this method to filter out non-dataset files."""
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)

        if not index.isValid():
            return False
        full_path = model.filePath(index)
        if Path(full_path).name == CACHE_PATH:
            return False
        scan_type = self.get_scan_type(full_path)
        return scan_type != "invalid"

    def get_scan_type(self, full_path):
        return self._type_db.get(full_path) or _get_scan_type(full_path)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        # Check if the requested column is the "Type" column (column 2 in QFileSystemModel)
        if index.column() == 2 and role == Qt.DisplayRole:
            source_index = self.mapToSource(index)
            full_path = self.sourceModel().filePath(source_index)  # Get full path
            return self.get_scan_type(full_path)

        if role == Qt.DisplayRole and index.column() == 1:  # Size column
            source_index = self.mapToSource(index)
            full_path = self.sourceModel().filePath(source_index)
            try:
                return get_human_readable_size(full_path)
            except OSError:
                return 0
        return super().data(index, role)  # Default behavior
