import argparse
import sys
from trxasviewer import main_gui, main_modeling_gui, __version__


def create_argparser():
    """Creates and returns an argument parser for trxasviewer CLI."""
    if len(sys.argv) == 1 or sys.argv[1] not in {"view", "model"}:
        sys.argv.insert(1, "view")  # Default subcommand is 'view'

    parser = argparse.ArgumentParser(
        prog="trxasviewer",
        description="TRXAS Viewer - A GUI application for TRXAS data visualization.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- View Subcommand ---
    view_parser = subparsers.add_parser("view", help="Visualize raw TrXAS datasets")
    view_parser.add_argument(
        "--version", action="version", version=f"trxasviewer {__version__}"
    )
    view_parser.add_argument(
        "--rawfolder", "-r", type=str, help="Path to the raw data folder.", default=None
    )
    view_parser.add_argument(
        "--syncbunch", "-s", type=int, help="Sync bunch index number.", default=None
    )
    view_parser.add_argument(
        "--disable-autoload",
        "-d",
        action="store_true",
        help="Disable automatically load previous settings.",
        default=False,
    )
    view_parser.add_argument(
        "--reset-dtype-cache",
        action="store_true",
        help="Invalidate previous cache.",
        default=False,
    )
    view_parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Load preprocessed data from cache when available; save to cache after parsing.",
        default=False,
    )
    view_parser.set_defaults(func=run_view)

    # --- Model Subcommand ---
    model_parser = subparsers.add_parser("model", help="Modeling TRXAS results.")
    model_parser.set_defaults(func=run_model)  # Placeholder

    return parser


def run_view(args):
    sys.exit(
        main_gui(
            rawfolder=args.rawfolder,
            syncbunch=args.syncbunch,
            autoload=(not args.disable_autoload),
            reset_cache=args.reset_dtype_cache,
            use_cache=args.use_cache,
        )
    )


def run_model(args):
    sys.exit(main_modeling_gui(args))


def main():
    parser = create_argparser()
    args = parser.parse_args()
    args.func(args)  # Dispatch to the correct handler


if __name__ == "__main__":
    main()
