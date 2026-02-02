import os
import time
import cv2
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch


def generate_pdf(data, feedback, photo=None, pie_values=None, pie_labels=None):
    """
    data       -> dictionary of results
    feedback   -> string feedback
    photo      -> numpy BGR image or path
    pie_values -> list of numbers for pie chart
    pie_labels -> list of labels for pie chart
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
    # Save child photo temporarily
    # =================================================
    img_path = None
    if photo is not None:
        img_path = "output/temp_photo.jpg"
        if isinstance(photo, str):
            img_path = photo
        else:
            cv2.imwrite(img_path, photo)

    # =================================================
    # Header
    # =================================================
    title = Paragraph(
        "<b><font size=22 color='#1f4e79'>Color Puzzle Performance Report</font></b>",
        styles["Heading1"]
    )

    if img_path:
        img = Image(img_path, width=95, height=95)
    else:
        img = Spacer(95, 95)

    header_table = Table([[title, img]], colWidths=[width - 180, 120])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT")
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 35))

    # =================================================
    # Data Table
    # =================================================
    table_data = []
    for k, v in data.items():
        table_data.append([str(k), "" if v is None else str(v)])

    table = Table(table_data)

    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 2, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 35))

    # =================================================
    # ✅ IMPROVED PIE CHART (labels at bottom)
    # =================================================
    if pie_values and pie_labels:

        pie_path = "output/temp_pie.png"

        fig, ax = plt.subplots(figsize=(5, 4))  # bigger for PDF

        # ONLY percentages inside
        wedges, texts, autotexts = ax.pie(
            pie_values,
            startangle=90,
            autopct="%1.1f%%" if sum(pie_values) > 0 else None
        )

        ax.axis("equal")

        # legend at bottom
        ax.legend(
            wedges,
            pie_labels,
            loc="upper center",
            bbox_to_anchor=(0.3, -0.10),
            ncol=len(pie_labels),
            frameon=False,
            fontsize=10
        )

        # very important spacing
        plt.subplots_adjust(bottom=0.30)

        fig.savefig(pie_path, bbox_inches="tight", dpi=300)
        plt.close(fig)

        pie_img = Image(pie_path, width=4.8*inch, height=4*inch)
        pie_img.hAlign = 'CENTER'

        elements.append(pie_img)
        elements.append(Spacer(1, 30))

    # =================================================
    # Feedback
    # =================================================
    feedback_para = Paragraph(
        f"<b>Feedback:</b> {feedback}",
        styles["Heading2"]
    )

    elements.append(feedback_para)

    # =================================================
    # Border
    # =================================================
    def draw_border(canvas, doc):
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(2)
        canvas.rect(20, 20, width - 40, height - 40)

    doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)

    return path
