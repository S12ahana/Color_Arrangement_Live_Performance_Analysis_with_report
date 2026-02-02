import streamlit as st
import face_recognition

def login_ui():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.face_encoding = None

    if st.session_state.authenticated:
        return

    st.title("🔐 Kid Authentication")

    name = st.text_input("Child Name")
    location = st.text_input("Playing Location")
    photo = st.file_uploader("Upload Kid Photo", type=["jpg", "png"])

    if st.button("Login"):
        if not name or not location or not photo:
            st.error("All fields required")
            return

        image = face_recognition.load_image_file(photo)
        enc = face_recognition.face_encodings(image)

        if len(enc) == 0:
            st.error("No face detected")
            return

        st.session_state.child_name = name
        st.session_state.location = location
        st.session_state.face_encoding = enc[0]
        st.session_state.authenticated = True
        st.success("Login successful")
        st.rerun()

    st.stop()