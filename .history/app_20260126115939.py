import streamlit as st
import cv2
import random
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from auth.login import login_ui
from video.video_processor import VideoProcessor
from utils.color_detection import detect_colors
from utils.helpers import calculate_accuracy
from reports.pdf_generator import generate_pdf

# ==============================
# SESSION STATE DEFAULTS
# ==============================
defaults = {
    "logged_in": False,
    "login_face": None,
    "bg_frame": None,
    "snapshot": None,
    "current_order": [],
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
    st.warning("🔐 Please login first")
    st.stop()

# ==============================
# CAMERA SETUP
# ==============================
ctx = webrtc_streamer(
    key="camera",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ==============================
# LOGIN FACE CAPTURE
# ==============================
st.sidebar.subheader("📸 Capture Login Face")
if st.sidebar.button("📷 Capture Face"):
    if ctx.video_processor and ctx.video_processor.frame is not None:
        frame = ctx.video_processor.frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            st.sidebar.error("❌ No face detected")
        else:
            x, y, w, h = faces[0]
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))

            st.session_state.registered_face = face
            ctx.video_processor.reference_face = face
            st.sidebar.success("✅ Login face captured")
    else:
        st.sidebar.error("Camera not ready")

# ==============================
# GAME UI
# ==============================
st.markdown("---")
st.title("🎨 Color Arrangement Puzzle")
if not st.session_state.current_order:
    st.session_state.current_order = random.sample(COLORS, len(COLORS))
st.success(" → ".join(st.session_state.current_order))

# ==============================
# SAVE BACKGROUND
# ==============================
if st.button("📸 Save Background"):
    if ctx.video_processor and ctx.video_processor.frame is not None:
        bg = ctx.video_processor.frame.copy()
        gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            st.error("❌ No face in background")
        else:
            x, y, w, h = faces[0]
            bg_face = gray[y:y+h, x:x+w]
            bg_face = cv2.resize(bg_face, (200, 200))

            ctx.video_processor.background_face = bg_face
            ctx.video_processor.bg_saved = True
            st.session_state.bg_frame = bg
            st.success("✅ Background saved")

# ==============================
# CAPTURE SNAPSHOT
# ==============================
if st.button("📷 Capture Snapshot"):
    if ctx.video_processor and ctx.video_processor.frame is not None:
        st.session_state.snapshot = ctx.video_processor.frame.copy()
        st.success("✅ Snapshot captured")

# ==============================
# ANALYZE SNAPSHOT
# ==============================
if st.button("⚡ Analyze Snapshot"):
    if not ctx.video_processor.identity_matched:
        st.error("🚫 FACE MISMATCH – Cannot analyze")
        st.stop()

    bg = st.session_state.bg_frame
    frame = st.session_state.snapshot
    if bg is None or frame is None:
        st.error("❌ Save background & snapshot first")
        st.stop()

    diff = cv2.absdiff(bg, frame)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray_diff, 40, 255, cv2.THRESH_BINARY)
    fg = cv2.bitwise_and(frame, frame, mask=mask)

    detected = detect_colors(fg)
    sorted_colors = sorted(
        [(c, pos) for c, pos in detected.items() if pos],
        key=lambda x: x[1][0]
    )
    detected_order = [c for c, _ in sorted_colors]

    correct, wrong, missing, accuracy = calculate_accuracy(
        detected_order, st.session_state.current_order
    )

    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)

    data = {
        "Target Order": st.session_state.current_order,
        "Detected Order": detected_order,
        "Accuracy": accuracy,
        "Identity": "Matched",
    }

    generate_pdf(data, "Excellent" if accuracy == 100 else "Needs Improvement")
    st.success("✅ Analysis completed")