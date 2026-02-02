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
# Session State
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
# FACE UPLOAD (REFERENCE FACE)
# ==============================
st.sidebar.subheader("📸 Upload Child Photo")
uploaded = st.sidebar.file_uploader("Upload face image", type=["jpg", "png", "jpeg"])

if uploaded:
    img = np.frombuffer(uploaded.read(), np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        st.sidebar.error("❌ No face detected")
    else:
        x, y, w, h = faces[0]
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (200, 200))
        st.session_state.registered_face = face
        st.sidebar.success("✅ Face registered")


# ==============================
# MAIN UI
# ==============================
st.title("🎨 Color Arrangement Puzzle")
st.info(f"👧 {st.session_state.child_name} | 📍 {st.session_state.location}")

if not st.session_state.current_order:
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

st.subheader("🎯 Target Order")
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

# Pass reference face to processor
if ctx.video_processor:
    ctx.video_processor.reference_face = st.session_state.registered_face


# ==============================
# BACKGROUND SAVE
# ==============================
if st.button("📸 Save Background"):
    if ctx.video_processor and ctx.video_processor.frame is not None:
        st.session_state.bg_frame = ctx.video_processor.frame.copy()

        # extract face from background
        gray = cv2.cvtColor(st.session_state.bg_frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            st.error("❌ No face in background")
        else:
            x, y, w, h = faces[0]
            bg_face = gray[y:y+h, x:x+w]
            bg_face = cv2.resize(bg_face, (200, 200))

            ctx.video_processor.background_face = bg_face
            ctx.video_processor.bg_saved = True

            st.success("✅ Background & face saved")


# ==============================
# SNAPSHOT
# ==============================
if st.button("📷 Capture Snapshot"):
    if ctx.video_processor and ctx.video_processor.frame is not None:
        st.session_state.snapshot = ctx.video_processor.frame.copy()
        st.success("✅ Snapshot captured")


# ==============================
# ANALYSIS
# ==============================
if st.button("⚡ Analyze Snapshot"):

    if not ctx.video_processor.identity_matched:
        st.error("🚫 FACE MISMATCH – Access Denied")
        st.stop()

    bg = st.session_state.bg_frame
    frame = st.session_state.snapshot

    if bg is None or frame is None:
        st.error("❌ Save background & snapshot first")
        st.stop()

    diff = cv2.absdiff(bg, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
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

    verification_status = "Matched" if ctx.video_processor.identity_matched else "Mismatch"

    data = {
        "Child Name": st.session_state.child_name,
        "Target Order": st.session_state.current_order,
        "Detected Order": detected_order,
        "Accuracy": accuracy,
        "Identity": verification_status,
    }

    pdf = generate_pdf(data, "Excellent" if accuracy == 100 else "Needs Improvement")
    with open(pdf, "rb") as f:
        st.download_button("📄 Download Report", f, "report.pdf")

    st.success("✅ Completed")