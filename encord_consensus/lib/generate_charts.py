from typing import Dict, List

import altair as alt
import altair.vegalite.v5.api as alt_api
import matplotlib.pyplot as plt
import pandas as pd
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


def get_bar_chart(data: dict, title: str, x_title: str, y_title: str) -> alt_api.Chart:
    data_df = pd.DataFrame({x_title: list(data.keys()), y_title: list(data.values())})
    chart = alt.Chart(
        data_df,
        title=alt.Title(title, fontSize=24, anchor=alt.TitleAnchor("middle")),
    ).mark_bar()
    return chart.encode(
        alt.X(x_title).title(x_title).type("ordinal"),
        alt.Y(y_title).title(y_title).type("quantitative"),
    ).configure_axis(
        labelAngle=0,  # Display axis labels horizontally
        labelFontSize=20,
        titleFontSize=20,
    )


def get_line_chart(data: dict, title: str, x_title: str, y_title: str) -> alt_api.Chart:
    data_df = pd.DataFrame({"x": list(data.keys()), "y": list(data.values())})
    data_df["diff"] = data_df["y"].diff().fillna(0)
    data_df["segment"] = (data_df["diff"] != 0).cumsum()

    base = alt.Chart(data_df, title=alt.Title(title, fontSize=24, anchor=alt.TitleAnchor("middle")),).encode(
        alt.X("x").title(x_title).type("ordinal"),
        alt.Y("y").title(y_title).type("quantitative").axis(format="d"),
        tooltip=[alt.Tooltip("x").title(x_title), alt.Tooltip("y").title(y_title)],  # Hide `segment` from the tooltip
    )

    chart = base.mark_line(point=True).encode(detail="segment") + base.mark_line(strokeDash=[5, 5])

    return chart.configure_axis(
        labelAngle=0,  # Display axis labels horizontally
        labelFontSize=20,
        titleFontSize=20,
    )
