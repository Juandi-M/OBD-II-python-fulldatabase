#!/usr/bin/env python3
"""OBD-II Scanner CLI entrypoint."""

import argparse

from app.flow import run_cli


def main() -> None:
    parser = argparse.ArgumentParser(description="OBD-II Scanner")
    parser.add_argument("--demo", action="store_true", help="Run without hardware")
    parser.parse_args()
    run_cli()


if __name__ == "__main__":
    main()
