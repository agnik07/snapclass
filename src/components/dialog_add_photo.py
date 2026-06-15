import streamlit as st
from PIL import Image

import time


@st.dialog("Capture or Upload Photos")
def add_photos_dialog():

    st.write('Add classroom photos to scan for attendance')

    # Initialize session state
    if 'photo_tab' not in st.session_state:
        st.session_state.photo_tab = 'camera'

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    t1, t2 = st.columns(2)

    with t1:
        type_camera = (
            "primary"
            if st.session_state.photo_tab == 'camera'
            else 'secondary'
        )

        if st.button(
            'Camera',
            type=type_camera,
            use_container_width=True
        ):
            st.session_state.photo_tab = 'camera'

    with t2:
        type_upload = (
            "primary"
            if st.session_state.photo_tab == 'upload'
            else 'secondary'
        )

        if st.button(
            'Upload Photos',
            type=type_upload,
            use_container_width=True
        ):
            st.session_state.photo_tab = 'upload'

    # Camera Section
    if st.session_state.photo_tab == 'camera':

        cam_photo = st.camera_input(
            'Take Snapshot',
            key='dialog_cam'
        )

        if cam_photo:

            st.session_state.attendance_images.append(
                Image.open(cam_photo)
            )

            st.toast('Photo Captured Successfully')

            st.rerun()

    # Upload Section
    elif st.session_state.photo_tab == 'upload':

        uploaded_files = st.file_uploader(
            'Choose image files',
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            key='dialog_upload'
        )

        if uploaded_files:

            for f in uploaded_files:

                st.session_state.attendance_images.append(
                    Image.open(f)
                )

            st.toast('Photos Uploaded Successfully')

            st.rerun()

    st.divider()

    if st.button(
        'Done',
        type='primary',
        use_container_width=True
    ):
        st.rerun()