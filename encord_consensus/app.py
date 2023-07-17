import os

import streamlit as st
from dotenv import load_dotenv

from lib.data_transformation import prepare_data_for_consensus
from lib.frame_label_consensus import calculate_frame_level_agreement, calculate_frame_level_integrated_agreement, \
    find_regions_of_interest, calculate_agreement_in_region, calculate_region_frame_level_integrated_agreement
from lib.project_access import get_user_client, list_projects, get_classifications_ontology, count_label_rows, \
    list_all_data_rows, download_data_hash_data_from_projects, get_all_datasets

load_dotenv()
app_user_client = get_user_client(os.getenv('ENCORD_KEYFILE'))

if 'attached_datasets' not in st.session_state:
    st.session_state.attached_datasets = []
if 'selected_projects' not in st.session_state:
    st.session_state.selected_projects = []
if 'ontology' not in st.session_state:
    st.session_state.ontology = {}
if 'label_rows' not in st.session_state:
    st.session_state.label_rows = {}
if 'selected_data_hash' not in st.session_state:
    st.session_state.selected_data_hash = ()
if 'lr_data' not in st.session_state:
    st.session_state.lr_data = {}
if 'project_title_lookup' not in st.session_state:
    st.session_state.project_title_lookup = {}
if 'consensus_has_been_calculated' not in st.session_state:
    st.session_state.consensus_has_been_calculated = False


def st_add_project(project_hash, project_title):
    datasets = get_all_datasets(app_user_client, project_hash)
    if count_label_rows(app_user_client, project_hash) != len(list_all_data_rows(app_user_client, datasets)):
        st.warning('You must select projects where all label rows are annotated!', icon="⚠️")
        return

    if not st.session_state.selected_projects:
        st.session_state.attached_datasets = datasets
    elif datasets != st.session_state.attached_datasets:
        st.warning('You must select projects with the same attached datasets!', icon="⚠️")
        return
    if not st.session_state.ontology:
        st.session_state.ontology = get_classifications_ontology(app_user_client, project_hash)
    elif get_classifications_ontology(app_user_client, project_hash) != st.session_state.ontology:
        st.warning('You must select projects with the same ontology!', icon="⚠️")
        return

    st.session_state.selected_projects.append(project_hash)
    st.session_state.project_title_lookup[project_hash] = project_title


def st_remove_project(project_hash):
    st.session_state.selected_projects.remove(project_hash)
    if not st.session_state.selected_projects:
        st.session_state.attached_datasets = []
        st.session_state.ontology = {}


st.write('# Consensus Tool')

if not st.session_state.selected_data_hash:
    st.write('## Project Selection')
    text_search = st.text_input("Search projects by title", value="")

    if text_search:
        matched_projects = list_projects(app_user_client, text_search)
        for p in matched_projects:
            p_hash = p['project']['project_hash']
            p_title = p['project']['title']
            emp = st.empty()
            col1, col2 = emp.columns([9, 3])
            col1.markdown(p_title, unsafe_allow_html=True)
            if p_hash not in st.session_state.selected_projects:
                col2.button("Add", key=f'add_{p_hash}', on_click=st_add_project, args=(p_hash, p_title))

    st.write('## Selected Projects')
    for p_hash in st.session_state.selected_projects:
        emp = st.empty()
        col1, col2 = emp.columns([9, 3])
        col1.markdown(st.session_state.project_title_lookup[p_hash], unsafe_allow_html=True)
        col2.button("Remove", key=f'del_{p_hash}', on_click=st_remove_project, args=(p_hash,))

    st.write('## Select Data Row to run consensus on')
else:
    st.write('## Selected Data Row to run consensus on')


def st_select_data_hash(data_hash, data_title):
    with st.spinner('Downloading data...'):
        st.session_state.selected_data_hash = (data_hash, data_title)
        st.session_state.lr_data = download_data_hash_data_from_projects(
            app_user_client,
            data_hash,
            st.session_state.selected_projects
        )


if not st.session_state.selected_data_hash:
    for dr in list_all_data_rows(app_user_client, st.session_state.attached_datasets):
        emp = st.empty()
        col1, col2 = emp.columns([9, 3])
        col1.markdown(dr.title, unsafe_allow_html=True)
        col2.button("Select", key=f'select_{dr.uid}', on_click=st_select_data_hash, args=(dr.uid, dr.title))
elif st.session_state.selected_data_hash:
    st.write('Downloaded data for:')
    st.write(st.session_state.selected_data_hash)

# TODO: extract emails and project names for consensus
# TODO: instance level comparison (slightly trickier, need to do some clever indexing for big projects + handle edges)
# TODO: Export
# TODO: make the fqname format nicer...

if st.session_state.lr_data:
    if not st.session_state.consensus_has_been_calculated:
        with st.spinner('Processing data...'):
            prepared_data = prepare_data_for_consensus(st.session_state.ontology, st.session_state.lr_data)
            frame_level_agreement_data = calculate_frame_level_agreement(prepared_data)
            st.session_state.fl_integrated_agreement = calculate_frame_level_integrated_agreement(frame_level_agreement_data)
            st.session_state.regions_of_interest = find_regions_of_interest(frame_level_agreement_data)
            st.session_state.consensus_has_been_calculated = True
    st.write('## Consensus Section')
    st.write('### Consensus Agreement Report')
    st.bar_chart(st.session_state.fl_integrated_agreement)
    st.write('### Demo Consensus Analysis Tool')
    total_num_annnotators = len(st.session_state.selected_projects)
    st.write(f'There are a total of {total_num_annnotators} annotators that could agree.')
    st.slider(
        'Minimum Agreement',
        min_value=1,
        max_value=total_num_annnotators,
        value=total_num_annnotators,
        step=1,
        key='min_agreement_slider',
    )
    st.slider(
        'Minimum Score',
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        key='min_score_slider',
    )
    for key, value in st.session_state.regions_of_interest.items():
        score = round(calculate_agreement_in_region(value['data'], total_num_annnotators), 2)
        if value['max_agreement'] >= st.session_state.min_agreement_slider and score >= st.session_state.min_score_slider:
            mini_report = f"Mini Report\nScore: {score}\n" + "\n".join([
                f"At least {k} annotators agreeing: {v} frames"
                for k, v in calculate_region_frame_level_integrated_agreement(value['data']).items()
            ])
            # TODO: Make the internal representation of this better
            prefix_identifier = key.split('@')[0]
            identifier_text = f"Region number {key.split('@')[1]}\n\nSelected Answers\n"
            for idx, chunk in enumerate(prefix_identifier.split('&')):
                identifier_text += (idx * '\t') + f"{chunk.split('=')[0]}: {chunk.split('=')[1]}\n"
            st.code(f"{identifier_text}\n{mini_report}")
            st.bar_chart(value['data'])
