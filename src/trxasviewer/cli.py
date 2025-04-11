import argparse
import sys
from trxasviewer import main_gui, __version__


def create_argparser():
    """Creates and returns an argument parser for trxasviewer CLI."""
    parser = argparse.ArgumentParser(
        prog="trxasviewer",
        description="TRXAS Viewer - A GUI application for TRXAS data visualization.",
    )

    # Version support
    parser.add_argument(
        "--version", action="version", version=f"trxasviewer {__version__}"
    )
    parser.add_argument(
        "--rawfolder", "-r", type=str, help="Path to the raw data folder.", default=None
    )
    parser.add_argument(
        "--syncbunch", "-s", type=int, help="Sync bunch index number.", default=None
    )
    parser.add_argument(
        "--disable-autoload",
        "-d",
        action="store_true",
        help="Disable automatically load previous settings.",
        default=False,
    )
    parser.add_argument(
        "--reset-dtype-cache",
        action="store_true",
        help="Invalidate previous cache.",
        default=False,
    )

    return parser


def main():
    """CLI entry point."""
    parser = create_argparser()
    args = parser.parse_args()  # No positional arguments needed for now

    # Run the GUI
    print(args)
    sys.exit(
        main_gui(
            rawfolder=args.rawfolder,
            syncbunch=args.syncbunch,
            autoload=(not args.disable_autoload),
            reset_cache=args.reset_dtype_cache,
        )
    )


if __name__ == "__main__":
    main()
