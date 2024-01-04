import json
from pathlib import Path
from typing import Dict

import streamlit as st

from encord_consensus.app.common.constants import (
    WORKFLOWS_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
)
from encord_consensus.app.common.css import set_page_css
from encord_consensus.app.common.state import State, get_state
from encord_consensus.lib.workflow_utils import send_to_annotate
from encord_consensus.lib.utils import get_project_root


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

    for wf_name, wf in wf_config.items():
        emp = st.empty()
        col1, col2, col3 = emp.columns([5, 2, 2])
        with col1:
            with st.expander(wf_name):
                st.text('Source Project:')
                st.text(wf["meta"]["source_project_name"])
                st.text('Target Projects:')
                for target_project_name in wf["meta"]["target_project_names"]:
                    st.text(target_project_name)
        col2.button("Sync 🔄", key=f"sync_{wf_name}", on_click=sync, args=(wf_name, wf,), type="primary")
        col3.button("Delete ❌", key=f"delete_{wf_name}", on_click=delete_workflow, args=(wf_name,))


if __name__ == "__main__":
    render_workflows_page()
