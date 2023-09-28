import os
from dataclasses import dataclass, field
from enum import Enum

import streamlit as st
from dotenv import load_dotenv
from encord import EncordUserClient, Project

from encord_consensus.lib.data_model import RegionOfInterest
from encord_consensus.lib.project_access import get_encord_client


class StateKey(str, Enum):
    GLOBAL = "GLOBAL"
    SCOPED = "SCOPED"
    SCOPED_AND_PERSISTED = "SCOPED_AND_PERSISTED"
    MEMO = "MEMO"


@dataclass
class InspectFilesState:
    data_hash: str | None = None
    lr_data: dict = field(default_factory=dict)
    consensus_has_been_calculated: bool = False
    fl_integrated_agreement: dict[int, int] = field(default_factory=dict)
    regions_of_interest: list[RegionOfInterest] = field(default_factory=list)
    regions_to_export: set = field(default_factory=set)
    data_export: dict = field(default_factory=dict)
    pickers_to_show: set = field(default_factory=set)
    min_agreement_slider: int = 1
    min_integrated_score_slider: float = 0


@dataclass
class State:
    """
    Use this class only for getting default values, otherwise use `get_state()`.
    To obtain the default `encord_client` we would call `State.encord_client`
    and to get/set the current value we would call `get_state().iou_threshold`.
    """

    encord_client: EncordUserClient
    inspect_files_state: InspectFilesState = field(default_factory=InspectFilesState)
    projects: list[Project] = field(default_factory=list)

    @classmethod
    def init(cls):
        if st.session_state.get(StateKey.GLOBAL) is None:
            load_dotenv(encoding="utf-8")
            encord_client = get_encord_client(os.getenv("ENCORD_KEYFILE"))
            st.session_state[StateKey.GLOBAL] = State(encord_client=encord_client)


def has_state():
    return StateKey.GLOBAL in st.session_state


def get_state() -> State:
    if not has_state():
        st.stop()

    return st.session_state[StateKey.GLOBAL]


def refresh(
    *,
    clear_global: bool = False,
    clear_scoped: bool = False,
    clear_memo: bool = False,
    clear_component: bool = False,
    nuke: bool = False,
):
    if nuke:
        persisted = st.session_state.pop(StateKey.SCOPED_AND_PERSISTED, {})
        st.session_state.clear()
        st.session_state[StateKey.SCOPED_AND_PERSISTED] = persisted
    else:
        if clear_global:
            st.session_state.pop(StateKey.GLOBAL, None)
        if clear_scoped:
            st.session_state.get(StateKey.SCOPED, {}).clear()
        if clear_memo:
            st.session_state.get(StateKey.MEMO, {}).clear()
        if clear_component:
            keys = {key for key in st.session_state.keys() if key not in StateKey.__members__}
            for key in keys:
                st.session_state.pop(key, None)

    st.experimental_rerun()
