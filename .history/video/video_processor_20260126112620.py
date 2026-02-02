import av
import cv2
import time
from streamlit_webrtc import VideoProcessorBase


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.prev_gray = None
        self.last_motion_time = time.time()
        self.bg_saved = False

        self.reference_face = None
        self.background_face = None
        self.identity_matched = True

    # ==============================
    # FACE COMPARISON
    # ==============================
    def compare_faces(self):
        if self.reference_face is None or self.background_face is None:
            return False

        ref = self.reference_face
        bg = self.background_face

        # ensure grayscale
        if len(ref.shape) == 3:
            ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        if len(bg.shape) == 3:
            bg = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)

        ref = cv2.resize(ref, (200, 200))
        bg = cv2.resize(bg, (200, 200))

        mse = ((ref.astype("float") - bg.astype("float")) ** 2).mean()
        print("Face MSE:", mse)

        return mse < 2000

    # ==============================
    # VIDEO STREAM
    # ==============================
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if not self.bg_saved:
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        self.identity_matched = self.compare_faces()

        if not self.identity_matched:
            cv2.putText(
                img,
                "🚫 FACE MISMATCH",
                (40, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
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