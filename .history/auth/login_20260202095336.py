import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av

# -----------------------
# Video Processor (captures live frames)
# -----------------------
class CameraVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None

    def recv(self, frame):
        self.frame = frame.to_ndarray(format="bgr24")
        return av.VideoFrame.from_ndarray(self.frame, format="bgr24")


# -----------------------
# Face comparison function
# -----------------------
def compare_faces(img1, img2):
    # Convert to grayscale
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    if len(img2.shape) == 3:
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Resize
    img1 = cv2.resize(img1, (200, 200))
    img2 = cv2.resize(img2, (200, 200))

    error = ((img1.astype("float") - img2.astype("float")) ** 2).mean()
    return error < 2000  # threshold


# ==============================
# Initialize session state
# ==============================
if "child_name" not in st.session_state:
    st.session_state.child_name = ""
if "location" not in st.session_state:
    st.session_state.location = ""  # Initialize as empty

# ==============================
# Login UI
# ==============================
def login_ui():
    st.sidebar.header("🔐 Child Login")

    # Child Name input
    child_name_input = st.sidebar.text_input(
        "Child Name",
        value=st.session_state.child_name
    ).strip()
    st.session_state.child_name = child_name_input if child_name_input else " "

    # Location input
    location_input = st.sidebar.text_input(
        "Location",
        value=st.session_state.location
    ).strip()
    st.session_state.location = location_input if location_input else "Unknown"

    st.sidebar.markdown(f"**Preview:** 👧 {st.session_state.child_name} | 📍 {st.session_state.location}")




    # Step 1: Capture Registered Photo
    st.sidebar.subheader("Step 1: Capture Registered Photo")
    st.sidebar.info("📸 Look at the camera and click 'Capture Registered Photo'")

    reg_ctx = webrtc_streamer(
        key="registered_cam",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=CameraVideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if st.sidebar.button("Capture Registered Photo"):
        if reg_ctx.video_processor and reg_ctx.video_processor.frame is not None:
            st.session_state.registered_face = reg_ctx.video_processor.frame.copy()
            st.sidebar.image(
                cv2.cvtColor(st.session_state.registered_face, cv2.COLOR_BGR2RGB),
                caption="Registered Photo"
            )
            st.sidebar.success("✅ Registered photo captured")
        else:
            st.sidebar.warning("⌛ Camera not ready. Please wait...")

    # Step 2: Capture Live Verification Photo
    if "registered_face" in st.session_state and st.session_state.registered_face is not None:
        st.sidebar.subheader("Step 2: Capture Live Verification Photo")
        st.sidebar.info("📸 Look at the camera and click 'Verify Face'")

        live_ctx = webrtc_streamer(
            key="live_cam",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=CameraVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        if st.sidebar.button("Verify Face"):
            if live_ctx.video_processor and live_ctx.video_processor.frame is not None:
                live_face = live_ctx.video_processor.frame.copy()
                if compare_faces(st.session_state.registered_face, live_face):
                    st.session_state.logged_in = True

    # Make sure session_state values are updated
                    

                    st.sidebar.success("✅ Face Verified! Login successful")

                else:
                    st.sidebar.error("🚫 Face mismatch! Cannot login")
            else:
                st.sidebar.warning("⌛ Camera not ready. Please wait...")
