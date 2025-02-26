import argparse
import sys
from trxasviewer import main_gui, __version__

def create_argparser():
    """Creates and returns an argument parser for trxasviewer CLI."""
    parser = argparse.ArgumentParser(
        prog="trxasviewer",
        description="TRXAS Viewer - A GUI application for TRXAS data visualization."
    )
    
    # Version support
    parser.add_argument("--version", action="version",
                        version=f"trxasviewer {__version__}")
    parser.add_argument("--rawfolder", "-r", type=str, 
                        help="Path to the raw data folder.", default=None)
    
    return parser


def main():
    """CLI entry point."""
    parser = create_argparser()
    args = parser.parse_args()  # No positional arguments needed for now

    # Run the GUI
    sys.exit(main_gui(args.rawfolder))


if __name__ == "__main__":
    main()
