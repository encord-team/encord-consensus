from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple

from pydantic import BaseModel, Field


class FQPart(BaseModel):
    question: str
    answer: str
    fq_part: str
    feature_hash: str


class Answer(BaseModel):
    classification_answers: Dict
    name: str
    value: str
    feature_hash: str
    fq_name: str
    fq_parts: List[FQPart]

    def __hash__(self) -> int:
        return hash(self.fq_name)

    def __eq__(self, other):
        return self.fq_name == other.fq_name


class ClassificationView(BaseModel):
    answer: Answer
    frames: List[int]
    source_project_hash: str

    def __hash__(self) -> int:
        return hash(self.source_project_hash + self.answer.fq_name)


class AggregatedView(BaseModel):
    answer: Answer
    frame_votes: DefaultDict[int, List[str]] = defaultdict(list)


class ConsensusData(BaseModel):
    max_agreement: int
    integrated_agreement_score: float
    min_n_agreement: Dict[int, int]
    n_scores: Dict[int, float] | None = None


class RegionOfInterest(BaseModel):
    answer: Answer
    frame_votes: Dict[int, List[str]] = Field(allow_mutation=False)
    frame_vote_counts: Dict[int, int] = Field(allow_mutation=False)
    region_number: int
    consensus_data: ConsensusData | None = None

    def __hash__(self) -> int:
        return hash(hash(self.answer) + self.region_number)

    @property
    def ranges_by_source(self) -> DefaultDict[str, List[Tuple[int, int]]]:
        res = defaultdict(list)
        start_frame_by_source = {}
        for frame, votes in self.frame_votes.items():
            for source in votes:
                if source not in start_frame_by_source:
                    start_frame_by_source[source] = frame
                if source not in self.frame_votes.get(frame + 1, []):
                    res[source].append((start_frame_by_source.get(source, frame), frame))
                    del start_frame_by_source[source]
        return res
