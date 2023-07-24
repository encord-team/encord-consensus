from collections import defaultdict
from typing import Dict, DefaultDict, List

from .data_model import Answer, ClassificationView, FQPart


def get_precedence(ontology, feature_hash, answer_hash):
    attributes = [x for x in ontology if x['featureNodeHash'] == feature_hash]
    assert len(attributes) == 1
    attributes = attributes[0]

    def recurse(subtree, answer_hash, res=set()):
        if subtree['featureNodeHash'] == answer_hash:
            return res.union({subtree['id']})
        else:
            if 'options' not in subtree:
                return res.union({None})
        local_r = []
        for opt in subtree['options']:
            local_r.append(recurse(opt, answer_hash, res))
        return set().union(*local_r)

    explored_r = recurse(attributes['attributes'][0], answer_hash)
    explored_r.discard(None)
    return int(''.join(explored_r.pop().split('.')))


def prepare_data_for_consensus(ontology, lr_data) -> List[ClassificationView]:
    out = []
    for project_hash, lr in lr_data.items():
        lookup: Dict[str, Answer] = {}
        res: DefaultDict[Answer, list[int]] = defaultdict(list[int])

        for frame, labels in lr['data_units'][lr['data_hash']]['labels'].items():
            for cl in labels['classifications']:
                if not lookup.get(cl['classificationHash']):
                    fq_parts = []
                    for classification in lr['classification_answers'][cl['classificationHash']]['classifications']:
                        fq_parts.append(
                            FQPart(
                                question=classification['value'],
                                answer=classification['answers'][0]['value'],
                                fq_part=f"{classification['value']}={classification['answers'][0]['value']}",
                                feature_hash=classification['featureHash']
                            )
                        )
                    sorted_fq_parts = sorted(
                        fq_parts,
                        key=lambda x: get_precedence(ontology, cl['featureHash'], x.feature_hash)
                    )
                    fq_name = '&'.join([x.fq_part for x in sorted_fq_parts])
                    lookup[cl['classificationHash']] = Answer(fq_name=fq_name, fq_parts=sorted_fq_parts)
                answer = lookup[cl['classificationHash']]
                res[answer].append(int(frame))
        out.extend([ClassificationView(answer=kv[0], frames=kv[1], source_project_hash=project_hash) for kv in res.items()])
    return out
