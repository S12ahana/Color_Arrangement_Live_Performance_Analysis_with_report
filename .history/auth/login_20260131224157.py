import time
import os
import cv2

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


# =================================================
# PDF GENERATOR (Styled + Photo + Robust Layout)
# =================================================
def generate_pdf(data, feedback, photo=None):
    """
    data  -> dictionary of results
    photo -> numpy frame (BGR) OR image path
    """

    os.makedirs("output", exist_ok=True)
    path = f"output/Report_{int(time.time())}.pdf"

    width, height = A4

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    # =================================================
    # SAVE PHOTO TEMPORARILY
    # =================================================
    img_path = None

    if photo is not None:
        img_path = "output/temp_photo.jpg"

        if isinstance(photo, str):
            img_path = photo
        else:
            cv2.imwrite(img_path, photo)

    # =================================================
    # HEADER (TITLE + PHOTO RIGHT)
    # =================================================
    title = Paragraph(
        "<b><font size=22 color='#1f4e79'>🎨 Color Puzzle Performance Report</font></b>",
        styles["Heading1"]
    )

    if img_path:
        img = Image(img_path, width=95, height=95)
    else:
        img = Spacer(95, 95)

    header_table = Table(
        [[title, img]],
        colWidths=[width - 180, 120]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT")
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 35))

    # =================================================
    # DATA TABLE (AUTO WIDTH — FIXES LOCATION ISSUE)
    # =================================================
    table_data = []

    for k, v in data.items():
        # safe conversion
        value = "" if v is None else str(v)
        table_data.append([str(k), value])

    # Auto fit width (IMPORTANT)
    table = Table(table_data)

    table.setStyle(TableStyle([

        # Border
        ("BOX", (0, 0), (-1, -1), 2, colors.black),

        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # First column style
        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.black),

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

    # =================================================
    # FEEDBACK SECTION
    # =================================================
    feedback_para = Paragraph(
        f"<b>Feedback:</b> {feedback}",
        styles["Heading2"]
    )

    elements.append(feedback_para)

    # =================================================
    # PAGE BORDER
    # =================================================
    def draw_border(canvas, doc):
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(2)
        canvas.rect(20, 20, width - 40, height - 40)

    doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)

    return path
