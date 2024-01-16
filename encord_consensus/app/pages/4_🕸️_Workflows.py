import json
from typing import Dict

import streamlit as st
from encord import Project

from encord_consensus.app.common.constants import (
    WORKFLOWS_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
)
from encord_consensus.app.common.css import set_page_css
from encord_consensus.app.common.project_selection import search_projects, reset_project_selection_state
from encord_consensus.app.common.state import State, get_state
from encord_consensus.lib.workflow_utils import pre_populate, WorkflowType, WORKFLOW_CONFIG_PATH, read_workflow_config


def render_workflows_page():
    st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
    set_page_css()
    st.write(f"# {WORKFLOWS_PAGE_TITLE}")
    State.init()
    user_client = get_state().encord_client

    if not WORKFLOW_CONFIG_PATH.exists():
        with open(WORKFLOW_CONFIG_PATH, 'w') as f:
            json.dump({}, f)
    wf_config = read_workflow_config()

    def sync(workflow_name: str, workflow: Dict):
        with st.spinner(f'Syncing {workflow_name}...'):
            synced_counter = pre_populate(**{'user_client': user_client, **workflow['spec']})
        st.text(f'Executed {workflow_name}, synced: {synced_counter} items')

    def delete_workflow(workflow_name: str):
        del wf_config[workflow_name]
        with open(WORKFLOW_CONFIG_PATH, 'w') as f:
            json.dump(wf_config, f)

    def select_reference_project(project: Project):
        get_state().reference_project = project

    def deselect_reference_project():
        get_state().reference_project = None

    def get_non_reference_projects():
        return [p for p in get_state().projects if p != get_state().reference_project]

    def toggle_visibility():
        get_state().show_element = not get_state().show_element

    def toggle_creation_flow():
        reset_project_selection_state()
        toggle_visibility()

    def add_workflow(new_workflow_name: str, workflow_type: WorkflowType, stage_filter: str):
        meta = {}
        reference_project = get_state().reference_project
        meta['reference_project_name'] = reference_project.title
        meta['non_reference_project_names'] = [p.title for p in get_non_reference_projects()]
        wf_config[new_workflow_name] = {
            "workflow_type": workflow_type.value,
            "spec": {
                "source_project_hash": reference_project.project_hash,
                "target_project_hashes": [p.project_hash for p in get_non_reference_projects()],
                "stage_filter": stage_filter,
                "target_priority": 1 if workflow_type == WorkflowType.PRE_POPULATE else None
            },
            "meta": meta
        }
        with open(WORKFLOW_CONFIG_PATH, 'w') as f:
            json.dump(wf_config, f)

    def render_workflow_add():
        new_workflow_name = st.text_input('New Workflow Name')
        workflow_type = st.radio('Workflow Type', [t.value for t in WorkflowType])
        if workflow_type == WorkflowType.PRE_POPULATE.value:
            stage_filter = st.text_input('Stage Filter (must match exactly with stage in app)')
        else:
            stage_filter = None
        st.text('Selected Projects')
        reference_name = "Source" if workflow_type == WorkflowType.PRE_POPULATE.value else "Target"
        non_reference_name = "Target" if workflow_type == WorkflowType.PRE_POPULATE.value else "Source"
        for proj in get_state().projects:
            emp = st.empty()
            col1, col2 = emp.columns([9, 3])
            col1.markdown(proj.title, unsafe_allow_html=True)
            if not get_state().reference_project:
                col2.button(
                    f"Select {reference_name}",
                    key=f"select_{proj.project_hash}",
                    on_click=select_reference_project,
                    args=(proj,)
                )
            elif proj == get_state().reference_project:
                col2.button(
                    f"Deselect {reference_name}",
                    key=f"select_{proj.project_hash}",
                    on_click=deselect_reference_project
                )

        if get_state().reference_project:
            st.subheader('Workflow Preview')
            st.text(f'{reference_name} Project:')
            st.text(f'--{get_state().reference_project.title}')
            st.text(f'{non_reference_name} Projects:')
            for target_project in get_non_reference_projects():
                st.text(f'--{target_project.title}')

            if st.button("Create"):
                add_workflow(new_workflow_name, WorkflowType(workflow_type), stage_filter)
                reset_project_selection_state()
                toggle_visibility()
                st.experimental_rerun()

        search_projects()

    for wf_name, wf in wf_config.items():
        emp = st.empty()
        col1, col2, col3 = emp.columns([5, 2, 2])
        reference_name = "Source" if wf.get("workflow_type") == WorkflowType.PRE_POPULATE.value else "Target"
        non_reference_name = "Target" if wf.get("workflow_type") == WorkflowType.PRE_POPULATE.value else "Source"
        with col1:
            with st.expander(wf_name):
                st.text(f'Stage Filter: {wf["spec"]["stage_filter"]}')
                st.text(f'{reference_name} Project:')
                st.text(f'--{wf["meta"]["reference_project_name"]}')
                st.text(f'{non_reference_name} Projects:')
                for target_project_name in wf["meta"]["non_reference_project_names"]:
                    st.text(f'--{target_project_name}')
        if wf.get("workflow_type", WorkflowType.PRE_POPULATE.value) == WorkflowType.PRE_POPULATE.value:
            col2.button("Sync 🔄", key=f"sync_{wf_name}", on_click=sync, args=(wf_name, wf,), type="primary")
        col3.button("Delete ❌", key=f"delete_{wf_name}", on_click=delete_workflow, args=(wf_name,))

    st.title('New Workflow')

    if not get_state().show_element:
        st.button('➕', on_click=toggle_creation_flow)
    else:
        st.button('🗑️', on_click=toggle_creation_flow)
    if get_state().show_element:
        render_workflow_add()


if __name__ == "__main__":
    render_workflows_page()
