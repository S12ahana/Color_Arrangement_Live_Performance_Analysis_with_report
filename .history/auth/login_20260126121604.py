import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av

# -----------------------
# Video Processor (captures live frames)
# -----------------------
class LoginVideoProcessor(VideoProcessorBase):
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


# -----------------------
# Login UI
# -----------------------
def login_ui():
    st.sidebar.header("🔐 Child Login")

    name = st.sidebar.text_input("Child Name")
    location = st.sidebar.text_input("Location")
    uploaded = st.sidebar.file_uploader(
        "Upload Registered Photo", type=["jpg", "png", "jpeg"]
    )

    if uploaded:
        st.sidebar.image(uploaded, caption="Registered Photo")
        # Convert uploaded image to OpenCV format
        file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
        registered_face = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        st.sidebar.info("📸 Start camera and click 'Verify Face' when ready")

        # Start camera
        ctx = webrtc_streamer(
            key="login_cam",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=LoginVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        # Button to verify
        if st.sidebar.button("Verify Face"):
            if ctx.video_processor and ctx.video_processor.frame is not None:
                live_face = ctx.video_processor.frame
                if compare_faces(registered_face, live_face):
                    st.session_state.child_name = name
                    st.session_state.location = location
                    st.session_state.registered_face = registered_face
                    st.session_state.logged_in = True
                    st.sidebar.success("✅ Face Verified! Login successful")
                else:
                    st.sidebar.error("🚫 Face mismatch! Cannot login")
            else:
                st.sidebar.warning("⌛ Camera not ready. Please wait...")
