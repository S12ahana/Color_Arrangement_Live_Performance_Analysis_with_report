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


st.markdown(""" <style> /* ===== Global Background ===== */ .stApp { background: linear-gradient(135deg, #fdf2f8, #ecfeff, #f0fdf4); font-family: 'Segoe UI', sans-serif; } /* ===== Main Container ===== */ .block-container { padding: 2rem 3rem; } /* ===== Titles ===== */ h1 { color: #7c3aed; text-shadow: 2px 2px 0px #fde68a; } h2 { color: #2563eb; } h3 { color: #059669; } /* ===== Info / Success / Warning / Error Cards ===== */ [data-testid="stInfo"], [data-testid="stSuccess"], [data-testid="stWarning"], [data-testid="stError"] { border-radius: 20px; padding: 1rem; font-weight: 600; box-shadow: 0 10px 25px rgba(0,0,0,0.15); } /* Individual colors */ [data-testid="stInfo"] { background: linear-gradient(135deg, #dbeafe, #e0f2fe); color: #1e40af; } [data-testid="stSuccess"] { background: linear-gradient(135deg, #dcfce7, #bbf7d0); color: #065f46; } [data-testid="stWarning"] { background: linear-gradient(135deg, #fef3c7, #fde68a); color: #92400e; } [data-testid="stError"] { background: linear-gradient(135deg, #fee2e2, #fecaca); color: #7f1d1d; } /* ===== Buttons ===== */ .stButton button { background: linear-gradient(135deg, #f472b6, #818cf8); color: white; font-weight: 700; border-radius: 20px; padding: 12px 26px; border: none; transition: all 0.3s ease; box-shadow: 0 8px 20px rgba(129,140,248,0.5); } .stButton button:hover { transform: translateY(-4px) scale(1.08); background: linear-gradient(135deg, #fb7185, #60a5fa); box-shadow: 0 12px 28px rgba(96,165,250,0.6); } /* ===== Special Buttons (Shuffle / Analyze) ===== */ button:has(span:contains("Shuffle")) { background: linear-gradient(135deg, #34d399, #22c55e) !important; } button:has(span:contains("Analyze")) { background: linear-gradient(135deg, #fb7185, #f59e0b) !important; } /* ===== Camera Stream ===== */ video { border-radius: 25px; border: 4px solid #a855f7; box-shadow: 0 15px 30px rgba(168,85,247,0.4); } /* ===== Captured Images ===== */ img { border-radius: 25px; border: 4px solid #38bdf8; box-shadow: 0 15px 30px rgba(56,189,248,0.4); } /* ===== Section Divider ===== */ hr { border: none; height: 3px; background: linear-gradient(90deg, #f472b6, #818cf8, #34d399); margin: 2.5rem 0; } /* ===== Pie Chart Card ===== */ iframe { background: linear-gradient(135deg, #ffffff, #f0f9ff); border-radius: 25px; padding: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); } /* ===== Download Button ===== */ .stDownloadButton button { background: linear-gradient(135deg, #22c55e, #4ade80); color: #064e3b; font-weight: 800; border-radius: 22px; padding: 14px 30px; box-shadow: 0 12px 30px rgba(34,197,94,0.5); } .stDownloadButton button:hover { background: linear-gradient(135deg, #16a34a, #22c55e); transform: scale(1.07); } </style> """, unsafe_allow_html=True)


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



login_ui()

if not st.session_state.logged_in:
    st.warning("🔐 Please login from the sidebar to continue")
    st.stop()


st.title("🎨 Color Arrangement Puzzle")
st.info(f"👧 {st.session_state.child_name} | 📍 {st.session_state.location}")

if not st.session_state.current_order:
    st.session_state.current_order = random.sample(COLORS, len(COLORS))

st.subheader("🎯 Target Color Order")
st.success(" → ".join(st.session_state.current_order))

if st.button("🔀 Shuffle Colors"):
    st.session_state.current_order = random.sample(COLORS, len(COLORS))


ctx = webrtc_streamer(
    key="cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)



col1, col2 = st.columns(2)

with col1:
    if st.button("📸 Save Background"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.bg_frame = ctx.video_processor.frame.copy()
            ctx.video_processor.bg_saved = True
            st.success("✅ Background saved")

with col2:
    if st.button("📷 Capture Snapshot"):
        if ctx.video_processor and ctx.video_processor.frame is not None:
            st.session_state.snapshot = ctx.video_processor.frame.copy()
            st.success("✅ Snapshot captured")

st.markdown("---")



if st.button("⚡ Analyze Snapshot "):

    bg = st.session_state.bg_frame
    frame = st.session_state.snapshot

    if bg is None or frame is None:
        st.error(" Please save background and capture snapshot first")
        st.stop()

    diff = cv2.absdiff(bg, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
    mask = cv2.medianBlur(mask, 5)
    fg = cv2.bitwise_and(frame, frame, mask=mask)

    detected = detect_colors(fg)

    sorted_colors = sorted(
        [(c, pos) for c, pos in detected.items() if pos is not None],
        key=lambda x: x[1][0]
    )

    detected_order = [c for c, _ in sorted_colors]

    correct, wrong, missing, accuracy = calculate_accuracy(
        detected_order, st.session_state.current_order
    )

    st.subheader("📷 Final Frame ")
    result_img = frame.copy()

    for i, (color, (x, y)) in enumerate(sorted_colors):
        if i < len(st.session_state.current_order) and color == st.session_state.current_order[i]:
            cv2.rectangle(result_img, (x-50, y-50), (x+50, y+50), (0,255,0), 3)
            cv2.putText(result_img, f"{color} ✔", (x-40, y-60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    st.image(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB), use_container_width=True)

    st.markdown("### 🎯 Target Order")
    st.success(" → ".join(st.session_state.current_order))

    st.markdown("### 🔍 Detected Order")
    st.info(" → ".join(detected_order) if detected_order else "No colors detected")

 
    st.subheader("📊 Result Pie Chart")

    values = [correct, wrong, missing]
    labels = ["Correct", "Wrong", "Missing"]
    pie_colors = ["#22c55e", "#ef4444", "#f59e0b"]

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie(
        values,
        colors=pie_colors,
        autopct="%1.1f%%" if sum(values) > 0 else None,
        startangle=90
    )
    ax.legend(labels, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    ax.axis("equal")
    st.pyplot(fig)

    verification_status = (
        "Matched" if ctx.video_processor and ctx.video_processor.identity_matched else "Mismatch"
    )

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

    feedback = (
        "🏆 Excellent performance!" if accuracy >= 90 else
        "👍 Good job! Keep practicing." if accuracy >= 70 else
        "🙂 Fair attempt. Try again." if accuracy >= 40 else
        "⚡ Needs improvement. Practice more."
    )

    pdf_path = generate_pdf(
        data,
        feedback,
        photo=st.session_state.registered_face,
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
