import datetime
import json

import streamlit as st
from encord.constants.enums import DataType
from encord.project import Project
from streamlit_extras.switch_page_button import switch_page

from encord_consensus.app.common.constants import (
    CHOOSE_PROJECT_PAGE_NAME,
    CHOOSE_PROJECT_PAGE_TITLE,
    CONSENSUS_BROWSER_TAB_TITLE,
    ENCORD_ICON_URL,
    INSPECT_FILES_PAGE_TITLE,
)
from encord_consensus.app.common.css import set_page_css
from encord_consensus.app.common.state import InspectFilesState, State, get_state
from encord_consensus.lib.constants import SUPPORTED_DATA_TYPES
from encord_consensus.lib.data_export import export_regions_of_interest
from encord_consensus.lib.data_model import RegionOfInterest
from encord_consensus.lib.data_transformation import prepare_data_for_consensus
from encord_consensus.lib.frame_label_consensus import (
    aggregate_by_answer,
    calculate_frame_level_min_n_agreement,
    find_regions_of_interest,
)
from encord_consensus.lib.generate_charts import (
    get_bar_chart,
    get_consensus_label_agreement_project_view_chart,
    get_line_chart,
)
from encord_consensus.lib.project_access import (
    download_label_row_from_projects,
    get_all_dataset_hashes,
    list_all_data_rows,
)

st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
set_page_css()
st.write(f"# {INSPECT_FILES_PAGE_TITLE}")
State.init()


def show_file_thumbnail(encord_project: Project, file_data_hash: str):
    # NOTE: Using obsolete LabelRow class instead of LabelRowV2 because LabelRowV2 can't retrieve signed urls
    # Ensure that the label row corresponding to the data hash exists in the platform (label_hash must not be `None`)
    lr_metadata = encord_project.list_label_rows(data_hashes=[file_data_hash], include_uninitialised_labels=True)[0]
    if lr_metadata.label_hash is None:
        lr = encord_project.create_label_row(lr_metadata.data_hash)
    else:
        lr = encord_project.get_label_row(lr_metadata.label_hash)

    if DataType(lr.data_type) not in SUPPORTED_DATA_TYPES:
        # add logs to trace inadequate uses
        return

    if lr.data_type == DataType.IMAGE.value:
        signed_url = next(iter(lr.data_units.values()), dict()).get("data_link")
        st.image(signed_url)
    elif lr.data_type == DataType.VIDEO.value:
        signed_url = next(iter(lr.data_units.values()), dict()).get("data_link")
        st.video(signed_url)


def select_data_hash(data_hash: str) -> None:
    with st.spinner("Downloading data..."):
        get_state().inspect_files_state = InspectFilesState(data_hash=data_hash)
        get_state().inspect_files_state.lr_data = download_label_row_from_projects(get_state().projects, data_hash)


def set_picker(to_pick: int) -> None:
    if to_pick in get_state().inspect_files_state.pickers_to_show:
        get_state().inspect_files_state.pickers_to_show.remove(to_pick)
    else:
        get_state().inspect_files_state.pickers_to_show.add(to_pick)


def select_region(region: RegionOfInterest):
    region_hash = hash(region)
    if region_hash not in get_state().inspect_files_state.regions_to_export:
        get_state().inspect_files_state.regions_to_export.add(region_hash)
    else:
        get_state().inspect_files_state.regions_to_export.remove(region_hash)


def prepare_export():
    get_state().inspect_files_state.data_export = json.dumps(
        export_regions_of_interest(
            regions=get_state().inspect_files_state.regions_of_interest,
            lr_data=get_state().inspect_files_state.lr_data,
            region_hashes_to_include=get_state().inspect_files_state.regions_to_export,
        )
    )


def reset_export():
    get_state().inspect_files_state.data_export = {}


if len(get_state().projects) == 0:
    st.warning(f"Seems like you haven't selected any projects, please proceed to {CHOOSE_PROJECT_PAGE_TITLE}.")
    with st.container():
        if st.button(f"Go to {CHOOSE_PROJECT_PAGE_TITLE}", use_container_width=True):
            switch_page(CHOOSE_PROJECT_PAGE_NAME)
        st.write("<div class='PageButtonMarker'/>", unsafe_allow_html=True)  # Enlarge page buttons using CSS
    exit(0)


st.write("## Select the file to run consensus on")

