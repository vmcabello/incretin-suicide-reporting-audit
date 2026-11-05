"""Reproduce documentary classification with cumulative access gaps.

Only the Python standard library is needed. No clinical effect model is fit.
The primary population is defined by entry criteria, without historical priority.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json

COMPONENTS = ('suicidal_ideation', 'suicide_attempt', 'suicide_death')
STAGES = ('A', 'B1', 'B2', 'B3')
KEY = ('unit_id', 'component', 'stage', 'modality', 'reference_id', 'window_id')
PRIMARY_STRATUM = 'entire_population_eligible_by_entry_criteria'
SUBPOPULATION_STRATUM = 'eligible_subpopulation_admission'
CONTENT_UNKNOWN = {'pending_decision', 'public_source_unavailable', 'reference_unverifiable'}
RULE = 'v3.1-cumulative-access-uniform-primary-20261101'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                   indent=2, allow_nan=False) + '\n', encoding='utf-8')


def valid_complete(row, allow_derivations=True):
    eligible = (row['status'] == 'complete_direct' or
                (allow_derivations and row['status'] == 'complete_derived'))
    return (eligible and not row['unresolved_conflict_hold'] and
            row.get('complete_fixed_reference_verified') is True and
            row.get('both_eligible_arms_reconstructed') is True and
            (row['status'] != 'complete_derived' or row.get('derivation_validated') is True))


def indicator(rows, allow_derivations=True):
    """A partial later source cannot cancel an unresolved earlier source gap.

    A valid complete witness is existential, so it precedes unrelated unknowns.
    The cumulative gap IDs are explicitly materialized and frozen in each row;
    they do not rewrite the source-scoped observation in ``status``.
    """
    if not rows:
        return None
    if any(valid_complete(row, allow_derivations) for row in rows):
        return 1
    if any(row['unresolved_conflict_hold'] or row['status'] in CONTENT_UNKNOWN or
           row.get('cumulative_unresolved_gap_ids') or
           row.get('analysis_scope_closed_for_this_position') is not True or
           row.get('unexamined_relevant_source_ids') or
           row.get('source_available_not_yet_assessed') for row in rows):
        return None
    # A nominal complete classification whose proof fails is not incompleteness.
    if any(row['status'] == 'complete_direct' or
           (allow_derivations and row['status'] == 'complete_derived') for row in rows):
        return None
    return 0


def summarize(values):
    n = len(values)
    k = sum(value == 1 for value in values)
    u = sum(value is None for value in values)
    return {'N': n, 'complete': k, 'not_complete_in_examined_scope': n-k-u,
            'unknown': u, 'logical_bounds': [k/n, (k+u)/n] if n else None,
            'bounds_are_not_confidence_intervals_or_clinical_risks': True,
            'no_point_estimate_imputed_for_unknowns': True}


def primary_ids(popmap):
    """No admission date or historical decision enters the primary rule."""
    return sorted(row['unit_id'] for row in popmap['records']
                  if row['designed_eligibility_stratum'] == PRIMARY_STRATUM)


def resolution_has_evidence(gap):
    """Closing an access gap requires a locatable, positively supported decision."""
    evidence = gap.get('resolution_evidence') or []
    return (bool(gap.get('resolution_reason')) and bool(evidence) and
            all(isinstance(item, dict) and item.get('source_id') and
                item.get('locator') and isinstance(item.get('sha256'), str) and
                len(item['sha256']) == 64 for item in evidence))


def assert_structure(data, popmap, gapledger):
    ids = [unit['unit_id'] for unit in data['units']]
    assert len(ids) == len(set(ids))
    assert len(data['assessments']) == 28*len(ids)
    expected = {tuple(row[key] for key in KEY)
                for row in data['expected_modality_plan']['cells']}
    actual = {tuple(row[key] for key in KEY) for row in data['assessments']}
    assert expected == actual and len(actual) == len(data['assessments'])
    assert {row['unit_id'] for row in popmap['records']} == set(ids)
    gaps = {row['gap_id']: row for row in gapledger['gaps']}
    assert len(gaps) == len(gapledger['gaps'])
    for row in data['assessments']:
        for gap_id in row.get('cumulative_unresolved_gap_ids', []):
            gap = gaps[gap_id]
            assert gap['unit_id'] == row['unit_id']
            assert row['component'] in gap['components']
            assert row['modality'] in gap['modalities']
            assert row['stage'] in gap['unresolved_stages']
            assert not gap.get('resolved', False)
    # Every declared unresolved relevant gap must enter every applicable row.
    for gap in gaps.values():
        if gap.get('resolved', False):
            assert resolution_has_evidence(gap), 'Resolution needs positive, locatable evidence'
            continue
        for row in data['assessments']:
            if (row['unit_id'] == gap['unit_id'] and row['component'] in gap['components']
                    and row['modality'] in gap['modalities']
                    and row['stage'] in gap['unresolved_stages']):
                assert gap['gap_id'] in row.get('cumulative_unresolved_gap_ids', [])
    return ids


def analyse(data, popmap, residual, gapledger):
    ids = assert_structure(data, popmap, gapledger)
    strata = {row['unit_id']: row['designed_eligibility_stratum'] for row in popmap['records']}
    primary = primary_ids(popmap)
    supported = sorted(uid for uid in ids if strata[uid] in
                       {PRIMARY_STRATUM, SUBPOPULATION_STRATUM})
    groups = collections.defaultdict(list)
    for row in data['assessments']:
        groups[(row['unit_id'], row['component'], row['stage'])].append(row)
    values = {(component, stage): {uid: indicator(groups[(uid, component, stage)])
              for uid in ids} for component in COMPONENTS for stage in STAGES}

    def family(roster):
        return {component+'::'+stage: summarize([values[(component, stage)][uid]
                for uid in roster]) for component in COMPONENTS for stage in STAGES}

    main = family(primary)
    operational = family(ids)
    bystratum = {}
    for stratum in sorted(set(strata.values())):
        subset = [uid for uid in ids if strata[uid] == stratum]
        for key, value in family(subset).items():
            bystratum[key+'::'+stratum] = value
    modalities = []
    paired = []
    sensitivities = {}
    position_results = []
    for row in data['assessments']:
        position_results.append({**{key: row[key] for key in KEY},
            'source_scoped_status': row['status'],
            'cumulative_unresolved_gap_ids': row.get('cumulative_unresolved_gap_ids', []),
            'effective_modality_indicator': indicator([row])})
    for label, roster in [('primary_whole_population', primary),
                          ('complementary_operational', ids)]:
        for component in COMPONENTS:
            for stage in STAGES:
                modality_names = next(row['modalities']
                    for row in data['expected_modality_plan']['catalog']
                    if row['component'] == component and row['stage'] == stage)
                for modality in modality_names:
                    vals = [indicator([row for row in groups[(uid, component, stage)]
                                       if row['modality'] == modality]) for uid in roster]
                    modalities.append({'analysis_set': label, 'component': component,
                        'stage': stage, 'modality': modality, **summarize(vals)})
            for left, right in zip(STAGES, STAGES[1:]):
                pairs = [(values[(component, left)][uid], values[(component, right)][uid])
                         for uid in roster]
                known = [pair for pair in pairs if None not in pair]
                freq = collections.Counter(known)
                paired.append({'analysis_set': label, 'component': component,
                    'left': left, 'right': right, 'N': len(roster),
                    'paired_resolved': len(known), 'paired_unknown': len(pairs)-len(known),
                    'n00': freq[(0, 0)], 'n01': freq[(0, 1)],
                    'n10': freq[(1, 0)], 'n11': freq[(1, 1)], 'no_inferential_test': True})
            sensitivities[label+'::'+component+'::without_any_derived_completeness'] = summarize(
                [indicator(groups[(uid, component, 'B3')], allow_derivations=False)
                 for uid in roster])
    # The enlarged set uses the same positive population rule for all units.
    # Parent outcomes are never assigned to an eligible subgroup by assumption.
    enlarged = family(supported)
    selection = {'operational_retained_units': len(ids), 'primary_units': len(primary),
        'population_supported_including_subpopulations': len(supported),
        'population_not_established_operational_only': len(ids)-len(supported),
        'membership_unknown_candidate_blocks': len(residual['unknown_records']),
        'dependent_block': 1, 'identity_unresolved_blocks': 2,
        'original_candidate_blocks': 220}
    assert sum(selection[key] for key in ['operational_retained_units',
        'membership_unknown_candidate_blocks', 'dependent_block',
        'identity_unresolved_blocks']) == selection['original_candidate_blocks']
    return {'analysis': 'documentary_reconstructibility_with_cumulative_unknowns',
        'rule_version': RULE, 'main': main,
        'complementary_operational': operational,
        'complementary_supported_population_including_subgroups': enlarged,
        'population_strata': bystratum, 'modality_results': modalities,
        'paired_source_changes': paired, 'sensitivities': sensitivities,
        'selection': selection, 'primary_unit_ids': primary,
        'primary_rule_uses_historical_admission': False,
        'primary_hierarchy_changed_after_expert_feedback_and_results_known': True,
        'stratum_roster_counts': dict(collections.Counter(strata.values())),
        'effective_position_indicators': position_results,
        'clinical_effect_estimates_computed': False,
        'GRADE_not_a_result_of_this_documentary_analysis': True,
        'source_reason_prevalence_not_estimated_from_targeted_bundles': True,
        'unknown_source_content_is_not_clinical_zero': True}


def selftest():
    count = 0
    def check(actual, expected):
        nonlocal count
        assert actual == expected, (actual, expected)
        count += 1
    def row(status, **kw):
        return {'status': status, 'unresolved_conflict_hold': False,
            'complete_fixed_reference_verified': True, 'both_eligible_arms_reconstructed': True,
            'derivation_validated': True, 'analysis_scope_closed_for_this_position': True,
            'cumulative_unresolved_gap_ids': [], **kw}
    check(indicator([row('public_source_unavailable')]), None)
    check(indicator([row('reference_unverifiable')]), None)
    check(indicator([row('pending_decision')]), None)
    check(indicator([row('partial_reference')]), 0)
    check(indicator([row('not_reconstructible_in_examined_corpus')]), 0)
    check(indicator([row('complete_direct'), row('public_source_unavailable')]), 1)
    check(indicator([row('complete_derived')]), 1)
    check(indicator([row('complete_derived')], allow_derivations=False), 0)
    check(indicator([row('complete_direct', unresolved_conflict_hold=True)]), None)
    check(indicator([row('complete_direct'), row('partial_reference', unresolved_conflict_hold=True)]), 1)
    check(summarize([1, 0, None, None])['logical_bounds'], [.25, .75])
    check(summarize([])['logical_bounds'], None)
    check(summarize([None, None])['logical_bounds'], [0, 1])
    check(summarize([0, 0])['logical_bounds'], [0, 0])
    check(summarize([1, 1])['logical_bounds'], [1, 1])
    check(indicator([row('partial_reference', analysis_scope_closed_for_this_position=False)]), None)
    check(indicator([row('complete_direct', both_eligible_arms_reconstructed=False)]), None)
    check(indicator([]), None)
    # These regression cases would fail under the old aggregation rule.
    check(indicator([row('partial_reference', cumulative_unresolved_gap_ids=['A_MAIN'])]), None)
    check(indicator([row('not_reconstructible_in_examined_corpus',
                        cumulative_unresolved_gap_ids=['A_SUPP'])]), None)
    check(indicator([row('partial_reference', cumulative_unresolved_gap_ids=['A_MAIN']),
                     row('complete_direct')]), 1)
    check(indicator([row('complete_derived', cumulative_unresolved_gap_ids=['A_MAIN'])]), 1)
    check(indicator([row('complete_derived', cumulative_unresolved_gap_ids=['A_MAIN'])],
                    allow_derivations=False), None)
    check(indicator([row('partial_reference', source_available_not_yet_assessed=True)]), None)
    check(indicator([row('partial_reference', unexamined_relevant_source_ids=['SUPP'])]), None)
    check(indicator([row('complete_direct', complete_fixed_reference_verified=False),
                     row('partial_reference')]), None)
    check(indicator([row('complete_derived', derivation_validated=False)]), None)
    check(indicator([row('partial_reference', cumulative_unresolved_gap_ids=[])]), 0)
    check(primary_ids({'records': [
        {'unit_id': 'OLD', 'designed_eligibility_stratum': 'not_established',
         'historical_admission_preserved': True},
        {'unit_id': 'NEW', 'designed_eligibility_stratum': PRIMARY_STRATUM,
         'historical_admission_preserved': False}]}), ['NEW'])
    check(primary_ids({'records': [
        {'unit_id': 'SUBGROUP', 'designed_eligibility_stratum': SUBPOPULATION_STRATUM}]}), [])
    check(resolution_has_evidence({'resolved': True}), False)
    check(resolution_has_evidence({'resolved': True, 'resolution_reason': 'registry is partial',
                                   'resolution_evidence': []}), False)
    check(resolution_has_evidence({'resolved': True, 'resolution_reason': 'same report recovered and read',
        'resolution_evidence': [{'source_id': 'SYNTHETIC', 'sha256': '0'*64, 'locator': 'Methods p2'}]}), True)
    check(resolution_has_evidence({'resolved': True, 'resolution_reason': 'unsupported wording',
        'resolution_evidence': [{'source_id': 'SYNTHETIC', 'sha256': '0'*64}]}), False)
    return {'passed': True, 'tests': count, 'real_data_analysed': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--data', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.selftest:
        print(json.dumps(selftest()))
        return
    assert args.data and args.out
    cert = load(args.data/'FREEZE_FINAL_20261101.json')
    for name, digest in cert['data_file_hashes'].items():
        assert sha(args.data/name) == digest, 'Frozen file changed: '+name
    assert sha(__file__) == cert['analysis_code_sha256'], 'Analysis code changed'
    data = load(args.data/'documental_entrada_final.json')
    assert data['analytical_release'] is True
    result = analyse(data, load(args.data/'populacoes_final.json'),
        load(args.data/'selecao_residual_final.json'), load(args.data/'lacunas_cumulativas.json'))
    result['frozen_input_sha256'] = sha(args.data/'documental_entrada_final.json')
    result['analysis_code_sha256'] = sha(__file__)
    result['frozen_data_file_hashes'] = cert['data_file_hashes']
    write(args.out, result)
    print(json.dumps({'output': str(args.out), 'primary_N': result['selection']['primary_units'],
                      'operational_N': result['selection']['operational_retained_units'],
                      'clinical_models': False}))


if __name__ == '__main__':
    main()
