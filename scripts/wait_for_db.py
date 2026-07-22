"""Block until the configured database accepts connections (for container boot).

Usage:  python scripts/wait_for_db.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text  # noqa: E402

from app.config import Config  # noqa: E402


def wait(max_attempts: int = 30, delay: float = 2.0) -> None:
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database is ready.")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"[{attempt}/{max_attempts}] DB not ready: {exc}")
            time.sleep(delay)
    raise SystemExit("Database did not become ready in time.")


if __name__ == "__main__":
    wait()
