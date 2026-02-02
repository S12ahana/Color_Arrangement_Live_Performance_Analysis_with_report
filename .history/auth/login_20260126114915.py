import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from video.video_processor import VideoProcessor

def login_ui():
    st.sidebar.header("🔐 Child Login (Camera-based)")

    # -----------------------------
    # Name & Location
    # -----------------------------
    name = st.sidebar.text_input("Child Name")
    location = st.sidebar.text_input("Location")

    # -----------------------------
    # Start camera for face capture
    # -----------------------------
    ctx = webrtc_streamer(
        key="login_camera",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=VideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
    )

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

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

                # ✅ Save to session state
                st.session_state.registered_face = face
                ctx.video_processor.reference_face = face
                st.sidebar.success("✅ Face captured successfully")
        else:
            st.sidebar.error("Camera not ready")

    # -----------------------------
    # Login Button
    # -----------------------------
    if st.sidebar.button("Login"):
        if not name or not location or "registered_face" not in st.session_state:
            st.sidebar.error("Please fill all details and capture face")
        else:
            st.session_state.child_name = name
            st.session_state.location = location
            st.session_state.logged_in = True
            st.sidebar.success(f"Login successful ✅ Welcome {name}")