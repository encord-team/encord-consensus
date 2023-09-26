import itertools
from collections import Counter, defaultdict
from typing import DefaultDict, Dict, List

from .data_model import (
    AggregatedView,
    Answer,
    ClassificationView,
    ConsensusData,
    RegionOfInterest,
)


def aggregate_by_answer(
    prepared_data: List[ClassificationView],
) -> List[AggregatedView]:
    pre_aggregated: DefaultDict[Answer, list[ClassificationView]] = defaultdict(list[ClassificationView])
    for c in prepared_data:
        pre_aggregated[c.answer].append(c)
    processed_aggregated: List[AggregatedView] = []
    for answer, classification_views in pre_aggregated.items():
        a = AggregatedView(answer=answer)
        for c in classification_views:
            for f in c.frames:
                a.frame_votes[f].append(c.source_project_hash)
        processed_aggregated.append(a)
    return processed_aggregated


def find_regions_of_interest(
    aggregated_data: List[AggregatedView], total_num_annotators: int
) -> List[RegionOfInterest]:
    regions: List[RegionOfInterest] = []
    for agg_view in aggregated_data:
        last_frame = None

        sections = []
        section = {}
        for f, n in sorted(agg_view.frame_votes.items()):
            if not last_frame:
                last_frame = f - 1
            if f - 1 != last_frame:
                sections.append(section)
                section = {f: n}
                last_frame = f
            else:
                section[f] = n
                last_frame = f
        sections.append(section)

        for idx, s in enumerate(sections):
            frame_vote_counts = {f: len(votes) for f, votes in s.items()}
            region = RegionOfInterest(
                answer=agg_view.answer,
                frame_votes=s,
                frame_vote_counts=frame_vote_counts,
                region_number=idx,
            )
            region.consensus_data = ConsensusData(
                max_agreement=max(frame_vote_counts.values()),
                integrated_agreement_score=calculate_integrated_agreement_score(region, total_num_annotators),
                min_n_agreement=calculate_region_frame_level_min_n_agreement(region),
                n_scores=calculate_n_scores(region),
            )
            regions.append(region)
    return regions


def calculate_integrated_agreement_score(region: RegionOfInterest, total_num_annotators: int) -> float:
    frame_vote_counts = region.frame_vote_counts
    num_frames = 1 + max(frame_vote_counts.keys()) - min(frame_vote_counts.keys())
    return round(sum(frame_vote_counts.values()) / (total_num_annotators * num_frames), 4)


def process_vote_counts(number_of_annotators_agreeing) -> Dict[int, int]:
    max_number_of_annotators_agreeing = max(number_of_annotators_agreeing, default=0)
    agreements_count_exact = [0] * (max_number_of_annotators_agreeing + 1)
    for annotators_amount, agreement_count in Counter(number_of_annotators_agreeing).items():
        agreements_count_exact[annotators_amount] = agreement_count
    agreement_count_ge = list(reversed(list(itertools.accumulate(reversed(agreements_count_exact)))))

    return {
        annotators_amount: agreement_count_ge
        for annotators_amount, agreement_count_ge in enumerate(agreement_count_ge, start=1)
    }


def calculate_frame_level_min_n_agreement(
    aggregated_data: List[AggregatedView],
) -> Dict[int, int]:
    number_of_annotators_agreeing = []
    for agg_view in aggregated_data:
        number_of_annotators_agreeing.extend([len(v) for v in agg_view.frame_votes.values()])
    return process_vote_counts(number_of_annotators_agreeing)


def calculate_region_frame_level_min_n_agreement(
    region: RegionOfInterest,
) -> Dict[int, int]:
    return process_vote_counts(list(region.frame_vote_counts.values()))


def calculate_n_scores(region: RegionOfInterest) -> Dict[int, float]:
    frame_level_min_n_agreement = calculate_region_frame_level_min_n_agreement(region)
    n_scores = {}
    total_num_annotators = max(frame_level_min_n_agreement.keys())
    for n in range(2, total_num_annotators + 1):
        n_scores[n] = round(frame_level_min_n_agreement[n] / frame_level_min_n_agreement[1], 4)
    return n_scores
