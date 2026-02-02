import time
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf(data, feedback):
    os.makedirs("output", exist_ok=True)
    path = f"output/Report_{int(time.time())}.pdf"

    pdf = canvas.Canvas(path, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(300, 800, "Color Puzzle Report")

    y = 750
    pdf.setFont("Helvetica", 12)
    for k, v in data.items():
        pdf.drawString(50, y, f"{k}: {v}")
        y -= 20

    pdf.drawString(50, 120, f"Feedback: {feedback}")
    pdf.save()
    return path