import streamlit as st

from encord_consensus.app.common.state import get_state, InspectFilesState
from encord_consensus.lib.project_access import get_all_dataset_hashes, list_projects


def add_project(project_hash: str):
    encord_client = get_state().encord_client
    project = encord_client.get_project(project_hash)
    datasets = get_all_dataset_hashes(project)

    if len(get_state().projects) > 0:
        has_errors = False
        # Verify that all selected projects share the same datasets
        if datasets != get_all_dataset_hashes(get_state().projects[0]):
            st.warning("Please select projects with the same attached datasets!", icon="⚠️")
            has_errors = True
        # Verify that all selected projects share the same ontology
        if project.ontology_hash != get_state().projects[0].ontology_hash:
            st.warning("Please select projects with the same ontology!", icon="⚠️")
            has_errors = True
        if has_errors:
            return

    get_state().projects.append(project)
    get_state().inspect_files_state = InspectFilesState(data_hash=None)


def remove_project(project_hash):
    project_index = next((i for i, p in enumerate(get_state().projects) if p.project_hash == project_hash), None)
    if project_index is not None:
        get_state().projects.pop(project_index)
    get_state().inspect_files_state = InspectFilesState(data_hash=None)


def search_projects():
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


def reset_project_selection_state():
    get_state().parent_project = None
    get_state().projects = []
