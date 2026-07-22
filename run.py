"""Application entrypoint.

Creates the Flask app via the factory, enables CORS, and ensures the
database schema exists (``db.create_all()``) on boot.
"""

from app import create_app
from app.extensions import db

app = create_app()


@app.shell_context_processor
def _shell_context():
    """Expose db + models in ``flask shell`` for convenience."""
    from app import models

    return {"db": db, **{name: getattr(models, name) for name in models.__all__}}


if __name__ == "__main__":
    app.run(
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5000),
        debug=app.config.get("FLASK_DEBUG", True),
    )
