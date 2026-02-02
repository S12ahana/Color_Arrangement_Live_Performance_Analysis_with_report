import streamlit as st
import cv2
import random
import numpy as np
import matplotlib.pyplot as plt
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from auth.login import login_ui
from video.video_processor import VideoProcessor
from utils.color_detection import detect_colors
from utils.helpers import calculate_accuracy
from reports.pdf_generator import generate_pdf


st.markdown("""
<style>

/* ===== Global Background ===== */
.stApp {
    background: radial-gradient(circle at top left, #1e1b4b, #020617);
    font-family: 'Segoe UI', sans-serif;
}

/* ===== Main Container Spacing ===== */
.block-container {
    padding: 2rem 3rem;
}

/* ===== Titles ===== */
h1, h2, h3 {
    color: #e9d5ff;
    text-shadow: 0 0 12px rgba(139,92,246,0.6);
}

/* ===== Info / Success / Warning Cards ===== */
[data-testid="stInfo"],
[data-testid="stSuccess"],
[data-testid="stWarning"],
[data-testid="stError"] {
    background: rgba(255,255,255,0.12);
    backdrop-filter: blur(14px);
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.25);
    box-shadow: 0 10px 35px rgba(0,0,0,0.45);
}

/* Color tuning */
[data-testid="stSuccess"] { color: #86efac; }
[data-testid="stInfo"] { color: #7dd3fc; }
[data-testid="stWarning"] { color: #fde68a; }
[data-testid="stError"] { color: #fecaca; }

/* ===== Buttons ===== */
.stButton button {
    background: linear-gradient(135deg, #8b5cf6, #22d3ee);
    color: black;
    font-weight: 700;
    border-radius: 18px;
    padding: 12px 26px;
    border: none;
    box-shadow: 0 0 20px rgba(139,92,246,0.8);
    transition: 0.25s ease;
}

.stButton button:hover {
    transform: translateY(-3px) scale(1.06);
    box-shadow: 0 0 35px rgba(34,211,238,0.9);
}

/* ===== Shuffle / Analyze Buttons emphasis ===== */
button:has(span:contains("Analyze")),
button:has(span:contains("Shuffle")) {
    font-size: 1.05rem;
}

/* ===== Camera Stream ===== */
video {
    border-radius: 22px;
    border: 3px solid transparent;
    background:
        linear-gradient(#020617, #020617) padding-box,
        linear-gradient(135deg, #8b5cf6, #22d3ee) border-box;
    box-shadow: 0 0 40px rgba(139,92,246,0.7);
}

/* ===== Captured Images ===== */
img {
    border-radius: 22px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.5);
}

/* ===== Section Divider ===== */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, #8b5cf6, transparent);
    margin: 2rem 0;
}

/* ===== Pie Chart Container ===== */
iframe {
    background: rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 10px;
}

/* ===== Download Button ===== */
.stDownloadButton button {
    background: linear-gradient(135deg, #22c55e, #4ade80);
    color: #022c22;
    font-weight: 700;
    border-radius: 18px;
    padding: 12px 28px;
    box-shadow: 0 0 25px rgba(74,222,128,0.8);
}

</style>
""", unsafe_allow_html=True)


