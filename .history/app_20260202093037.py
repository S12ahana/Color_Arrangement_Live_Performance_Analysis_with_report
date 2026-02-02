import streamlit as st
import cv2
import random
import numpy as np
import matplotlib.pyplot as plt
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from auth.login import login_ui
from video.video_processor import VideoProcessor
from utils.color_detection import detect_colors
from utils.helpers import calculate_accuracy
from reports.pdf_generator import generate_pdf


st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fdf2f8, #ecfeff, #f0fdf4);
    font-family: 'Segoe UI', sans-serif;
}
.block-container { padding: 2rem 3rem; }
h1 { color: #7c3aed; text-shadow: 2px 2px 0px #fde68a; }
h2 { color: #2563eb; }
h3 { color: #059669; }
</style>
""", unsafe_allow_html=True)


# ==============================
# Session State Initialization
# ==============================
defaults = {
    "child_name": "",
    "location": "",
    "registered_face": None,
    "logged_in": False,
    "current_order": [],
    "snapshot": None,
    "bg_frame": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


COLORS = ["Red", "Blue", "Green"]
st.set_page_config("Color Puzzle", layout="wide")


# ==============================
# LOGIN
# ==============================
login_ui()

if not st.session_state.logged_in:
    st.warning("🔐 Please login from the sidebar to continue")
    st.stop()


# ==============================
# MAIN APP
# ==============================
st.title("🎨 Color Arrangement Puzzle")
st.info(f"👧 {st.session_state.child_name} | 📍 {st.session_state.location}")

if not st.session_state.current_order:
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

st.subheader("🎯 Target Color Order")
st.success(" → ".join(st.session_state.current_order))

if st.button("🔀 Shuffle Colors"):
    st.session_state.current_order = random.sample(COLORS, len(COLORS))


# ==============================
# CAMERA
# ==============================
ctx = webrtc_streamer(
    key="cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)


# ==============================
# BACKGROUND & SNAPSHOT
# ==============================
col1, col2 = st.columns(2)

with col1:
    if st.button("📸 Save Background"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.bg_frame = ctx.video_processor.frame.copy()
            ctx.video_processor.bg_saved = True
            st.success("✅ Background saved")

with col2:
    if st.button("📷 Capture Snapshot"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.snapshot = ctx.video_processor.frame.copy()
            st.success("✅ Snapshot captured")

st.markdown("---")


# ==============================
# ANALYZE
# ==============================
if st.button("⚡ Analyze Snapshot (Left → Right)"):

    bg = st.session_state.bg_frame
    frame = st.session_state.snapshot

    if bg is None or frame is None:
        st.error("❌ Please save background and capture snapshot first")
        st.stop()

    diff = cv2.absdiff(bg, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
    mask = cv2.medianBlur(mask, 5)
    fg = cv2.bitwise_and(frame, frame, mask=mask)

    detected = detect_colors(fg)

    sorted_colors = sorted(
        [(c, pos) for c, pos in detected.items() if pos is not None],
        key=lambda x: x[1][0]
    )

    detected_order = [c for c, _ in sorted_colors]

    correct, wrong, missing, accuracy = calculate_accuracy(
        detected_order, st.session_state.current_order
    )

    st.subheader("📷 Final Frame (Correct Highlighted)")
    result_img = frame.copy()

    for i, (color, (x, y)) in enumerate(sorted_colors):
        if i < len(st.session_state.current_order) and color == st.session_state.current_order[i]:
            cv2.rectangle(result_img, (x-50, y-50), (x+50, y+50), (0,255,0), 3)
            cv2.putText(result_img, f"{color} ✔", (x-40, y-60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    st.image(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB), use_container_width=True)

    st.markdown("### 🎯 Target Order")
    st.success(" → ".join(st.session_state.current_order))

    st.markdown("### 🔍 Detected Order")
    st.info(" → ".join(detected_order) if detected_order else "No colors detected")

    # ==============================
    # PIE CHART (COLORED)
    # ==============================
    st.subheader("📊 Result Pie Chart")

    values = [correct, wrong, missing]
    labels = ["Correct", "Wrong", "Missing"]
    pie_colors = ["#22c55e", "#ef4444", "#f59e0b"]

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie(
        values,
        colors=pie_colors,
        autopct="%1.1f%%" if sum(values) > 0 else None,
        startangle=90
    )
    ax.legend(labels, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    ax.axis("equal")
    st.pyplot(fig)

    verification_status = (
        "Matched" if ctx.video_processor and ctx.video_processor.identity_matched else "Mismatch"
    )

    data = {
        "Child Name": st.session_state.child_name,
        "Location": st.session_state.location,
        "Target Order": st.session_state.current_order,
        "Detected Order": detected_order,
        "Correct": correct,
        "Wrong": wrong,
        "Missing": missing,
        "Accuracy (%)": accuracy,
        "Identity Verification": verification_status,
    }

    feedback = (
        "🏆 Excellent performance!" if accuracy >= 90 else
        "👍 Good job! Keep practicing." if accuracy >= 70 else
        "🙂 Fair attempt. Try again." if accuracy >= 40 else
        "⚡ Needs improvement. Practice more."
    )

    pdf_path = generate_pdf(
        data,
        feedback,
        photo=st.session_state.registered_face,
        pie_values=values,
        pie_labels=labels
    )

    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Download PDF Report",
            f,
            file_name="color_puzzle_report.pdf",
            mime="application/pdf"
        )

    st.success("✅ Analysis Completed Successfully")
