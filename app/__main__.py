from __future__ import annotations

import sys

from app.env import load_dotenv
from app.flow import run_cli


def main() -> None:
    load_dotenv()
    demo = len(sys.argv) > 1 and sys.argv[1] == "--demo"
    run_cli(demo=demo)


if __name__ == "__main__":
    main()
