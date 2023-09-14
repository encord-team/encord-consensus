import streamlit as st

from encord_consensus.app.common.constants import (
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
    EXPORT_PAGE_TITLE,
)

st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
st.write(f"# {EXPORT_PAGE_TITLE}")


# ---------- CSS STYLES ----------
st.markdown(
    """
<style>
/* Set the minimum and maximum width for the sidebar */
[data-testid="stSidebar"][aria-expanded="true"]{
    min-width: 5%;
    max-width: 15%;
}
</style>
""",
    unsafe_allow_html=True,
)
