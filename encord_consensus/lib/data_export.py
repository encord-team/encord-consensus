import base64
import uuid
from datetime import datetime
from typing import Dict, List, Set

import pytz

from .data_model import RegionOfInterest


GMT_TIMEZONE = pytz.timezone("GMT")
DATETIME_STRING_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"


def _get_timestamp(now=datetime.now()):
    new_timezone_timestamp = now.astimezone(GMT_TIMEZONE)
    return new_timezone_timestamp.strftime(DATETIME_STRING_FORMAT)

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


def _short_uuid_str() -> str:
    """This is being used as a condensed uuid."""
    return base64.b64encode(uuid.uuid4().bytes[:6]).decode("utf-8")


def export_regions_of_interest(
    regions: List[RegionOfInterest],
    lr_data: Dict,
    region_hashes_to_include: Set[int] = None,
) -> Dict:
    now = datetime.now()
    created_at = _get_timestamp(now)
    export_dict = _initialise_export_dict(lr_data)
    data_hash = export_dict["data_hash"]
    filtered_regions = regions
    if region_hashes_to_include:
        filtered_regions = [r for r in regions if hash(r) in region_hashes_to_include]
    for region in filtered_regions:
        object_hash = _short_uuid_str()
        export_dict["classification_answers"][object_hash] = {
            "classificationHash": object_hash,
            "classifications": region.answer.classification_answers["classifications"],
        }

        for frame in region.frame_votes.keys():
            classification_entry = {
                "name": region.answer.name,
                "value": region.answer.value,
                "featureHash": region.answer.feature_hash,
                "createdAt": created_at,
                "createdBy": "robot@encord.com",  # YOU CAN CHANGE THIS TO BE EMAIL OF UPLOADING USER
                "confidence": 1,
                "classificationHash": object_hash,
                "manualAnnotation": True,
            }
            if not export_dict["data_units"][data_hash]["labels"].get(frame):
                export_dict["data_units"][data_hash]["labels"][frame] = {
                    'objects': [],
                    'classifications': [classification_entry]
                }
            else:
                export_dict["data_units"][data_hash]["labels"][frame]['classifications'].append(classification_entry)
    return export_dict
