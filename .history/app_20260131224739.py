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

# Target order
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
        else:
            st.error("Camera not ready")

with col2:
    if st.button("📷 Capture Snapshot"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.snapshot = ctx.video_processor.frame.copy()
            st.success("✅ Snapshot captured")
        else:
            st.error("Camera not ready")

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

    # -------- FOREGROUND EXTRACTION --------
    diff = cv2.absdiff(bg, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
    mask = cv2.medianBlur(mask, 5)
    fg = cv2.bitwise_and(frame, frame, mask=mask)

    # -------- COLOR DETECTION --------
    detected = detect_colors(fg)

    sorted_colors = sorted(
        [(c, pos) for c, pos in detected.items() if pos is not None],
        key=lambda x: x[1][0]
    )

    detected_order = [c for c, _ in sorted_colors]

    # -------- ACCURACY --------
    correct, wrong, missing, accuracy = calculate_accuracy(
        detected_order, st.session_state.current_order
    )

    # ==============================
    # FINAL FRAME
    # ==============================
    st.subheader("📷 Final Frame (Correct Highlighted)")
    result_img = frame.copy()

    for i, (color, (x, y)) in enumerate(sorted_colors):
        if i < len(st.session_state.current_order) and \
           color == st.session_state.current_order[i]:

            cv2.rectangle(
                result_img,
                (x - 50, y - 50),
                (x + 50, y + 50),
                (0, 255, 0),
                3
            )

            cv2.putText(
                result_img,
                f"{color} ✔",
                (x - 40, y - 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    st.image(
        cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB),
        use_container_width=True
    )

    # ==============================
    # ORDERS
    # ==============================
    st.markdown("### 🎯 Target Order")
    st.success(" → ".join(st.session_state.current_order))

    st.markdown("### 🔍 Detected Order")
    if detected_order:
        st.info(" → ".join(detected_order))
    else:
        st.warning("No colors detected")

    # ==============================
    # PIE CHART
    # ==============================
    st.subheader("📊 Result Pie Chart")

    values = [correct, wrong, missing]
    labels = ["Correct", "Wrong", "Missing"]

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie(
        values,
        autopct="%1.1f%%" if sum(values) > 0 else None,
        startangle=90
    )
    ax.legend(labels, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    ax.axis("equal")
    st.pyplot(fig)

    # ==============================
    # IDENTITY STATUS
    # ==============================
    verification_status = (
        "Matched"
        if ctx.video_processor and ctx.video_processor.identity_matched
        else "Mismatch"
    )

    # ==============================
    # PDF
    # ==============================
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

    

    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Download PDF Report",
            f,
            file_name="color_puzzle_report.pdf",
            mime="application/pdf"
        )

    st.success("✅ Analysis Completed Successfully")