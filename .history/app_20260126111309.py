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
# SESSION STATE
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

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


COLORS = ["Red", "Blue", "Green"]
st.set_page_config("Color Puzzle", layout="wide")


# ==============================
# LOGIN
# ==============================
login_ui()

if not st.session_state.logged_in:
    st.warning("🔐 Please login to continue")
    st.stop()


# ==============================
# MAIN UI
# ==============================
st.title("🎨 Color Arrangement Puzzle")
st.info(f"👧 {st.session_state.child_name} | 📍 {st.session_state.location}")

if not st.session_state.current_order:
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

st.success(" → ".join(st.session_state.current_order))


# ==============================
# CAMERA
# ==============================
ctx = webrtc_streamer(
    key="camera",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)


# ==============================
# SAVE BACKGROUND & VERIFY FACE
# ==============================
if st.button("📸 Save Background & Verify Identity"):

    if ctx.video_processor and ctx.video_processor.frame is not None:

        frame = ctx.video_processor.frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            st.error("❌ No face detected")

        elif st.session_state.registered_face is None:
            st.error("❌ No reference face found from login")

        else:
            x, y, w, h = faces[0]
            bg_face = gray[y:y+h, x:x+w]
            bg_face = cv2.resize(bg_face, (200, 200))

            vp = ctx.video_processor
            vp.background_face = bg_face
            vp.reference_face = st.session_state.registered_face

            vp.identity_matched = vp.compare_faces()

            if vp.identity_matched:
                st.success("✅ Identity Verified")
            else:
                st.error("🚫 Identity Mismatch")

    else:
        st.error("Camera not ready")


# ==============================
# SNAPSHOT
# ==============================
if st.button("📷 Capture Snapshot"):
    if ctx.video_processor:
        st.session_state.snapshot = ctx.video_processor.frame.copy()
        st.success("Snapshot captured")


# ==============================
# ANALYSIS
# ==============================
if st.button("⚡ Analyze Snapshot"):

    frame = st.session_state.snapshot
    if frame is None:
        st.error("Capture snapshot first")
        st.stop()

    detected = detect_colors(frame)
    detected_order = [c for c in detected if detected[c] is not None]

    correct, wrong, missing, accuracy = calculate_accuracy(
        detected_order, st.session_state.current_order
    )

    st.success(f"Accuracy: {accuracy}%")


# ==============================
# PDF STATUS
# ==============================
verification_status = (
    "Matched" if ctx.video_processor and ctx.video_processor.identity_matched
    else "Mismatch"
)