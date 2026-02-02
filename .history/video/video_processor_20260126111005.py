import av
import cv2
import numpy as np
import time
from streamlit_webrtc import VideoProcessorBase


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.bg_saved = False

        # 🔐 Identity
        self.reference_face = None      # uploaded face
        self.background_face = None     # face from background
        self.identity_matched = True

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def compare_faces(self):
        """Compare uploaded face with background face"""
        diff = cv2.absdiff(self.reference_face, self.background_face)
        score = np.mean(diff)
        return score < 60   # threshold (tune if needed)

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        # 🚫 Show mismatch on camera
        if self.bg_saved and not self.identity_matched:
            cv2.putText(
                img,
                "🚫 IDENTITY MISMATCH",
                (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )
            cv2.rectangle(
                img,
                (20, 20),
                (img.shape[1]-20, img.shape[0]-20),
                (0, 0, 255),
                4
            )

        return av.VideoFrame.from_ndarray(img, format="bgr24")