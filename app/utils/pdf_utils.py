"""PDF export helpers built on reportlab.

reportlab is imported lazily inside each function so the API can boot even when
the optional dependency isn't installed; only the export endpoints require it.
"""

import io

from flask import Response, jsonify


def _pdf_response(filename: str, story) -> Response:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=filename)
    doc.build(story)
    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _styled_table(headers, rows):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    data = [headers] + [[str(cell) for cell in row] for row in rows]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def table_pdf_response(filename: str, title: str, headers: list, rows: list) -> Response:
    try:
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, Spacer
    except ImportError:
        return jsonify({"error": "PDF export requires reportlab to be installed."}), 500

    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12), _styled_table(headers, rows)]
    return _pdf_response(filename, story)


def document_pdf_response(
    filename: str, title: str, sections: list, subtitle: str | None = None
) -> Response:
    """Multi-section report (used for the workspace growth report)."""
    try:
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, Spacer
    except ImportError:
        return jsonify({"error": "PDF export requires reportlab to be installed."}), 500

    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"])]
    if subtitle:
        story.append(Paragraph(subtitle, styles["Normal"]))
    story.append(Spacer(1, 16))

    for section in sections:
        story.append(Paragraph(section.get("heading", ""), styles["Heading2"]))
        if section.get("text"):
            story.append(Paragraph(section["text"], styles["Normal"]))
        table = section.get("table")
        if table and table.get("rows"):
            story.append(Spacer(1, 6))
            story.append(_styled_table(table["headers"], table["rows"]))
        story.append(Spacer(1, 16))

    return _pdf_response(filename, story)
