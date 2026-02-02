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
    Compare reference face and background face using MSE
    (Both must be grayscale)
    """
    if self.reference_face is None or self.background_face is None:
        return False

    # 🔥 ENSURE BOTH ARE GRAYSCALE
    if len(self.reference_face.shape) == 3:
        ref = cv2.cvtColor(self.reference_face, cv2.COLOR_BGR2GRAY)
    else:
        ref = self.reference_face

    if len(self.background_face.shape) == 3:
        bg = cv2.cvtColor(self.background_face, cv2.COLOR_BGR2GRAY)
    else:
        bg = self.background_face

    # Resize
    ref = cv2.resize(ref, (200, 200))
    bg = cv2.resize(bg, (200, 200))

    # Mean Squared Error
    error = ((ref.astype("float") - bg.astype("float")) ** 2).mean()

    print("Face MSE:", error)  # 👈 debug value

    return error < 2000   # threshold (tune if needed)
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