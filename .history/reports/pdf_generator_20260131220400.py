import time
import os
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def generate_pdf(data, feedback):

    os.makedirs("output", exist_ok=True)
    path = f"output/Report_{int(time.time())}.pdf"

    doc = SimpleDocTemplate(path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    # ==========================
    # TITLE
    # ==========================
    title = Paragraph(
        "🎨 <b>Color Puzzle Performance Report</b>",
        styles["Heading1"]
    )
    elements.append(title)
    elements.append(Spacer(1, 25))

    # ==========================
    # TABLE DATA
    # ==========================
    table_data = []

    for k, v in data.items():
        table_data.append([str(k), str(v)])

    table = Table(table_data, colWidths=[200, 300])

    table.setStyle(TableStyle([

        # Border
        ("BOX", (0, 0), (-1, -1), 2, colors.black),

        # Grid
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),

        # Header column style
        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.black),

        # Alignment
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # Padding
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

        # Font
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))

    # ==========================
    # FEEDBACK SECTION
    # ==========================
    feedback_para = Paragraph(
        f"<b>Feedback:</b> {feedback}",
        styles["Heading3"]
    )
    elements.append(feedback_para)

    # ==========================
    # PAGE BORDER FUNCTION
    # ==========================
    def draw_border(canvas, doc):
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(3)
        canvas.rect(20, 20, A4[0] - 40, A4[1] - 40)

    doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)

    return path
