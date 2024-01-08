import streamlit as st

from encord_consensus.app.common.constants import (
    CHOOSE_PROJECT_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
)
from encord_consensus.app.common.css import set_page_css
from encord_consensus.app.common.project_selection import add_project, remove_project
from encord_consensus.app.common.state import State, get_state
from encord_consensus.lib.project_access import (
    list_projects,
)


def render_choose_projects_page():
    st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
    set_page_css()
    st.write(f"# {CHOOSE_PROJECT_PAGE_TITLE}")
    State.init()

    text_search = st.text_input("Search projects by title", value="")
    if text_search:
        matched_projects = list_projects(get_state().encord_client, text_search)
        for proj in matched_projects:
            proj_hash = proj["project"].project_hash
            emp = st.empty()
            col1, col2 = emp.columns([9, 3])
            col1.markdown(proj["project"].title, unsafe_allow_html=True)
            if not any(proj_hash == p.project_hash for p in get_state().projects):
                col2.button("Add", key=f"add_{proj_hash}", on_click=add_project, args=(proj_hash,))

    if len(get_state().projects) > 0:
        st.write("## Selected Projects")
        for proj in get_state().projects:
            proj_hash = proj.project_hash
            emp = st.empty()
            col1, col2 = emp.columns([9, 3])
            col1.markdown(proj.title, unsafe_allow_html=True)
            col2.button("Remove", key=f"del_{proj_hash}", on_click=remove_project, args=(proj_hash,))


if __name__ == "__main__":
    render_choose_projects_page()
