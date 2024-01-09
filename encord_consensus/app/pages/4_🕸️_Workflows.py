import json
from pathlib import Path
from typing import Dict

import streamlit as st
from encord import Project

from encord_consensus.app.common.constants import (
    WORKFLOWS_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
)
from encord_consensus.app.common.css import set_page_css
from encord_consensus.app.common.project_selection import add_project
from encord_consensus.app.common.state import State, get_state
from encord_consensus.lib.project_access import list_projects
from encord_consensus.lib.utils import get_project_root
from encord_consensus.lib.workflow_utils import send_to_annotate


def render_workflows_page():
    st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
    set_page_css()
    st.write(f"# {WORKFLOWS_PAGE_TITLE}")
    State.init()
    user_client = get_state().encord_client

    root_dir = get_project_root()
    config_path = root_dir.joinpath(Path('.workflow_configs.json'))

    with open(config_path, 'r') as f:
        wf_config = json.load(f)

    def sync(workflow_name: str, workflow: Dict):
        with st.spinner(f'Syncing {workflow_name}...'):
            synced_counter = send_to_annotate(**{'user_client': user_client, **workflow['spec']})
        st.text(f'Executed {workflow_name}, synced: {synced_counter} items')

    def delete_workflow(workflow_name: str):
        del wf_config[workflow_name]
        with open(config_path, 'w') as f:
            json.dump(wf_config, f)

    def select_parent_project(project: Project):
        get_state().parent_project = project

    def deselect_parent_project():
        get_state().parent_project = None

    def get_target_projects():
        return [p for p in get_state().projects if p != get_state().parent_project]

    def toggle_visibility():
        get_state().show_element = not get_state().show_element

    def add_workflow(new_workflow_name: str, stage_filter: str):
        meta = {}
        source_project = get_state().parent_project
        meta['source_project_name'] = source_project.title

        new_target_project_names = []
        meta['target_project_names'] = [p.title for p in get_target_projects()]
        wf_config[new_workflow_name] = {
            "spec": {
                "source_project_hash": source_project.project_hash,
                "target_project_hashes": [p.project_hash for p in get_target_projects()],
                "stage_filter": stage_filter,
                "target_priority": 1
            },
            "meta": {
                "source_project_name": "source project",
                "target_project_names": new_target_project_names
            }
        }
        with open(config_path, 'w') as f:
            json.dump(wf_config, f)

    def reset_creation_flow():
        get_state().parent_project = None
        get_state().projects = []

    def render_workflow_add():
        new_workflow_name = st.text_input('New Workflow Name')
        stage_filter = st.text_input('Stage Filter (must match exactly with stage in app)')
        st.text('Selected Projects')
        for proj in get_state().projects:
            emp = st.empty()
            col1, col2 = emp.columns([9, 3])
            col1.markdown(proj.title, unsafe_allow_html=True)
            if not get_state().parent_project:
                col2.button("Select Source", key=f"select_{proj.project_hash}", on_click=select_parent_project,
                            args=(proj,))
            elif proj == get_state().parent_project:
                col2.button("Deselect Source", key=f"select_{proj.project_hash}", on_click=deselect_parent_project)

        if get_state().parent_project:
            st.subheader('Workflow Preview')
            st.text('Source Project:')
            st.text(f'--{get_state().parent_project.title}')
            st.text('Target Projects:')
            for target_project in get_target_projects():
                st.text(f'--{target_project.title}')

            if st.button("Create"):
                add_workflow(new_workflow_name, stage_filter)
                reset_creation_flow()
                toggle_visibility()
                st.experimental_rerun()

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

    for wf_name, wf in wf_config.items():
        emp = st.empty()
        col1, col2, col3 = emp.columns([5, 2, 2])
        with col1:
            with st.expander(wf_name):
                st.text(f'Stage Filter: {wf["spec"]["stage_filter"]}')
                st.text('Source Project:')
                st.text(f'--{wf["meta"]["source_project_name"]}')
                st.text('Target Projects:')
                for target_project_name in wf["meta"]["target_project_names"]:
                    st.text(f'--{target_project_name}')
        col2.button("Sync 🔄", key=f"sync_{wf_name}", on_click=sync, args=(wf_name, wf,), type="primary")
        col3.button("Delete ❌", key=f"delete_{wf_name}", on_click=delete_workflow, args=(wf_name,))

    st.title('New Workflow')

    if not get_state().show_element:
        st.button('➕', on_click=toggle_visibility)
    if get_state().show_element:
        render_workflow_add()


if __name__ == "__main__":
    render_workflows_page()
