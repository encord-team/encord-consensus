import json
from enum import Enum
from pathlib import Path
from typing import List, Dict

from encord import EncordUserClient, Project

from encord_consensus.lib.utils import get_project_root

root_dir = get_project_root()
WORKFLOW_CONFIG_PATH = root_dir.joinpath(Path('.workflow_configs.json'))


class WorkflowType(str, Enum):
    PRE_POPULATE = 'Pre Populate'
    COPY_DOWNSTREAM = 'Copy Downstream'


def read_workflow_config():
    with open(WORKFLOW_CONFIG_PATH, 'r') as f:
        return json.load(f)


def pre_populate(
        user_client: EncordUserClient,
        source_project_hash: str,
        target_project_hashes: List[str],
        stage_filter: str = 'COMPLETE',
        target_priority: int = 1
) -> int:
    source_project = user_client.get_project(source_project_hash)
    target_projects = [
        user_client.get_project(p_hash) for p_hash in target_project_hashes
    ]
    synced_counter = 0
    for lr_s in source_project.list_label_rows_v2(workflow_graph_node_title_eq=stage_filter):
        for target_project in target_projects:
            lr_t = target_project.list_label_rows_v2(data_hashes=[lr_s.data_hash]).pop()
            if lr_t.priority == 0.5:
                if not lr_s.is_labelling_initialised:
                    lr_s.initialise_labels()
                lr_t.initialise_labels(include_object_feature_hashes=set(), include_classification_feature_hashes=set())
                for obj in lr_s.get_object_instances():
                    lr_t.add_object_instance(obj.copy())
                for cl in lr_s.get_classification_instances():
                    lr_t.add_classification_instance(cl.copy())
                lr_t.set_priority(target_priority)
                synced_counter += 1
                lr_t.save()
    return synced_counter


def get_downstream_copy_workflow_for_selection(non_reference_projects: List[Project]) -> Dict | None:
    non_ref_project_hashes = set([p.project_hash for p in non_reference_projects])
    wf_config = read_workflow_config()
    matches = [
        wf for wf in wf_config.values()
        if set(wf['spec']['target_project_hashes']) == non_ref_project_hashes
        and wf['workflow_type'] == WorkflowType.COPY_DOWNSTREAM.value
    ]
    if len(matches) == 0:
        return None
    if len(matches) == 1:
        return matches.pop()
    raise Exception('Found multiple matches in workflow config!')