for dr in list_all_data_rows(
    get_state().encord_client, get_all_dataset_hashes(get_state().projects[0]), data_types=SUPPORTED_DATA_TYPES
):
    emp = st.empty()
    col1, col2 = emp.columns([9, 3])
    col1.markdown(dr.title, unsafe_allow_html=True)
    col2.button(
        "Select",
        key=f"select_{dr.uid}",
        on_click=select_data_hash,
        args=(dr.uid,),
        disabled=get_state().inspect_files_state == dr.uid,
    )

if get_state().inspect_files_state.data_hash is None:
    exit(0)

st.write(f"Downloaded file with data hash: {get_state().inspect_files_state.data_hash}")

# Display the file's thumbnail
show_file_thumbnail(get_state().projects[0], get_state().inspect_files_state.data_hash)

# TODO: extract emails and project names for consensus

if len(get_state().inspect_files_state.lr_data) > 0:
    total_num_annnotators = len(get_state().projects)
    if not get_state().inspect_files_state.consensus_has_been_calculated:
        with st.spinner("Processing data..."):
            prepared_data = prepare_data_for_consensus(
                get_state().projects[0].ontology["classifications"], get_state().inspect_files_state.lr_data
            )
            aggregated_data = aggregate_by_answer(prepared_data)
            get_state().inspect_files_state.fl_integrated_agreement = calculate_frame_level_min_n_agreement(
                aggregated_data
            )
            get_state().inspect_files_state.regions_of_interest = find_regions_of_interest(
                aggregated_data, total_num_annnotators
            )
            get_state().inspect_files_state.consensus_has_been_calculated = True
    st.write("## Consensus Section")
    st.write("### Consensus Agreement Report")
    st.altair_chart(
        get_bar_chart(
            get_state().inspect_files_state.fl_integrated_agreement,
            title="Consensus on Annotations by Number of Contributors",
            x_title="Concurring annotators",
            y_title="Number of annotations",
        ),
        use_container_width=True,
    )
    st.write("### Demo Consensus Analysis Tool")
    st.write(f"There are a total of {total_num_annnotators} annotators that could agree.")
    get_state().inspect_files_state.min_agreement_slider = st.slider(
        "Minimum Agreement",
        min_value=1,
        max_value=total_num_annnotators,
        value=total_num_annnotators,
        step=1,
    )
    get_state().inspect_files_state.min_integrated_score_slider = st.slider(
        "Minimum Integrated Agreement Score",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        key="min_integrated_score_slider",
    )

    for region in get_state().inspect_files_state.regions_of_interest:
        if (
            region.consensus_data.max_agreement >= get_state().inspect_files_state.min_agreement_slider
            and region.consensus_data.integrated_agreement_score
            >= get_state().inspect_files_state.min_integrated_score_slider
        ):
            st.checkbox(
                "Select",
                on_change=select_region,
                args=(region,),
                key=f"select_{hash(region)}",
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

            lr = next(iter(get_state().inspect_files_state.lr_data.values()))
            if lr.data_type == DataType.IMAGE.value:
                continue

            st.button(
                "Toggle Chart",
                on_click=set_picker,
                args=(hash(region),),
                key=f"show_{hash(region)}",
            )

            if hash(region) not in get_state().inspect_files_state.pickers_to_show:
                st.altair_chart(
                    get_line_chart(
                        region.frame_vote_counts,
                        title="Agreement on the Consensus Label (Count per Frame)",
                        x_title="Timeline frames",
                        y_title="Concurring  annotators",
                    ).interactive(bind_y=False),
                    use_container_width=True,
                )

            if hash(region) in get_state().inspect_files_state.pickers_to_show:
                project_title_lookup = {p.project_hash: p.title for p in get_state().projects}
                chart = get_consensus_label_agreement_project_view_chart(region, project_title_lookup)
                if chart is not None:
                    st.altair_chart(chart.interactive(bind_y=False), use_container_width=True)

    st.write("### Export")
    if len(get_state().inspect_files_state.regions_to_export) == 0:
        st.write("No regions available for export.")
    else:
        one_region = len(get_state().inspect_files_state.regions_to_export) == 1
        st.write(
            f"{len(get_state().inspect_files_state.regions_to_export)} region{'' if one_region else 's'} available for export."
        )

        if st.button("Prepare Export", on_click=prepare_export) and get_state().inspect_files_state.data_export:
            st.write("Your export is ready to download!")
            st.download_button(
                label="Download Export",
                data=get_state().inspect_files_state.data_export,
                file_name=f'consensus_label_export_{datetime.datetime.now().isoformat(timespec="seconds")}.json',
                mime="application/json",
                on_click=reset_export,
            )
