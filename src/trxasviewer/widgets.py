import os
from PySide6.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QCheckBox,
    QFileDialog,
)
from PySide6.QtCore import Slot, QPointF
import pyqtgraph as pg


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

        self.prefix_label = QLabel("Subdirectory")
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText(
            "Enter a prefix for the files. It will create a folder with this name."
        )
        self.prefix_edit.setText(prefix)
        self.browse_button = QPushButton("Browse...")

        # Checkboxes
        self.cb_image = QCheckBox("Save Image (.png)")
        self.cb_numpy = QCheckBox("Save NumPy (.npy)")
        self.cb_origin = QCheckBox("Save OriginLab (.txt)")
        self.cb_hdf = QCheckBox("Save HDF5 (.hdf)")
        # Set default checked states if desired
        self.cb_image.setChecked(True)
        self.cb_numpy.setChecked(True)
        self.cb_origin.setChecked(True)
        self.cb_hdf.setChecked(True)

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
        main_layout.addLayout(dir_layout)  # Add the horizontal layout
        main_layout.addLayout(prefix_layout)
        main_layout.addLayout(cb_layout)
        main_layout.addWidget(self.button_box)
        # --- Connections ---
        self.browse_button.clicked.connect(self.select_directory)
        self.button_box.accepted.connect(self.accept)  # Connect OK to accept
        self.button_box.rejected.connect(self.reject)  # Connect Cancel to reject

        # --- Initial State ---
        # Disable OK button until a directory is selected
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setEnabled(False)

    @Slot()  # Decorator indicating this is a slot
    def select_directory(self):
        """
        Opens a QFileDialog to select a directory and updates the line edit.
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Save Directory",
            os.path.expanduser("~"),  # Start in user's home directory
        )
        if directory:  # If a directory was selected (not cancelled)
            self.path_edit.setText(directory)
            # Enable the OK button now that a path is selected
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button:
                ok_button.setEnabled(True)

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
            "save_hdf": self.cb_origin.isChecked(),
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
