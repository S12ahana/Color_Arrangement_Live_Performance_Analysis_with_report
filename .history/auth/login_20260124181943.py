import streamlit as st
import cv2
import os
import time
import random
import numpy as np
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av
from utils.color_detection import detect_colors

COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Violet"]
os.makedirs("output", exist_ok=True)

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.prev_gray = None
        self.last_motion_time = time.time()
        self.bg_saved = False 

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        
        if not self.bg_saved:
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        if self.prev_gray is None:
            self.prev_gray = gray
            return av.VideoFrame.from_ndarray(img, format="bgr24")

       
        diff = cv2.absdiff(self.prev_gray, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        motion_pixels = cv2.countNonZero(thresh)

        if motion_pixels > 2000:
            self.last_motion_time = time.time()

      
        wait_time = time.time() - self.last_motion_time

        if wait_time > 3:
            cv2.putText(img, "⚠️ PLACE THE COLOR!", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255), 3)
            cv2.rectangle(img, (10, 10), (img.shape[1]-10, img.shape[0]-10),
                          (0, 0, 255), 4)

        self.prev_gray = gray
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ---------------- PDF ----------------
def generate_pdf_report(data, pie_chart_path, feedback_text):
    report_path = f"output/Color_Report_{int(time.time())}.pdf"
    pdf = pdf_canvas.Canvas(report_path, pagesize=A4)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(300, 800, "Color Challenge Report")

    y = 760
    pdf.setFont("Helvetica", 12)
    for k, v in data.items():
        pdf.drawString(50, y, f"{k}: {v}")
        y -= 18

    if os.path.exists(pie_chart_path):
        pdf.drawImage(ImageReader(pie_chart_path), 100, y - 260, width=350, height=250)

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, 100, "Feedback:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 80, feedback_text)

    pdf.save()
    return report_path


st.set_page_config(page_title="Color Puzzle", layout="wide")
st.title("🎨 Color Arrangement Puzzle")

if "current_order" not in st.session_state:
    st.session_state.current_order = COLORS.copy()

if st.button("🔀 Shuffle Colors"):
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

st.subheader("Target Color Order")
st.write(", ".join(st.session_state.current_order))

webrtc_ctx = webrtc_streamer(
    key="live",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

col1, col2 = st.columns(2)

with col1:
    if st.button("📸 Save Background"):
        if webrtc_ctx.video_processor:
            f = webrtc_ctx.video_processor.frame
            if f is not None:
                st.session_state.bg_frame = f
                webrtc_ctx.video_processor.bg_saved = True 
                st.success("✅ Background saved. Motion tracking enabled.")

with col2:
    if st.button("📷 Capture Snapshot"):
        if webrtc_ctx.video_processor:
            f = webrtc_ctx.video_processor.frame
            if f is not None:
                st.session_state.last_frame = f
                cv2.imwrite("output/snapshot.jpg", f)
                st.success("✅ Snapshot captured")

st.markdown("---")


if st.button("⚡ Analyze Snapshot (Left → Right)"):

    bg = st.session_state.get("bg_frame")
    frame = st.session_state.get("last_frame")

    if bg is None or frame is None:
        st.error("❌ Save background and snapshot first.")
    else:
      
        diff = cv2.absdiff(bg, frame)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
        mask = cv2.medianBlur(mask, 5)
        fg = cv2.bitwise_and(frame, frame, mask=mask)

        detected_positions = detect_colors(fg)

        sorted_colors = sorted(
            [(c, pos) for c, pos in detected_positions.items() if pos],
            key=lambda x: x[1][0]
        )

        detected_order = [c for c, _ in sorted_colors]

        st.subheader("Detected Order (Left → Right)")
        st.write(", ".join(detected_order))

        target_count = len(st.session_state.current_order)
        placed_count = len(detected_order)

        correct = 0
        for i in range(min(placed_count, target_count)):
            if detected_order[i] == st.session_state.current_order[i]:
                correct += 1

        wrong = placed_count - correct
        missing = max(0, target_count - placed_count)
        accuracy = round((correct / target_count) * 100, 2) if target_count > 0 else 0

        result_img = frame.copy()
        for i, (color, pos) in enumerate(sorted_colors):
            x, y = pos
            if i < target_count and color == st.session_state.current_order[i]:
                cv2.rectangle(result_img, (x-50, y-50), (x+50, y+50), (0, 255, 0), 3)
                cv2.putText(result_img, color, (x-40, y-60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        
        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("Final Frame (Correct Highlighted)")
            st.image(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB), use_container_width=True)

        with right_col:
            st.subheader("Result Pie Chart")
            fig, ax = plt.subplots()
            ax.pie([correct, wrong, missing],
                   labels=["Correct", "Wrong", "Missing"],
                   autopct="%1.1f%%")
            pie_path = "output/pie.png"
            plt.savefig(pie_path)
            st.pyplot(fig)

        
        st.subheader("Report Summary")
        st.write("Target Order:", ", ".join(st.session_state.current_order))
        st.write("Detected Order:", ", ".join(detected_order))
        st.write("Placed Colors:", placed_count)
        st.write("Correct:", correct)
        st.write("Wrong:", wrong)
        st.write("Missing:", missing)
        st.write("Accuracy (%):", accuracy)

        result_data = {
            "Target Order": ", ".join(st.session_state.current_order),
            "Detected Order": ", ".join(detected_order),
            "Total Target Colors": target_count,
            "Placed Colors": placed_count,
            "Correct": correct,
            "Wrong": wrong,
            "Missing": missing,
            "Accuracy (%)": accuracy
        }

        feedback = "🏆 Excellent!" if accuracy >= 90 else "🎯 Good Job!" if accuracy >= 70 else "⚡ Improve"
        pdf_path = generate_pdf_report(result_data, pie_path, feedback)

        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download PDF Report", f, file_name=os.path.basename(pdf_path))

        st.success("✅ Analysis Completed")
