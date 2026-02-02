import streamlit as st
import cv2
import random
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from auth.login import login_ui
from video.video_processor import VideoProcessor
from utils.color_detection import detect_colors
from utils.helpers import calculate_accuracy
from reports.pdf_generator import generate_pdf

import streamlit as st

# ---- Session State Initialization ----
if "child_name" not in st.session_state:
    st.session_state.child_name = None

if "location" not in st.session_state:
    st.session_state.location = None

if "registered_face" not in st.session_state:
    st.session_state.registered_face = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

COLORS = ["Red", "Blue", "Green"]

st.set_page_config("Color Puzzle", layout="wide")

# ---- LOGIN ----
login_ui()

st.title("🎨 Color Arrangement Puzzle")

if "current_order" not in st.session_state:
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

st.info(
    f"👧 {st.session_state.child_name} | 📍 {st.session_state.location}"
)

if st.button("🔀 Shuffle Colors"):
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

if st.session_state.logged_in:
    st.success(
        f"👧 {st.session_state.child_name} | 📍 {st.session_state.location}"
    )
else:
    st.warning("Please login first")

ctx = webrtc_streamer(
    key="cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False}
)

if st.button("📸 Capture"):
    if ctx.video_processor:
        st.session_state.snapshot = ctx.video_processor.frame
        st.success("Snapshot saved")

if st.button("⚡ Analyze"):
    frame = st.session_state.get("snapshot")
    if frame is None:
        st.error("Capture first")
    else:
        detected = detect_colors(frame)
        order = [c for c, _ in sorted(detected.items(), key=lambda x: x[1][0])]

        correct, wrong, missing, accuracy = calculate_accuracy(
            order, st.session_state.current_order
        )

        verification_status = (
            "Matched" if ctx.video_processor.mismatch_count == 0 else "Mismatch"
        )

        data = {
            "Child Name": st.session_state.child_name,
            "Location": st.session_state.location,
            "Target Order": st.session_state.current_order,
            "Detected Order": order,
            "Accuracy (%)": accuracy,
            "Identity Verification": verification_status
        }

        pdf = generate_pdf(data, "Excellent" if accuracy > 70 else "Improve")
        with open(pdf, "rb") as f:
            st.download_button("📄 Download Report", f)