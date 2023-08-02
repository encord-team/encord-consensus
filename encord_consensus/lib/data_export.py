from typing import List, Dict, Set

from .data_model import RegionOfInterest


def _initialise_export_dict(lr_data: Dict) -> Dict:
    first_lr = list(lr_data.values())[0]
    result = {
        k: first_lr[k]
        for k in [
            "dataset_hash",
            "dataset_title",
            "data_title",
            "data_hash",
            "data_type",
        ]
    }
    result["data_units"] = first_lr["data_units"]
    result["data_units"][result["data_hash"]]["labels"] = {}
    for k in ["classification_answers", "consensus_meta"]:
        result[k] = {}
    return result


def export_regions_of_interest(
    regions: List[RegionOfInterest],
    lr_data: Dict,
    region_hashes_to_include: Set[int] = None,
) -> Dict:
    result = _initialise_export_dict(lr_data)
    data_hash = result["data_hash"]
    filtered_regions = regions
    if region_hashes_to_include:
        filtered_regions = [r for r in regions if hash(r) in region_hashes_to_include]
    for region in filtered_regions:
        region_hash = hash(region)
        result["classification_answers"][region_hash] = {
            "regionHash": region_hash,
            "classifications": region.answer.classification_answers["classifications"],
        }
        result["consensus_meta"][region_hash] = {
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
            if not result["data_units"][data_hash]["labels"].get(frame):
                result["data_units"][data_hash]["labels"][frame] = [
                    classification_entry
                ]
            else:
                result["data_units"][data_hash]["labels"][frame].append(
                    classification_entry
                )
    return result
