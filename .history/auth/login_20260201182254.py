import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av

# ==============================
# 🌈 PAGE STYLE (CSS)
# ==============================
st.markdown("""
<style>
/* App Background */
.stApp {
    background: linear-gradient(135deg, #667eea, #764ba2);
    font-family: 'Segoe UI', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1e2f, #2a2a40);
    padding: 20px;
}

/* Sidebar Headers */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff;
}

/* Sidebar Text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #e0e0ff;
}

/* Text Inputs */
.stTextInput input {
    background-color: #ffffff;
    border-radius: 10px;
    padding: 10px;
    border: 2px solid #764ba2;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-radius: 12px;
    padding: 10px 18px;
    font-weight: 600;
    border: none;
    transition: 0.3s ease;
}

.stButton button:hover {
    transform: scale(1.05);
    background: linear-gradient(135deg, #764ba2, #667eea);
}

/* Alerts */
[data-testid="stSuccess"] {
    background-color: #e6fffa;
    color: #065f46;
    border-radius: 12px;
}

[data-testid="stError"] {
    background-color: #fee2e2;
    color: #7f1d1d;
    border-radius: 12px;
}

[data-testid="stWarning"] {
    background-color: #fff7ed;
    color: #7c2d12;
    border-radius: 12px;
}

/* Camera & Images */
video, img {
    border-radius: 16px;
    border: 3px solid #764ba2;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# ==============================
# 🎥 Video Processor
# ==============================
class CameraVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None

    def recv(self, frame):
        self.frame = frame.to_ndarray(format="bgr24")
        return av.VideoFrame.from_ndarray(self.frame, format="bgr24")

# ==============================
# 🧠 Face Comparison
# ==============================
def compare_faces(img1, img2):
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    if len(img2.shape) == 3:
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    img1 = cv2.resize(img1, (200, 200))
    img2 = cv2.resize(img2, (200, 200))

    error = ((img1.astype("float") - img2.astype("float")) ** 2).mean()
    return error < 2000

# ==============================
# 📦 Session State
# ==============================
if "child_name" not in st.session_state:
    st.session_state.child_name = ""
if "location" not in st.session_state:
    st.session_state.location = ""
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==============================
# 🔐 Login UI
# ==============================
def login_ui():
    st.sidebar.markdown("## 👶 Child Secure Login")
    st.sidebar.markdown("---")

    # Inputs
    st.session_state.child_name = st.sidebar.text_input(
        "Child Name",
        value=st.session_state.child_name
    ).strip() or "Unknown"

    st.session_state.location = st.sidebar.text_input(
        "Location",
        value=st.session_state.location
    ).strip() or "Unknown"

    # Preview Box
    st.sidebar.markdown(
        f"""
        <div style="
            background:#2d2d44;
            padding:12px;
            border-radius:12px;
            color:white;
            text-align:center;
            margin-bottom:15px;
        ">
            👧 <b>{st.session_state.child_name}</b><br>
            📍 <b>{st.session_state.location}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Step 1
    st.sidebar.subheader("📸 Step 1: Register Face")
    st.sidebar.info("Look at the camera and capture")

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
            st.sidebar.success("✅ Registered successfully")
        else:
            st.sidebar.warning("⌛ Camera not ready")

    # Step 2
    if "registered_face" in st.session_state:
        st.sidebar.subheader("🔍 Step 2: Verify Face")
        st.sidebar.info("Look at the camera and verify")

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
                    st.sidebar.success("🎉 Face Verified! Login Successful")
                else:
                    st.sidebar.error("🚫 Face mismatch")
            else:
                st.sidebar.warning("⌛ Camera not ready")

# ==============================
# 🚀 Main App
# ==============================
login_ui()

if st.session_state.logged_in:
    st.markdown("## 🎉 Welcome!")
    st.success(f"Hello **{st.session_state.child_name}** from **{st.session_state.location}** 👋")
