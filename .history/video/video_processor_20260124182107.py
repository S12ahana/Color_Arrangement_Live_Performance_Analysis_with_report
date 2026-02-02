import cv2
import time
import av
import streamlit as st
from streamlit_webrtc import VideoProcessorBase
from utils.face_verification import verify_face

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.prev_gray = None
        self.last_motion_time = time.time()
        self.bg_saved = False
        self.mismatch_count = 0

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        # ---- FACE VERIFICATION ----
        if "face_encoding" in st.session_state:
            match, status = verify_face(
                st.session_state.face_encoding, img
            )

            if not match:
                self.mismatch_count += 1
            else:
                self.mismatch_count = 0

            if self.mismatch_count > 10:
                cv2.putText(
                    img,
                    "⚠ PERSON NOT MATCHED",
                    (40, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3
                )

        return av.VideoFrame.from_ndarray(img, format="bgr24")