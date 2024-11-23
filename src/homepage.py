import streamlit as st


def render_home_page():
    st.title("🤖 File Conversion Tools")
    st.markdown(
        """
    Convert your files easily and quickly! ✨

    ### Why?
    - I needed a quick way to convert files to different formats
    - I needed to convert images from HEIC to PNG/JPEG/WebP
    - I was totally tired of the existing online converters, full of ads and tracking


    ### 🛠️ Available Tools
    - 🖼️ **Image Converter**
        - PNG, JPEG, WebP, HEIC
        - Batch conversion supported

    ### 🚀 How to Use
    1. Pick a tool from the sidebar
    2. Drop your files
    3. Choose output format
    4. Download!

    That's it! 🎉
    """
    )
