import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from encord_consensus.app.common.constants import (
    CHOOSE_PROJECT_PAGE_NAME,
    CHOOSE_PROJECT_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
    INSPECT_FILES_PAGE_NAME,
    INSPECT_FILES_PAGE_TITLE, WORKFLOWS_PAGE_TITLE, WORKFLOWS_PAGE_NAME,
)
from encord_consensus.app.common.css import set_page_css


def render_home_page():
    st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
    set_page_css()
    st.write("# Welcome to Encord Consensus! 👋")

    page_buttons_container = st.container()
    with page_buttons_container:
        choose_project_col, inspect_files_col, workflows_col = st.columns(3)

        if choose_project_col.button(CHOOSE_PROJECT_PAGE_TITLE, use_container_width=True):
            switch_page(CHOOSE_PROJECT_PAGE_NAME)
        if inspect_files_col.button(INSPECT_FILES_PAGE_TITLE, use_container_width=True):
            switch_page(INSPECT_FILES_PAGE_NAME)
        if workflows_col.button(WORKFLOWS_PAGE_TITLE, use_container_width=True):
            switch_page(WORKFLOWS_PAGE_NAME)
        st.write("<div class='PageButtonMarker'/>", unsafe_allow_html=True)  # Enlarge page buttons using CSS


if __name__ == "__main__":
    render_home_page()
