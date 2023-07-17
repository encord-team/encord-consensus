from collections import defaultdict


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


def prepare_data_for_consensus(ontology, lr_data):
    out = {}
    for label_hash, lr in lr_data.items():
        res = defaultdict(list)
        lookup = {}
        for frame, labels in lr['data_units'][lr['data_hash']]['labels'].items():
            for cl in labels['classifications']:
                if not lookup.get(cl['classificationHash']):
                    fq_parts = []
                    for classification in lr['classification_answers'][cl['classificationHash']]['classifications']:
                        fq_parts.append((f"{classification['value']}={classification['answers'][0]['value']}",
                                         classification['featureHash']))
                    fq_parts = sorted(fq_parts,
                                      key=lambda x: get_precedence(ontology, cl['featureHash'], x[1]))
                    lookup[cl['classificationHash']] = '&'.join([x[0] for x in fq_parts])
                fq_name = lookup.get(cl['classificationHash'])
                res[fq_name].append(int(frame))
        out[label_hash] = res
    return out
