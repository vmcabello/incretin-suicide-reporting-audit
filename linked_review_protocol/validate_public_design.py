"""Replay the public 109-position follow-up design; no private data or votes.

This checks selection keys, allocation and inclusion probabilities, not whether
any assessor examined a source, independence, scientific accuracy or review
completion. Python standard library only. No files are written.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
import math

KEY = ('unit_id', 'component', 'stage', 'modality', 'reference_id', 'window_id')
PHASE1_SEED = 'EJCP-P4-20261104-VALIDATION-v1'
COMPLETE = {'complete_direct', 'complete_derived'}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def key(row):
    return '|'.join(row[k] for k in KEY)


def allocation(strata, total):
    """One per stratum, then exact proportional largest remainder of n_h-1."""
    assert strata and all(rows for rows in strata.values())
    assert len(strata) <= total <= sum(len(rows) for rows in strata.values())
    capacities = {s:len(rows)-1 for s,rows in strata.items()}
    extra = total-len(strata)
    capacity = sum(capacities.values())
    quotas = {s:Fraction(extra*c,capacity) if capacity else Fraction(0) for s,c in capacities.items()}
    allocated = {s:1+q.numerator//q.denominator for s,q in quotas.items()}
    remainder = total-sum(allocated.values())
    priority = sorted(strata, key=lambda s: (-(quotas[s]-(allocated[s]-1)),s))
    for s in priority[:remainder]:
        allocated[s] += 1
    assert sum(allocated.values()) == total
    assert all(1 <= allocated[s] <= len(strata[s]) for s in strata)
    return allocated


def selftest():
    count = 0
    def check(actual, expected):
        nonlocal count
        assert actual == expected, (actual,expected)
        count += 1
    check(allocation({'a':[0], 'b':[0,1,2,3]},3), {'a':1,'b':2})
    check(allocation({'b':[0,1], 'a':[0,1]},3), {'b':1,'a':2})
    check(allocation({'a':[0,1,2], 'b':[0,1,2]},6), {'a':3,'b':3})
    check(allocation({'a':[0], 'b':[0]},2), {'a':1,'b':1})
    return count


def validate(repository):
    repository = Path(repository).resolve()
    here = repository/'linked_review_protocol'
    protocol = load(here/'PROTOCOL.json')
    serial = load(here/'PUBLIC_PROTOCOL_SERIALIZATION.json')
    roster_data = load(here/'SELECTION_ROSTER.json')
    distributed = roster_data['rows']
    original_protocol_hash = serial['original_fixed_protocol_sha256']
    assert roster_data['protocol_sha256'] == original_protocol_hash
    assert hashlib.sha256((here/'PROTOCOL.json').read_bytes()).hexdigest() == serial['public_protocol_LF_sha256']
    assert serial['protocol_sha256_fields_refer_to_original_fixed_protocol_bytes'] is True
    assert protocol['protocol_id'] == 'EJCP-LINKED-SOURCE-109-20261105-v1'
    assert protocol['selection_not_executed_at_time_of_this_file'] is True
    assert protocol['primary_results_changed'] is False and protocol['human_answers_filled'] is False

    spec = importlib.util.spec_from_file_location('linked_design_legacy', repository/'input_snapshot/codigo/analise_final.py')
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    rows = load(repository/'current_input/documental_entrada_reconciliada.json')['assessments']
    by_key = {key(row):row for row in rows}
    assert len(by_key) == len(rows) == 5096
    values = {k:legacy.indicator([row]) for k,row in by_key.items()}
    assert collections.Counter(values.values()) == {0:4030,None:1009,1:57}

    # Reconstruct the original 4,030-position frame independently of availability.
    negative_frame = collections.defaultdict(list)
    for k,row in by_key.items():
        if values[k] == 0:
            dimensions = (row['component'],row['modality'],row['stage'],row['status'])
            negative_frame[dimensions].append(k)
    assert len(negative_frame) == protocol['phase_1_negative_frame']['strata'] == 56
    phase1 = {}
    strata = {}
    for dimensions, keys in negative_frame.items():
        sid = 'STR-'+digest('|'.join(dimensions))[:12]
        n_h = math.ceil(.1*len(keys))
        chosen = sorted(keys,key=lambda k:(digest(PHASE1_SEED+'|'+k),k))[:n_h]
        assert sid not in strata
        strata[sid] = chosen
        for k in chosen:
            phase1[k] = {'stratum_id':sid,'N_h':len(keys),'n_h':n_h}
    assert len(phase1) == protocol['phase_1_negative_frame']['n'] == 426
    assert sum(len(keys) for keys in negative_frame.values()) == protocol['phase_1_negative_frame']['N'] == 4030
    earlier = load(repository/'validation_protocol/SAMPLING_ROSTER.json')['records']
    earlier_negative = {key(row):row for row in earlier if row['design_group']=='retained_probability_sample_not_complete'}
    assert set(earlier_negative) == set(phase1)
    for k,expected in phase1.items():
        got = earlier_negative[k]
        assert got['position_id'] == 'POS-'+digest(k)[:20]
        assert all(got[field] == value for field,value in expected.items())
        assert got['selection_probability'] == expected['n_h']/expected['N_h']

    # Independently calculate the phase-2 allocation using exact rational quotas.
    total = protocol['phase_2_negative_sample']['n']
    assert total == 72
    m = allocation(strata,total)
    declared_alloc = {row['stratum_id']:row for row in protocol['allocation']}
    assert set(declared_alloc) == set(strata) and len(declared_alloc) == len(protocol['allocation'])
    for sid,keys in strata.items():
        first = phase1[keys[0]]
        assert declared_alloc[sid] == {'stratum_id':sid,'N_h':first['N_h'],'n_h':first['n_h'],'m_h':m[sid]}
    seed = protocol['phase_2_negative_sample']['seed']
    assert seed == 'EJCP-LINKED-SOURCE-PHASE2-NEGATIVE72-20261105-v1'
    selected_negative = {}
    for sid, keys in strata.items():
        chosen = sorted(keys,key=lambda k:(digest(seed+'|'+k),k))[:m[sid]]
        for k in chosen:
            first = phase1[k]
            n_h,N_h,m_h = first['n_h'],first['N_h'],m[sid]
            selected_negative[k] = {**first,'m_h':m_h,
                'phase1_probability':n_h/N_h,'phase2_probability':m_h/n_h,
                'composed_probability':m_h/N_h,'weight':N_h/m_h,
                'selection_hash':digest(seed+'|'+k)}

    # The mandatory census is derived from the locked public paired labels.
    paired = load(repository/'validation/PAIRED_RATINGS_663.json')['rows']
    historical_positive = {k for k,v in values.items() if v==1}
    positive_pairs = {key(row):row for row in paired if key(row) in historical_positive}
    assert set(positive_pairs) == historical_positive and len(positive_pairs) == 57
    expected_positive = {k for k,row in positive_pairs.items()
                         if not all(row[reviewer]['cumulative_classification'] in COMPLETE for reviewer in ('R1','R2'))}
    assert len(expected_positive) == 37
    assert len({by_key[k]['unit_id'] for k in expected_positive}) == 13
    for k in expected_positive:
        assert positive_pairs[k]['R1']['cumulative_classification'] == positive_pairs[k]['R2']['cumulative_classification']
        assert positive_pairs[k]['R1']['cumulative_classification'] in {'reference_unverifiable','public_source_unavailable','pending_decision'}

    got = {key(row):row for row in distributed}
    assert len(got) == len(distributed) == 109
    assert len({row['position_id'] for row in distributed}) == 109
    got_negative = {k:row for k,row in got.items() if row['design_group']=='phase2_original_negative_probability_sample'}
    got_positive = {k:row for k,row in got.items() if row['design_group']=='census_pending_source_confirmation'}
    assert set(got_negative) == set(selected_negative) and len(got_negative) == 72
    assert set(got_positive) == expected_positive
    assert set(got) == set(selected_negative)|expected_positive
    for k,expected in selected_negative.items():
        row = got_negative[k]
        assert row['position_id'] == 'POS-'+digest(k)[:20]
        assert all(row[field] == value for field,value in expected.items()),k
    for k,row in got_positive.items():
        assert row['position_id'] == 'POS-'+digest(k)[:20]
        assert row['stratum_id'] is None and row['selection_hash'] is None
        assert all(row[field] == 37 for field in ('N_h','n_h','m_h'))
        assert all(row[field] == 1.0 for field in ('phase1_probability','phase2_probability','composed_probability','weight'))
    assert len({row['stratum_id'] for row in got_negative.values()}) == 56
    assert len({row['unit_id'] for row in distributed}) == 59
    assert collections.Counter(row['stratum_id'] for row in got_negative.values()) == m

    with (here/'SELECTION_ROSTER.csv').open(encoding='utf-8-sig',newline='') as handle:
        tabular = list(csv.DictReader(handle))
    assert len(tabular) == len(distributed)
    assert [row['position_id'] for row in tabular] == [row['position_id'] for row in distributed]
    for tab,row in zip(tabular,distributed):
        assert all(tab[k] == row[k] for k in KEY)
        for field in ('N_h','n_h','m_h'):
            assert int(tab[field]) == row[field]
        for field in ('phase1_probability','phase2_probability','composed_probability','weight'):
            assert float(tab[field]) == row[field]
        assert tab['stratum_id'] == (row['stratum_id'] or '')
        assert tab['selection_hash'] == (row['selection_hash'] or '')
    return {'status':'PASS','public_design_fully_replayed':True,
        'historical_negative_frame':4030,'phase1_sample_keys_replayed':426,
        'phase2_sample_keys_replayed':72,'strata_replayed':56,
        'mandatory_currently_indeterminate_positive_keys_replayed':37,
        'total_positions':109,'units':59,'largest_remainder_allocation_exact_rational':True,
        'position_keys_probabilities_and_weights_match':True,'csv_projection_matches':True,
        'synthetic_allocation_tests':selftest(),'private_inputs_used':False,
        'human_reviews_completed_or_certified':False,'scientific_accuracy_validated':False,
        'note':'Public selection/probability replay only. Original protocol timing is declared metadata; the fixed original byte hash is distinguished from the LF public serialization. This does not establish source reading, review independence or scientific validity.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',type=Path,default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    print(json.dumps(validate(args.repository),ensure_ascii=False,sort_keys=True,indent=2))
