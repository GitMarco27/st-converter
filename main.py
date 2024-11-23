import streamlit as st

from src import render_home_page, render_image_converter


# Main app code
def main():
    st.set_page_config(layout="wide")

    # Add CSS for centered text
    st.markdown(
        """
        <style>
        [data-testid="stImage"] img {
            border-radius: 15px;
        }
        .centered-text {
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("File Conversion Tools")
    st.sidebar.image("./resources/images/artwork.jpeg")
    st.sidebar.markdown(
        '<p class="centered-text">Marco Sanguineti, 2024</p>', unsafe_allow_html=True
    )

    pg = st.navigation(
        [
            st.Page(render_home_page, title="Homepage", icon="🏡"),
            st.Page(render_image_converter, title="Image Converter", icon="🏞️"),
        ],
        expanded=True,
        position="sidebar",
    )
    pg.run()


if __name__ == "__main__":
    main()
