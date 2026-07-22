"""Drop and recreate all tables. Destructive — dev use only.

Usage:  python scripts/reset_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset complete.")
