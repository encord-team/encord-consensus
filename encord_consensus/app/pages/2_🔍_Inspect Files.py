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
    download_data_hash_data_from_projects,
    list_all_data_rows,
)

st.set_page_config(page_title=CONSENSUS_BROWSER_TAB_TITLE, page_icon=ENCORD_ICON_URL)
set_page_css()
st.write(f"# {INSPECT_FILES_PAGE_TITLE}")


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


def st_select_data_hash(data_hash, data_title):
    with st.spinner("Downloading data..."):
        st.session_state.selected_data_hash = (data_hash, data_title)
        st.session_state.lr_data = download_data_hash_data_from_projects(
            st.session_state.app_user_client, data_hash, st.session_state.selected_projects
        )


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


if "attached_datasets" not in st.session_state:
    st.warning(f"Seems like you haven't selected any projects, please proceed to {CHOOSE_PROJECT_PAGE_TITLE}.")
    with st.container():
        if st.button(f"Go to {CHOOSE_PROJECT_PAGE_TITLE}", use_container_width=True):
            switch_page(CHOOSE_PROJECT_PAGE_NAME)
        st.write("<div class='PageButtonMarker'/>", unsafe_allow_html=True)  # Enlarge page buttons using CSS
    exit(0)


st.write("## Select the file to run consensus on")

if "selected_data_hash" not in st.session_state:
    st.session_state.selected_data_hash = ()
if "lr_data" not in st.session_state:
    st.session_state.lr_data = {}
if "consensus_has_been_calculated" not in st.session_state:
    st.session_state.consensus_has_been_calculated = False
if "regions_to_export" not in st.session_state:
    st.session_state.regions_to_export = set()
if "data_export" not in st.session_state:
    st.session_state.data_export = {}
if "pickers_to_show" not in st.session_state:
    st.session_state.pickers_to_show = set()

for dr in list_all_data_rows(
    st.session_state.app_user_client, st.session_state.attached_datasets, data_types=SUPPORTED_DATA_TYPES
):
    emp = st.empty()
    col1, col2 = emp.columns([9, 3])
    col1.markdown(dr.title, unsafe_allow_html=True)
    col2.button(
        "Select",
        key=f"select_{dr.uid}",
        on_click=st_select_data_hash,
        args=(dr.uid, dr.title),
        disabled=st.session_state.selected_data_hash.count(dr.uid) == 1,
    )

if not st.session_state.selected_data_hash:
    exit(0)

st.write("Downloaded data for:")
st.write(st.session_state.selected_data_hash)

# Display the file's thumbnail
if not st.session_state.get("downloaded_file"):
    show_file_thumbnail(
        st.session_state.app_user_client.get_project(st.session_state.selected_projects[0]),
        st.session_state.selected_data_hash[0],
    )

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

            lr = next(iter(st.session_state.lr_data.values()))
            if lr.data_type == DataType.IMAGE.value:
                continue

            st.button(
                "Toggle Chart",
                on_click=st_set_picker,
                args=(hash(region),),
                key=f"show_{hash(region)}",
            )

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
    if len(st.session_state.regions_to_export) == 0:
        st.write("No regions available for export.")
    else:
        one_region = len(st.session_state.regions_to_export) == 1
        st.write(f"{len(st.session_state.regions_to_export)} region{'' if one_region else 's'} available for export.")

        if st.button("Prepare Export", on_click=prepare_export) and st.session_state.data_export:
            st.write("Your export is ready to download!")
            st.download_button(
                label="Download Export",
                data=st.session_state.data_export,
                file_name=f'consensus_label_export_{datetime.datetime.now().isoformat(timespec="seconds")}.json',
                mime="application/json",
                on_click=reset_export,
            )
