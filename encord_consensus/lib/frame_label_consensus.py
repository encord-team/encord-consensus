def calculate_frame_level_agreement(prepared_data, min_agreement=0):
    res = {}
    already_computed = set()
    for label_hash, frame_view in prepared_data.items():
        for fq_name, frames in frame_view.items():
            if fq_name not in already_computed:
                already_computed.add(fq_name)
                all_frames = []
                for fv in prepared_data.values():
                    all_frames.extend(fv.get(fq_name, []))
                data = {f: all_frames.count(f) for f in set(all_frames) if all_frames.count(f) >= min_agreement}
                if data:
                    res[fq_name] = data
    return res


def find_regions_of_interest(frame_level_agreement_data):
    regions = {}
    for fq_name, data in frame_level_agreement_data.items():
        last_frame = list(data.keys())[0] - 1

        sections = []
        section = {}
        for f, n in data.items():
            if f - 1 != last_frame:
                sections.append(section)
                section = {f: n}
                last_frame = f
            else:
                section[f] = n
                last_frame = f
        sections.append(section)

        for idx, s in enumerate(sections):
            regions[f'{fq_name}@{idx}'] = {'data': s, 'max_agreement': max(s.values())}
    return regions


def calculate_agreement_in_region(region_data, total_num_annnotators):
    num_frames = 1 + max(region_data.keys()) - min(region_data.keys())
    return sum(region_data.values()) / (total_num_annnotators * num_frames)


def process_votes(number_of_annotators_agreeing):
    max_number_of_annotators_agreeing = max(number_of_annotators_agreeing)
    exact_num_agreed = {
        num_agreed: number_of_annotators_agreeing.count(num_agreed)
        for num_agreed in set(number_of_annotators_agreeing)
    }
    return {
        n: sum([
            exact_num_agreed[num_agreed] for num_agreed in range(n, max_number_of_annotators_agreeing + 1)
        ])
        for n in exact_num_agreed.keys()
    }


def calculate_frame_level_integrated_agreement(frame_level_agreement_data):
    number_of_annotators_agreeing = []
    for fl_agreement in frame_level_agreement_data.values():
        number_of_annotators_agreeing.extend([v for v in fl_agreement.values()])
    return process_votes(number_of_annotators_agreeing)


def calculate_region_frame_level_integrated_agreement(region):
    return process_votes(list(region.values()))
