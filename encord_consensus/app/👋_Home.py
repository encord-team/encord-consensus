import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from encord_consensus.app.common.constants import (
    CHOOSE_PROJECT_PAGE_NAME,
    CHOOSE_PROJECT_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
    EXPORT_PAGE_NAME,
    EXPORT_PAGE_TITLE,
    INSPECT_FILES_PAGE_NAME,
    INSPECT_FILES_PAGE_TITLE,
)

st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
st.write("# Welcome to Encord Consensus! 👋")

container = st.container()
with container:
    choose_project_col, inspect_files_col, export_col = st.columns(3)

    if choose_project_col.button(CHOOSE_PROJECT_PAGE_TITLE, use_container_width=True):
        switch_page(CHOOSE_PROJECT_PAGE_NAME)
    if inspect_files_col.button(INSPECT_FILES_PAGE_TITLE, use_container_width=True):
        switch_page(INSPECT_FILES_PAGE_NAME)
    if export_col.button(EXPORT_PAGE_TITLE, use_container_width=True):
        switch_page(EXPORT_PAGE_NAME)


# ---------- CSS STYLES ----------
st.markdown(
    """
<style>
/* Enlarge buttons corresponding to the main pages */
div.css-ocqkz7.esravye3 button {
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
