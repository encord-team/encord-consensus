from collections import defaultdict
from typing import List, Dict, DefaultDict

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


class RegionOfInterest(BaseModel):
    answer: Answer
    frame_votes: Dict[int, List[str]] = Field(allow_mutation=False)
    frame_vote_counts: Dict[int, int] = Field(allow_mutation=False)
    max_agreement: int
    region_number: int
    score: float | None = None

    def __hash__(self) -> int:
        return hash(hash(self.answer) + self.region_number)
