import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av

# Simple face comparison class for login verification
class LoginVideoProcessor(VideoProcessorBase):
    def __init__(self, reference_face):
        self.frame = None
        self.reference_face = reference_face
        self.verified = None  # None → not verified yet, True/False → result

    def compare_faces(self, live_face):
        ref = self.reference_face
        bg = live_face

        # Ensure grayscale
        if len(ref.shape) == 3:
            ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        if len(bg.shape) == 3:
            bg = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)

        ref = cv2.resize(ref, (200, 200))
        bg = cv2.resize(bg, (200, 200))

        error = ((ref.astype("float") - bg.astype("float")) ** 2).mean()
        print("Face MSE:", error)
        return error < 2000

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        # If not verified yet, compare live frame with reference
        if self.verified is None:
            if self.frame is not None:
                match = self.compare_faces(self.frame)
                self.verified = match

        return av.VideoFrame.from_ndarray(img, format="bgr24")


def login_ui():
    st.sidebar.header("🔐 Child Login")

    name = st.sidebar.text_input("Child Name")
    location = st.sidebar.text_input("Location")

    uploaded = st.sidebar.file_uploader(
        "Upload Registered Photo", type=["jpg", "png", "jpeg"]
    )

    if uploaded:
        st.sidebar.image(uploaded, caption="Registered Photo")

    if st.sidebar.button("Proceed to Verify"):
        if not (name and location and uploaded):
            st.sidebar.error("Fill all details")
            st.stop()

        # Convert uploaded image to OpenCV format
        file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
        reference_face = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        st.info("📸 Please capture live image for verification")

        # Start camera
        ctx = webrtc_streamer(
            key="login_cam",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=lambda: LoginVideoProcessor(reference_face),
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True
        )

        if ctx.video_processor:
            if ctx.video_processor.verified is True:
                # ✅ Verified
                st.session_state.child_name = name
                st.session_state.location = location
                st.session_state.registered_face = reference_face
                st.session_state.logged_in = True
                st.sidebar.success("Login successful ✅")
            elif ctx.video_processor.verified is False:
                st.sidebar.error("🚫 Face mismatch! Cannot login")
                st.session_state.logged_in = False