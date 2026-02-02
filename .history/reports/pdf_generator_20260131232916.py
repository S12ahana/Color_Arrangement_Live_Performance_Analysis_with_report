import time
import os
import cv2
import matplotlib.pyplot as plt

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def generate_pdf(data, feedback, photo=None, pie_values=None, pie_labels=None):
    """
    photo -> numpy frame (BGR) OR image path
    pie_values -> list of numbers for pie chart
    pie_labels -> list of labels for pie chart
    """

    os.makedirs("output", exist_ok=True)
    path = f"output/Report_{int(time.time())}.pdf"

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    width, height = A4

    # =================================================
    # SAVE PHOTO TEMPORARILY (if numpy frame)
    # =================================================
    img_path = None

    if photo is not None:
        img_path = "output/temp_photo.jpg"
        if isinstance(photo, str):
            img_path = photo
        else:
            cv2.imwrite(img_path, photo)

    # =================================================
    # HEADER (Title + Photo)
    # =================================================
    title = Paragraph(
        "<b><font size=20>🎨 Color Puzzle Performance Report</font></b>",
        styles["Heading1"]
    )

    if img_path:
        img = Image(img_path, width=90, height=90)
    else:
        img = Spacer(90, 90)

    header_table = Table(
        [[title, img]],
        colWidths=[width - 160, 120]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT")
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 30))

    # =================================================
    # DATA TABLE
    # =================================================
    table_data = []
    for k, v in data.items():
        table_data.append([str(k), str(v)])

    table = Table(table_data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 2, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.7, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 25))

    # =================================================
    # PIE CHART
    # =================================================
    if pie_values and pie_labels:
        # Save pie chart as temporary image
        pie_path = "output/temp_pie.png"
        fig, ax = plt.subplots(figsize=(3.5, 3.5))
        ax.pie(
            pie_values,
            labels=pie_labels,
            autopct="%1.1f%%" if sum(pie_values) > 0 else None,
            startangle=90
        )
        ax.axis("equal")
        plt.tight_layout()
        fig.savefig(pie_path, bbox_inches="tight")
        plt.close(fig)

        pie_img = Image(pie_path, width=200, height=200)
        elements.append(pie_img)
        elements.append(Spacer(1, 25))

    # =================================================
    # FEEDBACK
    # =================================================
    feedback_para = Paragraph(
        f"<b>Feedback:</b> {feedback}",
        styles["Heading3"]
    )
    elements.append(feedback_para)

    # =================================================
    # BORDER
    # =================================================
    def draw_border(canvas, doc):
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(3)
        canvas.rect(20, 20, width - 40, height - 40)

    doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)

    return path
