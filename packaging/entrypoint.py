# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""PyInstaller entry point for the trxasviewer GUI."""

import multiprocessing

from trxasviewer.cli import main


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
