import av
import cv2
from streamlit_webrtc import VideoProcessorBase


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None

        # identity related
        self.reference_face = None
        self.background_face = None
        self.identity_matched = True

    def compare_faces(self):
        """
        Simple face comparison using MSE
        """
        if self.reference_face is None or self.background_face is None:
            return False

        ref = cv2.resize(self.reference_face, (200, 200))
        bg = cv2.resize(self.background_face, (200, 200))

        error = ((ref.astype("float") - bg.astype("float")) ** 2).mean()
        return error < 2000   # threshold (tunable)

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        # 🔴 SHOW WARNING ONLY
        if not self.identity_matched:
            cv2.putText(
                img,
                "🚫 IDENTITY MISMATCH",
                (40, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )
            cv2.rectangle(
                img,
                (10, 10),
                (img.shape[1] - 10, img.shape[0] - 10),
                (0, 0, 255),
                4
            )

        return av.VideoFrame.from_ndarray(img, format="bgr24")