from typing import List, Dict, Set

from .data_model import RegionOfInterest


def _initialise_export_dict(lr_data: Dict) -> Dict:
    first_lr = list(lr_data.values())[0]
    export_dict = {
        k: first_lr[k]
        for k in [
            "dataset_hash",
            "dataset_title",
            "data_title",
            "data_hash",
            "data_type",
        ]
    }
    export_dict["data_units"] = first_lr["data_units"]
    export_dict["data_units"][export_dict["data_hash"]]["labels"] = {}
    for k in ["classification_answers", "consensus_meta"]:
        export_dict[k] = {}
    return export_dict


def export_regions_of_interest(
    regions: List[RegionOfInterest],
    lr_data: Dict,
    region_hashes_to_include: Set[int] = None,
) -> Dict:
    export_dict = _initialise_export_dict(lr_data)
    data_hash = export_dict["data_hash"]
    filtered_regions = regions
    if region_hashes_to_include:
        filtered_regions = [r for r in regions if hash(r) in region_hashes_to_include]
    for region in filtered_regions:
        region_hash = hash(region)
        export_dict["classification_answers"][region_hash] = {
            "regionHash": region_hash,
            "classifications": region.answer.classification_answers["classifications"],
        }
        export_dict["consensus_meta"][region_hash] = {
            "score": round(region.score, 4),
            "answer_fq_name": region.answer.fq_name,
        }

        for frame, votes in region.frame_votes.items():
            classification_entry = {
                "name": region.answer.name,
                "value": region.answer.value,
                "featureHash": region.answer.feature_hash,
                "regionHash": region_hash,
                "voteProjectHashes": votes,
                "voteCount": len(votes),
            }
            if not export_dict["data_units"][data_hash]["labels"].get(frame):
                export_dict["data_units"][data_hash]["labels"][frame] = [
                    classification_entry
                ]
            else:
                export_dict["data_units"][data_hash]["labels"][frame].append(
                    classification_entry
                )
    return export_dict
