import streamlit as st

from encord_consensus.app.common.constants import (
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
    EXPORT_PAGE_TITLE,
)
from encord_consensus.app.common.css import set_page_css

st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
set_page_css()
st.write(f"# {EXPORT_PAGE_TITLE}")

)
