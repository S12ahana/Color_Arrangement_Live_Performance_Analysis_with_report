import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av

# ==============================
# 🌌 INNOVATIVE GLASS UI STYLE
# ==============================
st.markdown("""
<style>

/* ===== Background ===== */
.stApp {
    background: radial-gradient(circle at top, #1a1a3c, #0b0b1e);
    font-family: 'Segoe UI', sans-serif;
}

/* ===== Sidebar Glass Card ===== */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255,255,255,0.15);
    padding: 25px;
}

/* Headings */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff;
    text-shadow: 0 0 10px #8b5cf6;
}

/* Labels */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #dcdcff;
}

/* ===== Input Fields ===== */
.stTextInput input {
    background: rgba(255,255,255,0.15);
    color: white;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.3);
    padding: 12px;
}

.stTextInput input:focus {
    outline: none;
    border: 1px solid #8b5cf6;
    box-shadow: 0 0 12px #8b5cf6;
}

/* ===== Neon Buttons ===== */
.stButton button {
    background: linear-gradient(135deg, #8b5cf6, #22d3ee);
    color: black;
    border-radius: 18px;
    padding: 12px 22px;
    font-weight: 700;
    border: none;
    box-shadow: 0 0 15px rgba(139,92,246,0.8);
    transition: 0.3s ease;
}

.stButton button:hover {
    transform: translateY(-2px) scale(1.05);
    box-shadow: 0 0 30px rgba(34,211,238,0.9);
}

/* ===== Glass Info Box ===== */
.glass-box {
    background: rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 14px;
    text-align: center;
    color: white;
    margin-bottom: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}

/* Alerts */
[data-testid="stSuccess"] {
    background: rgba(34,197,94,0.15);
    color: #86efac;
    border-radius: 16px;
}

[data-testid="stError"] {
    background: rgba(239,68,68,0.15);
    color: #fecaca;
    border-radius: 16px;
}

/* ===== Camera Glow ===== */
video, img {
    border-radius: 20px;
    border: 3px solid transparent;
    background:
        linear-gradient(#000, #000) padding-box,
        linear-gradient(135deg, #8b5cf6, #22d3ee) border-box;
    box-shadow: 0 0 35px rgba(139,92,246,0.6);
}

</style>
""", unsafe_allow_html=True)

# ==============================
# 🎥 Camera Processor
# ==============================
class CameraVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None

    def recv(self, frame):
        self.frame = frame.to_ndarray(format="bgr24")
        return av.VideoFrame.from_ndarray(self.frame, format="bgr24")

# ==============================
# 🧠 Face Compare
# ==============================
def compare_faces(img1, img2):
    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    img1 = cv2.resize(img1, (200, 200))
    img2 = cv2.resize(img2, (200, 200))

    mse = ((img1.astype("float") - img2.astype("float")) ** 2).mean()
    return mse < 2000

# ==============================
# 📦 Session State
# ==============================
for key in ["child_name", "location", "logged_in"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ==============================
# 🔐 Login UI
# ==============================
def login_ui():
    st.sidebar.markdown("## 🛡️ Smart Child Login")
    st.sidebar.markdown("---")

    st.session_state.child_name = st.sidebar.text_input(
        "👶 Child Name",
        value=st.session_state.child_name
    ).strip() or "Unknown"

    st.session_state.location = st.sidebar.text_input(
        "📍 Location",
        value=st.session_state.location
    ).strip() or "Unknown"

    # Glass Preview
    st.sidebar.markdown(
        f"""
        <div class="glass-box">
            👧 <b>{st.session_state.child_name}</b><br>
            📍 <b>{st.session_state.location}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Register
    st.sidebar.subheader("📸 Register Face")
    reg_ctx = webrtc_streamer(
        key="reg",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=CameraVideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if st.sidebar.button("✨ Capture Face"):
        if reg_ctx.video_processor and reg_ctx.video_processor.frame is not None:
            st.session_state.registered_face = reg_ctx.video_processor.frame.copy()
            st.sidebar.success("Face Registered ✨")

    # Verify
    if "registered_face" in st.session_state:
        st.sidebar.subheader("🔍 Verify Face")
        live_ctx = webrtc_streamer(
            key="live",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=CameraVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        if st.sidebar.button("🚀 Verify & Login"):
            if live_ctx.video_processor and live_ctx.video_processor.frame is not None:
                if compare_faces(st.session_state.registered_face, live_ctx.video_processor.frame):
                    st.session_state.logged_in = True
                    st.sidebar.success("Login Successful 🎉")
                else:
                    st.sidebar.error("Face Not Matched 🚫")

# ==============================
# 🚀 App Start
# ==============================
login_ui()

if st.session_state.logged_in:
    st.markdown("""
    <div class="glass-box">
        <h2>🎉 Welcome!</h2>
        <p>Secure login completed successfully</p>
    </div>
    """, unsafe_allow_html=True)
