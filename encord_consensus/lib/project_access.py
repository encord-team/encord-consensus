import json
from pathlib import Path
from typing import List, Dict

from encord import EncordUserClient, Project


def get_user_client(path_to_keyfile: str) -> EncordUserClient:
    with Path(path_to_keyfile).open(encoding="utf-8") as f:
        private_key = f.read()
    return EncordUserClient.create_with_ssh_private_key(private_key)


def list_projects(user_client, search_query) -> List[Dict]:
    return user_client.get_projects(title_like=f'%{search_query}%')


def get_all_projects(user_client, project_hashes: List) -> List[Project]:
    return [user_client.get_project(p_hash) for p_hash in project_hashes]


def get_all_datasets(user_client, project_hash):
    return {d['dataset_hash'] for d in user_client.get_project(project_hash).datasets}


def get_classifications_ontology(user_client, project_hash):
    project = user_client.get_project(project_hash)
    return project.get_project()['editor_ontology']['classifications']


def count_label_rows(user_client, p_hash):
    project = user_client.get_project(p_hash)
    label_hashes = [lrm.label_hash for lrm in project.list_label_rows()]
    return len(label_hashes)


def list_all_data_rows(user_client, datasets):
    res = []
    for dataset_hash in datasets:
        res.extend(user_client.get_dataset(dataset_hash).list_data_rows())
    return res


def download_data_hash_data_from_projects(user_client, data_hash, projects):
    lr_data = {}
    for p_hash in projects:
        project = user_client.get_project(p_hash)
        lrms = project.list_label_rows(data_hashes=[data_hash])
        lr_hash = lrms[0].label_hash
        lr = project.get_label_row(lr_hash)
        lr_data[p_hash] = lr
    return lr_data
