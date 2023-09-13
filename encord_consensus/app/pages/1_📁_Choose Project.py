import os

import streamlit as st
from dotenv import load_dotenv

from encord_consensus.app.common.constants import (
    CHOOSE_PROJECT_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
)
from encord_consensus.lib.project_access import (
    count_label_rows,
    get_all_datasets,
    get_classifications_ontology,
    get_encord_client,
    list_all_data_rows,
    list_projects,
)

st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
st.write(f"# {CHOOSE_PROJECT_PAGE_TITLE}")

# Get app configurations
load_dotenv(encoding="utf-8")
app_user_client = get_encord_client(os.getenv("ENCORD_KEYFILE"))
st.session_state.app_user_client = app_user_client


def st_add_project(project_hash, project_title):
    datasets = get_all_datasets(app_user_client, project_hash)
    if count_label_rows(app_user_client, project_hash) != len(list_all_data_rows(app_user_client, datasets)):
        st.warning("You must select projects where all label rows are annotated!", icon="⚠️")
        return

    if not st.session_state.selected_projects:
        st.session_state.attached_datasets = datasets
    elif datasets != st.session_state.attached_datasets:
        st.warning("You must select projects with the same attached datasets!", icon="⚠️")
        return
    if not st.session_state.ontology:
        st.session_state.ontology = get_classifications_ontology(app_user_client, project_hash)
    elif get_classifications_ontology(app_user_client, project_hash) != st.session_state.ontology:
        st.warning("You must select projects with the same ontology!", icon="⚠️")
        return

    st.session_state.selected_projects.append(project_hash)
    st.session_state.project_title_lookup[project_hash] = project_title


def st_remove_project(project_hash):
    st.session_state.selected_projects.remove(project_hash)
    if not st.session_state.selected_projects:
        st.session_state.attached_datasets = []
        st.session_state.ontology = {}


st.write("# Consensus Tool")

if "selected_data_hash" not in st.session_state:
    st.session_state.selected_data_hash = ()
if "selected_projects" not in st.session_state:
    st.session_state.selected_projects = []
if "ontology" not in st.session_state:
    st.session_state.ontology = {}
if "project_title_lookup" not in st.session_state:
    st.session_state.project_title_lookup = {}

if not st.session_state.selected_data_hash:
    st.write("## Project Selection")
    text_search = st.text_input("Search projects by title", value="")

    if text_search:
        matched_projects = list_projects(app_user_client, text_search)
        for p in matched_projects:
            p_hash = p["project"]["project_hash"]
            p_title = p["project"]["title"]
            emp = st.empty()
            col1, col2 = emp.columns([9, 3])
            col1.markdown(p_title, unsafe_allow_html=True)
            if p_hash not in st.session_state.selected_projects:
                col2.button(
                    "Add",
                    key=f"add_{p_hash}",
                    on_click=st_add_project,
                    args=(p_hash, p_title),
                )

    st.write("## Selected Projects")
    for p_hash in st.session_state.selected_projects:
        emp = st.empty()
        col1, col2 = emp.columns([9, 3])
        col1.markdown(st.session_state.project_title_lookup[p_hash], unsafe_allow_html=True)
        col2.button("Remove", key=f"del_{p_hash}", on_click=st_remove_project, args=(p_hash,))
