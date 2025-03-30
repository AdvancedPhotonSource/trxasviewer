import pyqtgraph as pg
from PySide6.QtCore import QPointF


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
