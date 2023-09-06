import datetime
import json
import os
import warnings

import streamlit as st
from dotenv import load_dotenv
from encord.constants.enums import DataType
from lib.data_export import export_regions_of_interest
from lib.data_model import RegionOfInterest
from lib.data_transformation import prepare_data_for_consensus
from lib.frame_label_consensus import (
    aggregate_by_answer,
    calculate_frame_level_min_n_agreement,
    find_regions_of_interest,
)
from lib.generate_charts import (
    generate_stacked_chart,
    get_bar_chart,
    get_consensus_label_agreement_project_view_chart,
    get_line_chart,
)
from lib.project_access import (
    count_label_rows,
    download_data_hash_data_from_projects,
    get_all_datasets,
    get_classifications_ontology,
    get_user_client,
    list_all_data_rows,
    list_projects,
)

warnings.filterwarnings("error", category=UserWarning)

SUPPORTED_DATA_FORMATS = [DataType.VIDEO]

load_dotenv(encoding="utf-8")
app_user_client = get_user_client(os.getenv("ENCORD_KEYFILE"))

if "attached_datasets" not in st.session_state:
    st.session_state.attached_datasets = []
if "selected_projects" not in st.session_state:
    st.session_state.selected_projects = []
if "ontology" not in st.session_state:
    st.session_state.ontology = {}
if "label_rows" not in st.session_state:
    st.session_state.label_rows = {}
if "selected_data_hash" not in st.session_state:
    st.session_state.selected_data_hash = ()
if "lr_data" not in st.session_state:
    st.session_state.lr_data = {}
if "project_title_lookup" not in st.session_state:
    st.session_state.project_title_lookup = {}
if "consensus_has_been_calculated" not in st.session_state:
    st.session_state.consensus_has_been_calculated = False
if "regions_to_export" not in st.session_state:
    st.session_state.regions_to_export = set()
if "data_export" not in st.session_state:
    st.session_state.data_export = {}
if "pickers_to_show" not in st.session_state:
    st.session_state.pickers_to_show = set()


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


def st_set_picker(to_pick: int) -> None:
    if to_pick in st.session_state.pickers_to_show:
        st.session_state.pickers_to_show.remove(to_pick)
    else:
        st.session_state.pickers_to_show.add(to_pick)


def st_select_region(region: RegionOfInterest):
    region_hash = hash(region)
    if region_hash not in st.session_state.regions_to_export:
        st.session_state.regions_to_export.add(region_hash)
    else:
        st.session_state.regions_to_export.remove(region_hash)


def prepare_export():
    st.session_state.data_export = json.dumps(
        export_regions_of_interest(
            regions=st.session_state.regions_of_interest,
            lr_data=st.session_state.lr_data,
            region_hashes_to_include=st.session_state.regions_to_export,
        )
    )


def reset_export():
    st.session_state.data_export = {}


st.write("# Consensus Tool")

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

    st.write("## Select Data Row to run consensus on")
else:
    st.write("## Selected Data Row to run consensus on")


def st_select_data_hash(data_hash, data_title):
    with st.spinner("Downloading data..."):
        st.session_state.selected_data_hash = (data_hash, data_title)
        st.session_state.lr_data = download_data_hash_data_from_projects(
            app_user_client, data_hash, st.session_state.selected_projects
        )


if not st.session_state.selected_data_hash:
    for dr in list_all_data_rows(
        app_user_client, st.session_state.attached_datasets, data_types=SUPPORTED_DATA_FORMATS
    ):
        emp = st.empty()
        col1, col2 = emp.columns([9, 3])
        col1.markdown(dr.title, unsafe_allow_html=True)
        col2.button(
            "Select",
            key=f"select_{dr.uid}",
            on_click=st_select_data_hash,
            args=(dr.uid, dr.title),
        )
elif st.session_state.selected_data_hash:
    st.write("Downloaded data for:")
    st.write(st.session_state.selected_data_hash)

