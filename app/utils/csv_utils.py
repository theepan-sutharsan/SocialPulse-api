"""CSV export helper built on the standard library (no extra dependency)."""

import csv
import io

from flask import Response


def rows_to_csv_response(filename: str, headers: list, rows: list) -> Response:
    """Stream ``headers`` + ``rows`` as a downloadable CSV attachment."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
