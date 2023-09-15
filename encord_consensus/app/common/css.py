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
    
    /* Set button's color and default animations */
    div.stButton > button:first-child {
        background-color: #5658dd; /* Encord's color */
        color: #ffffff;
    }
    div.stButton p {
        font-size: 20px;
    }
    div.stButton > button:hover {
        opacity: 0.65;
        transition: opacity .2s;
        border-color: #5658dd;
    }
    div.stButton > button:focus:not(:active) {
        border-color: #8186eb;
        background-color: #5658dd; /* Encord's color */
        color: #ffffff;
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
