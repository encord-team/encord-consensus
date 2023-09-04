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


def get_label_occurrence_per_frame_chart(
    region: RegionOfInterest,
    project_title_lookup: dict[str, str],
) -> alt_api.Chart:
    source_boxes = region.ranges_by_source

    raw_data = []
    # Extract projects' data points from the region of interest
    for proj_hash, matching_consensus_intervals in source_boxes.items():
        if len(matching_consensus_intervals) == 0:
            raw_data.append({"Project": project_title_lookup[proj_hash], "Start": None, "End": None})
            continue
        for start, end in matching_consensus_intervals:
            raw_data.append({"Project": project_title_lookup[proj_hash], "Start": start, "End": end})

    data = pd.DataFrame(raw_data)
    min_start = data["Start"].min(skipna=True)
    max_end = data["End"].max(skipna=True)

    # Create a bar chart (lines) to represent intervals
    chart_title = "Agreement on the Consensus Label (Project View)"
    lines = (
        alt.Chart(data, title=alt.Title(chart_title, fontSize=24, anchor=alt.TitleAnchor("middle")))
        .mark_bar(invalid=None)
        .encode(
            alt.X("Start").title("Timeline Frames").scale(domain=[max(min_start - 1, 0), max_end + 1]).axis(format="d"),
            alt.X2("End"),
            alt.Y("Project").scale(padding=0.2).axis(labelLimit=200),
            color="Project",
            tooltip=[alt.Tooltip(field_name) for field_name in data.columns],
        )
    )

    #  Create a scatter plot (points) to represent intervals with Start = End
    points_data = data[data["Start"] == data["End"]]
    points = (
        alt.Chart(points_data)
        .mark_point(size=50, filled=True)
        .encode(
            alt.X("Start"),
            alt.Y("Project"),
            color="Project",
            tooltip=[alt.Tooltip(field_name) for field_name in points_data.columns],
        )
    )

    # Combine the lines and points charts and configure axis labels and titles
    chart = lines + points
    return chart.configure_axis(
        labelFontSize=16,
        titleFontSize=20,
    )