# ==============================
# Session State Initialization
# ==============================
defaults = {
    "child_name": "",
    "location": "",
    "registered_face": None,
    "logged_in": False,
    "current_order": [],
    "snapshot": None,
    "bg_frame": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


COLORS = ["Red", "Blue", "Green"]
st.set_page_config("Color Puzzle", layout="wide")


# ==============================
# LOGIN
# ==============================
login_ui()

if not st.session_state.logged_in:
    st.warning("🔐 Please login from the sidebar to continue")
    st.stop()


# ==============================
# MAIN APP
# ==============================
st.title("🎨 Color Arrangement Puzzle")
st.info(f"👧 {st.session_state.child_name} | 📍 {st.session_state.location}")

# Target order
if not st.session_state.current_order:
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

st.subheader("🎯 Target Color Order")
st.success(" → ".join(st.session_state.current_order))

if st.button("🔀 Shuffle Colors"):
    st.session_state.current_order = random.sample(COLORS, len(COLORS))


# ==============================
# CAMERA
# ==============================
ctx = webrtc_streamer(
    key="cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)


# ==============================
# BACKGROUND & SNAPSHOT
# ==============================
col1, col2 = st.columns(2)

with col1:
    if st.button("📸 Save Background"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.bg_frame = ctx.video_processor.frame.copy()
            ctx.video_processor.bg_saved = True
            st.success("✅ Background saved")
        else:
            st.error("Camera not ready")

with col2:
    if st.button("📷 Capture Snapshot"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.snapshot = ctx.video_processor.frame.copy()
            st.success("✅ Snapshot captured")
        else:
            st.error("Camera not ready")

st.markdown("---")


# ==============================
# ANALYZE
# ==============================
if st.button("⚡ Analyze Snapshot (Left → Right)"):

    bg = st.session_state.bg_frame
    frame = st.session_state.snapshot

    if bg is None or frame is None:
        st.error("❌ Please save background and capture snapshot first")
        st.stop()

    # -------- FOREGROUND EXTRACTION --------
    diff = cv2.absdiff(bg, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
    mask = cv2.medianBlur(mask, 5)
    fg = cv2.bitwise_and(frame, frame, mask=mask)

    # -------- COLOR DETECTION --------
    detected = detect_colors(fg)

    sorted_colors = sorted(
        [(c, pos) for c, pos in detected.items() if pos is not None],
        key=lambda x: x[1][0]
    )

    detected_order = [c for c, _ in sorted_colors]

    # -------- ACCURACY --------
    correct, wrong, missing, accuracy = calculate_accuracy(
        detected_order, st.session_state.current_order
    )

    # ==============================
    # FINAL FRAME
    # ==============================
    st.subheader("📷 Final Frame (Correct Highlighted)")
    result_img = frame.copy()

    for i, (color, (x, y)) in enumerate(sorted_colors):
        if i < len(st.session_state.current_order) and \
           color == st.session_state.current_order[i]:

            cv2.rectangle(result_img, (x - 50, y - 50), (x + 50, y + 50), (0, 255, 0), 3)
            cv2.putText(result_img, f"{color} ✔", (x - 40, y - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    st.image(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB), use_container_width=True)

    # ==============================
    # ORDERS
    # ==============================
    st.markdown("### 🎯 Target Order")
    st.success(" → ".join(st.session_state.current_order))

    st.markdown("### 🔍 Detected Order")
    if detected_order:
        st.info(" → ".join(detected_order))
    else:
        st.warning("No colors detected")

    # ==============================
    # PIE CHART
    # ==============================
    st.subheader("📊 Result Pie Chart")
    values = [correct, wrong, missing]
    labels = ["Correct", "Wrong", "Missing"]

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie(values, autopct="%1.1f%%" if sum(values) > 0 else None, startangle=90)
    ax.legend(labels, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    ax.axis("equal")
    st.pyplot(fig)

    # ==============================
    # IDENTITY STATUS
    # ==============================
    verification_status = (
        "Matched" if ctx.video_processor and ctx.video_processor.identity_matched else "Mismatch"
    )

    # ==============================
    # PDF
    # ==============================
    data = {
        "Child Name": st.session_state.child_name,
        "Location": st.session_state.location,
        "Target Order": st.session_state.current_order,
        "Detected Order": detected_order,
        "Correct": correct,
        "Wrong": wrong,
        "Missing": missing,
        "Accuracy (%)": accuracy,
        "Identity Verification": verification_status,
    }

    # -------------------------
    # Create dynamic feedback
    # -------------------------
    if accuracy >= 90:
        feedback = "🏆 Excellent performance!"
    elif accuracy >= 70:
        feedback = "👍 Good job! Keep practicing."
    elif accuracy >= 40:
        feedback = "🙂 Fair attempt. Try again."
    else:
        feedback = "⚡ Needs improvement. Practice more."

    # -------------------------
    # Generate PDF
    # -------------------------
    values = [correct, wrong, missing]
    labels = ["Correct", "Wrong", "Missing"]

    pdf_path = generate_pdf(
        data,
        feedback,
        photo=st.session_state.snapshot,
        pie_values=values,
        pie_labels=labels
    )


    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Download PDF Report",
            f,
            file_name="color_puzzle_report.pdf",
            mime="application/pdf"
        )

    st.success("✅ Analysis Completed Successfully")
