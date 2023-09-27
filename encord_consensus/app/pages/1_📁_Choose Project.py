import streamlit as st

from encord_consensus.app.common.constants import (
    CHOOSE_PROJECT_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
)
from encord_consensus.app.common.css import set_page_css
from encord_consensus.app.common.state import State, get_state
from encord_consensus.lib.project_access import (
    count_label_rows,
    get_all_datasets,
    list_all_data_rows,
    list_projects,
)


def render_choose_projects_page():
    st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
    set_page_css()
    st.write(f"# {CHOOSE_PROJECT_PAGE_TITLE}")
    State.init()

    def add_project(project_hash: str, project_title):
        encord_client = get_state().encord_client
        project = encord_client.get_project(project_hash)
        datasets = get_all_datasets(encord_client, project_hash)
        if count_label_rows(encord_client, project_hash) != len(list_all_data_rows(encord_client, datasets)):
            st.warning("You must select projects where all label rows are annotated!", icon="⚠️")
            return

        if len(get_state().projects) == 0:
            st.session_state.attached_datasets = datasets
        elif datasets != st.session_state.attached_datasets:
            st.warning("You must select projects with the same attached datasets!", icon="⚠️")
            return

        # Verify that all selected projects share the same ontology
        if len(get_state().projects) > 0 and project.ontology_hash != get_state().projects[0].ontology_hash:
            st.warning("You must select projects with the same ontology!", icon="⚠️")
            return

        get_state().projects.append(project)
        st.session_state.project_title_lookup[project_hash] = project_title
        st.session_state.selected_data_hash = ()

    def remove_project(project_hash):
        project_index = next((i for i, p in enumerate(get_state().projects) if p.project_hash == project_hash), None)
        if project_index is not None:
            get_state().projects.pop(project_index)

        if len(get_state().projects) == 0:
            st.session_state.attached_datasets = []
        st.session_state.selected_data_hash = ()

    if "project_title_lookup" not in st.session_state:
        st.session_state.project_title_lookup = {}

    text_search = st.text_input("Search projects by title", value="")
    if text_search:
        matched_projects = list_projects(get_state().encord_client, text_search)
        for proj in matched_projects:
            p_hash = proj["project"].project_hash
            p_title = proj["project"].title
            emp = st.empty()
            col1, col2 = emp.columns([9, 3])
            col1.markdown(p_title, unsafe_allow_html=True)
            if not any(p_hash == p.project_hash for p in get_state().projects):
                col2.button(
                    "Add",
                    key=f"add_{p_hash}",
                    on_click=add_project,
                    args=(p_hash, p_title),
                )

    if len(get_state().projects) > 0:
        st.write("## Selected Projects")
        for proj in get_state().projects:
            proj_hash = proj.project_hash
            emp = st.empty()
            col1, col2 = emp.columns([9, 3])
            col1.markdown(st.session_state.project_title_lookup[proj_hash], unsafe_allow_html=True)
            col2.button("Remove", key=f"del_{proj_hash}", on_click=remove_project, args=(proj_hash,))


if __name__ == "__main__":
    render_choose_projects_page()
