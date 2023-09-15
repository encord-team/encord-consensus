import streamlit as st


def set_page_css():
    st.markdown(
        """
    <style>
    /* Enlarge buttons that redirect to app's pages (put the marker `PageButtonMarker` inside button's container) */
    div[data-testid="stVerticalBlock"] > div:has(div.PageButtonMarker) button {
        height: auto;
        padding-top: 20px;
        padding-bottom: 20px;
    }

    /* Set the minimum and maximum width for the sidebar */
    [data-testid="stSidebar"][aria-expanded="true"]{
        min-width: 5%;
        max-width: 15%;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
