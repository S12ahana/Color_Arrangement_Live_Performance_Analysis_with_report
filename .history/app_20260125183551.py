import streamlit as st
import cv2
import random
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from auth.login import login_ui
from video.video_processor import VideoProcessor
from utils.color_detection import detect_colors
from utils.helpers import calculate_accuracy
from reports.pdf_generator import generate_pdf


# ==============================
# Session State Initialization
# ==============================
if "child_name" not in st.session_state:
    st.session_state.child_name = ""

if "location" not in st.session_state:
    st.session_state.location = ""

if "registered_face" not in st.session_state:
    st.session_state.registered_face = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_order" not in st.session_state:
    st.session_state.current_order = []

if "snapshot" not in st.session_state:
    st.session_state.snapshot = None


COLORS = ["Red", "Blue", "Green"]

st.set_page_config("Color Puzzle", layout="wide")


# ==============================
# LOGIN
# ==============================
login_ui()

# 🔴 IMPORTANT: block app until login
if not st.session_state.logged_in:
    st.warning("🔐 Please login from the sidebar to continue")
    st.stop()


# ==============================
# MAIN APP (runs ONLY after login)
# ==============================
st.title("🎨 Color Arrangement Puzzle")

st.info(
    f"👧 {st.session_state.child_name} | 📍 {st.session_state.location}"
)

# Initialize puzzle order
if not st.session_state.current_order:
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

st.write("🎯 Target Order:", st.session_state.current_order)

if st.button("🔀 Shuffle Colors"):
    st.session_state.current_order = random.sample(COLORS, len(COLORS))


# ==============================
# CAMERA
# ==============================
ctx = webrtc_streamer(
    key="cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False}
)
col1, col2 = st.columns(2)

with col1:
    if st.button("📸 Save Background"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.bg_frame = ctx.video_processor.frame
            ctx.video_processor.bg_saved = True
            st.success("Background saved")

with col2:
    if st.button("📷 Capture Snapshot"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.snapshot = ctx.video_processor.frame
            st.success("Snapshot captured")


# ==============================
# CAPTURE


# ==============================
# ANALYZE
# ==============================
if st.button("⚡ Analyze"):
    frame = st.session_state.snapshot

    if frame is None:
        st.error("❌ Please capture an image first")
    else:
        detected = detect_colors(frame)

        order = [
            c for c, _ in sorted(detected.items(), key=lambda x: x[1][0])
        ]

        correct, wrong, missing, accuracy = calculate_accuracy(
            order, st.session_state.current_order
        )

        verification_status = (
            "Matched"
            if ctx.video_processor and ctx.video_processor.mismatch_count == 0
            else "Mismatch"
        )

        st.subheader("📊 Results")
        st.write("Detected Order:", order)
        st.write("Accuracy:", accuracy, "%")
        st.write("Identity Verification:", verification_status)

        data = {
            "Child Name": st.session_state.child_name,
            "Location": st.session_state.location,
            "Target Order": st.session_state.current_order,
            "Detected Order": order,
            "Accuracy (%)": accuracy,
            "Identity Verification": verification_status,
        }

        pdf = generate_pdf(
            data,
            "Excellent" if accuracy > 70 else "Needs Improvement"
        )

        with open(pdf, "rb") as f:
            st.download_button("📄 Download Report", f)