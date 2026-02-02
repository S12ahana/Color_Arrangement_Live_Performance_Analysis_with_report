# ==============================
# PDF GENERATOR (reports/pdf_generator.py)
# ==============================
import os
import time
import cv2
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def generate_pdf(data, feedback, photo=None, pie_chart_path=None):
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

    # --- Header (title + photo) ---
    title = Paragraph("<b><font size=22 color='#1f4e79'>🎨 Color Puzzle Performance Report</font></b>", styles["Heading1"])
    if photo is not None:
        cv2.imwrite("output/temp_photo.jpg", photo)
        img = Image("output/temp_photo.jpg", width=95, height=95)
    else:
        img = Spacer(95, 95)

    header_table = Table([[title, img]], colWidths=[400, 120])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT")
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 25))

    # --- Data Table ---
    table_data = [[str(k), str(v)] for k, v in data.items()]
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 2, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 25))

    # --- Pie Chart ---
    if pie_chart_path is not None:
        pie_img = Image(pie_chart_path, width=3*inch, height=3*inch)
        pie_img.hAlign = 'CENTER'
        elements.append(pie_img)
        elements.append(Spacer(1, 25))

    # --- Feedback ---
    feedback_para = Paragraph(f"<b>Feedback:</b> {feedback}", styles["Heading2"])
    elements.append(feedback_para)

    # --- Page Border ---
    def draw_border(canvas, doc):
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(2)
        canvas.rect(20, 20, width - 40, height - 40)

    doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)
    return path
