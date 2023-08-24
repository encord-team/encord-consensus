from typing import Dict, List

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from encord_consensus.lib.data_model import RegionOfInterest


def generate_stacked_chart(
    region: RegionOfInterest,
    selected_projects: List[str],
    project_title_lookup: Dict[str, str],
) -> Figure:
    source_boxes = region.ranges_by_source
    fig, ax = plt.subplots()
    ax.plot([0, 0], [0, 0])

    indexes = {source: selected_projects.index(source) for source in source_boxes}
    cmap = {source: plt.get_cmap("tab20").colors[idx] for source, idx in indexes.items()}

    for source, boxes in source_boxes.items():
        for box in boxes:
            ax.add_patch(
                Rectangle(
                    (box[0], indexes[source]),
                    box[1] - box[0],
                    0.7,
                    color=cmap[source],
                    alpha=0.4,
                )
            )
    plt.xlim(max(min(region.frame_votes) - 5, 0), max(region.frame_votes) + 5)
    plt.ylim(-1, len(indexes) + 1)
    ax.set_xlabel("Frame Number")
    ax.set_ylabel("Project")
    ax.set_yticks(
        [idx + 0.4 for idx in indexes.values()],
        [project_title_lookup[k] for k in indexes.keys()],
    )
    return fig
