import streamlit as st
import cv2
import numpy as np

def login_ui():
    st.sidebar.header("🔐 Child Login")

    name = st.sidebar.text_input("Child Name")
    location = st.sidebar.text_input("Location")

    uploaded = st.sidebar.file_uploader(
        "Upload Child Photo", type=["jpg", "png", "jpeg"]
    )

    if uploaded:
        st.sidebar.image(uploaded, caption="Registered Photo")

    if st.sidebar.button("Login"):
        if not (name and location and uploaded):
            st.sidebar.error("Fill all details")
            st.stop()

        file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        st.session_state.child_name = name
st.session_state.location = location
st.session_state.registered_face = img
st.session_state.logged_in = True

st.sidebar.success("Login successful")