# TODO: extract emails and project names for consensus

if st.session_state.lr_data:
    total_num_annnotators = len(st.session_state.selected_projects)
    if not st.session_state.consensus_has_been_calculated:
        with st.spinner("Processing data..."):
            prepared_data = prepare_data_for_consensus(st.session_state.ontology, st.session_state.lr_data)
            aggregated_data = aggregate_by_answer(prepared_data)
            st.session_state.fl_integrated_agreement = calculate_frame_level_min_n_agreement(aggregated_data)
            st.session_state.regions_of_interest = find_regions_of_interest(aggregated_data, total_num_annnotators)
            st.session_state.consensus_has_been_calculated = True
    st.write("## Consensus Section")
    st.write("### Consensus Agreement Report")
    st.altair_chart(
        get_bar_chart(
            st.session_state.fl_integrated_agreement,
            title="Consensus on Annotations by Number of Contributors",
            x_title="Concurring annotators",
            y_title="Number of annotations",
        ),
        use_container_width=True,
    )
    st.write("### Demo Consensus Analysis Tool")
    st.write(f"There are a total of {total_num_annnotators} annotators that could agree.")
    st.slider(
        "Minimum Agreement",
        min_value=1,
        max_value=total_num_annnotators,
        value=total_num_annnotators,
        step=1,
        key="min_agreement_slider",
    )
    st.slider(
        "Minimum Integrated Agreement Score",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        key="min_integrated_score_slider",
    )

    for region in st.session_state.regions_of_interest:
        if (
            region.consensus_data.max_agreement >= st.session_state.min_agreement_slider
            and region.consensus_data.integrated_agreement_score >= st.session_state.min_integrated_score_slider
        ):
            st.checkbox(
                "Select",
                on_change=st_select_region,
                args=(region,),
                key=f"select_{hash(region)}",
            )
            st.button(
                "Toggle Chart",
                on_click=st_set_picker,
                args=(hash(region),),
                key=f"show_{hash(region)}",
            )

            mini_report = (
                f"Mini Report\nIntegrated Agreement Score: {region.consensus_data.integrated_agreement_score}\n\n"
                + "\n".join(
                    [
                        f"At least {k} annotators agreeing: {v} frames"
                        for k, v in region.consensus_data.min_n_agreement.items()
                    ]
                )
                + "\n\nN Scores\n"
                + "\n".join([f"{n}-score: {s}" for n, s in region.consensus_data.n_scores.items()])
            )
            identifier_text = f"Region number {region.region_number}\n\nSelected Answers\n"
            for idx, part in enumerate(region.answer.fq_parts):
                identifier_text += (idx * "\t") + f"{part.question}: {part.answer}\n"
            st.code(f"{identifier_text}\n{mini_report}")

            if hash(region) not in st.session_state.pickers_to_show:
                st.altair_chart(
                    get_line_chart(
                        region.frame_vote_counts,
                        title="Agreement on the Consensus Label (Count per Frame)",
                        x_title="Timeline frames",
                        y_title="Concurring  annotators",
                    ).interactive(bind_y=False),
                    use_container_width=True,
                )

            if hash(region) in st.session_state.pickers_to_show:
                chart = get_consensus_label_agreement_project_view_chart(region, st.session_state.project_title_lookup)
                if chart is not None:
                    st.altair_chart(chart.interactive(bind_y=False), use_container_width=True)

    st.write("### Export")
    st.write(f"There are a total of {len(st.session_state.regions_to_export)} regions to export.")

    if st.button("Prepare Export", on_click=prepare_export) and st.session_state.data_export:
        st.write("Your export is ready to download!")
        st.download_button(
            label="Download Export",
            data=st.session_state.data_export,
            file_name=f'consensus_label_export_{datetime.datetime.now().isoformat(timespec="seconds")}.json',
            mime="application/json",
            on_click=reset_export,
        )
