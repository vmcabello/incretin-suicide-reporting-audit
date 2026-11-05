"""Positive-only sensitivity linked to the source-limited human reassessment.

Standard-library-only, deterministic, descriptive. This scenario is not an
adjudication and does not replace the primary historical classifications.
Run --selftest or --repository PUBLIC_REPOSITORY --out OUTPUT_DIRECTORY.
"""
from pathlib import Path
import argparse
import collections
import copy
import csv
import hashlib
import importlib.util
import json

KEY = ('unit_id', 'component', 'stage', 'modality', 'reference_id', 'window_id')
COMPLETE = {'complete_direct', 'complete_derived'}
UNKNOWN = {'public_source_unavailable', 'reference_unverifiable', 'pending_decision'}
SCHEMA = 'positive-only-source-limited-human-reassessment-sensitivity-v1'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(row):
    return tuple(row[k] for k in KEY)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True,
                               indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                             if isinstance(v, (dict, list)) else v for k, v in row.items() if k in fields})


def import_script(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_scenario(data, paired, reconciliation, legacy):
    """Change only exact historical positive keys; never infer human corrections."""
    scenario = copy.deepcopy(data)
    original = {key(row): row for row in data['assessments']}
    assert len(original) == len(data['assessments'])
    paired_by_key = {key(row): row for row in paired['rows']}
    technical_by_key = {key(row): row for row in reconciliation['rows']}
    historical_complete = {k for k, row in original.items() if legacy.valid_complete(row)}
    assert historical_complete == set(technical_by_key), 'Complete-census bridge does not match historical positives'
    positive_bridge = []
    modified = set()
    for row in scenario['assessments']:
        k = key(row)
        if k not in historical_complete:
            continue
        pair = paired_by_key[k]
        tech = technical_by_key[k]
        labels = [pair[reviewer]['cumulative_classification'] for reviewer in ('R1', 'R2')]
        assert labels[0] == labels[1], 'This scenario requires concordant paired current labels'
        assert tech['raw_cumulative_classification'] == {'R1': labels[0], 'R2': labels[1]}
        current_label = labels[0]
        before = copy.deepcopy(row)
        if current_label in COMPLETE:
            assert current_label == row['status'], 'Complete type changed; adjudication would be required'
            disposition = 'historical_positive_currently_confirmed_in_source_limited_human_reassessment'
        else:
            assert current_label in UNKNOWN, 'A new non-unknown decision requires separate adjudication'
            # Proof flags and historical witness records remain immutable data,
            # but the scenario status is indeterminate so they cannot count complete.
            row['status'] = current_label
            modified.add(k)
            disposition = 'historical_positive_not_currently_confirmed_set_unknown_in_this_scenario_only'
        historical_technical = tech['technical_reconciliation']
        positive_bridge.append({
            **{field: row[field] for field in KEY},
            'position_id': pair['position_id'],
            'historical_status': before['status'],
            'historical_effective_indicator': legacy.indicator([before]),
            'R1_source_scoped_classification': pair['R1']['source_scoped_classification'],
            'R2_source_scoped_classification': pair['R2']['source_scoped_classification'],
            'R1_cumulative_classification': labels[0],
            'R2_cumulative_classification': labels[1],
            'R1_primary_source_examined': pair['R1']['primary_source_examined'],
            'R2_primary_source_examined': pair['R2']['primary_source_examined'],
            'scenario_status': row['status'],
            'scenario_effective_indicator': legacy.indicator([row]),
            'scenario_disposition': disposition,
            'historical_technical_witness_retained_in_primary': True,
            'technical_witness_source_ids': historical_technical['sufficient_witness_source_ids_within_this_row_layer'],
            'technical_source_scopes': historical_technical['source_original_scopes'],
            'historical_technical_reconciliation_is_a_new_human_vote': False,
            'changed_in_sensitivity_only': k in modified,
        })
    assert {key(row) for row in positive_bridge} == historical_complete
    scenario_by_key = {key(row): row for row in scenario['assessments']}
    for k, before in original.items():
        after = scenario_by_key[k]
        differences = {field for field in set(before) | set(after) if before.get(field) != after.get(field)}
        assert differences == ({'status'} if k in modified else set()), 'Unintended scenario change'
    return scenario, sorted(positive_bridge, key=key), modified


def summarize(data, pop, legacy):
    ids = sorted(row['unit_id'] for row in data['units'])
    strata = {row['unit_id']: row['designed_eligibility_stratum'] for row in pop['records']}
    rosters = {
        'whole_population_posthoc_exploratory': [u for u in ids if strata[u] == legacy.PRIMARY_STRATUM],
        'supported_including_subgroups_complementary': [u for u in ids if strata[u] in {legacy.PRIMARY_STRATUM, legacy.SUBPOPULATION_STRATUM}],
        'operational_historical_complementary': ids,
    }
    grouped = collections.defaultdict(list)
    for row in data['assessments']:
        grouped[(row['unit_id'], row['component'], row['stage'], row['modality'])].append(row)

    def cell(roster, component, stage, modalities, allow_derivations=True):
        direct, derived, unknown, not_complete = [], [], [], []
        for uid in roster:
            rows = [r for modality in modalities for r in grouped[(uid, component, stage, modality)]]
            value = legacy.indicator(rows, allow_derivations=allow_derivations)
            if value == 1:
                if any(r['status'] == 'complete_direct' and legacy.valid_complete(r) for r in rows):
                    direct.append(uid)
                else:
                    derived.append(uid)
            elif value is None:
                unknown.append(uid)
            else:
                not_complete.append(uid)
        n = len(roster)
        confirmed = len(direct) + len(derived)
        assert confirmed + len(unknown) + len(not_complete) == n
        return {
            'N': n, 'direct_confirmed': len(direct), 'derived_confirmed': len(derived),
            'confirmed_total': confirmed, 'unknown': len(unknown),
            'not_complete_in_examined_scope': len(not_complete),
            'corpus_conditional_identification_interval': [confirmed/n, (confirmed+len(unknown))/n] if n else None,
            'direct_unit_ids': direct, 'derived_only_unit_ids': derived, 'unknown_unit_ids': unknown,
        }

    specific, unions, direct_only, added = [], [], [], []
    for label, roster in rosters.items():
        for plan in data['expected_modality_plan']['catalog']:
            comp, stage, modalities = plan['component'], plan['stage'], plan['modalities']
            for modality in modalities:
                specific.append({'analysis_set': label, 'component': comp, 'stage': stage, 'modality': modality,
                                 **cell(roster, comp, stage, [modality])})
            unions.append({'analysis_set': label, 'component': comp, 'stage': stage,
                           'interpretation': 'secondary_union_of_non_equivalent_modalities',
                           **cell(roster, comp, stage, modalities)})
            if stage == 'B3':
                values = cell(roster, comp, stage, modalities, allow_derivations=False)
                direct_only.append({'analysis_set': label, 'component': comp, 'stage': stage,
                    'N': values['N'], 'direct_complete': values['confirmed_total'], 'unknown': values['unknown'],
                    'not_complete_in_examined_scope': values['not_complete_in_examined_scope'],
                    'corpus_conditional_identification_interval': values['corpus_conditional_identification_interval']})
    for row in unions:
        if row['analysis_set'] != 'whole_population_posthoc_exploratory' or row['stage'] != 'B3':
            continue
        for label, additional_n in [('additional_12_population_unresolved', 12), ('additional_35_membership_unknown', 35),
                                    ('additional_2_identity_unresolved', 2), ('additional_49_combined_disjoint_uncertainties', 49)]:
            n = row['N'] + additional_n
            k, u = row['confirmed_total'], row['unknown'] + additional_n
            added.append({'scenario': label, 'component': row['component'],
                'assumed_additional_distinct_fully_eligible_units': additional_n, 'N_hypothetical': n,
                'known_confirmed_carried_forward': k, 'unknown_hypothetical': u,
                'corpus_conditional_identification_interval': [k/n, (k+u)/n],
                'assumption': 'Every added block is a distinct fully eligible unit and its reconstruction status is unknown. This is not an admission decision or a bound on unlocated trials.'})
    return {'roster_sizes': {label: len(roster) for label, roster in rosters.items()},
            'modality_results': specific, 'secondary_union_results': unions,
            'without_derived_completeness': direct_only, 'illustrative_membership_scenarios': added}


def compare_tables(historical, scenario):
    result = {}
    for name in ['modality_results', 'secondary_union_results', 'without_derived_completeness', 'illustrative_membership_scenarios']:
        assert len(historical[name]) == len(scenario[name])
        rows = []
        for old, new in zip(historical[name], scenario[name]):
            identity = {k: old[k] for k in ['analysis_set', 'scenario', 'component', 'stage', 'modality'] if k in old}
            assert all(new[k] == v for k, v in identity.items())
            count_keys = ['N', 'N_hypothetical', 'confirmed_total', 'direct_complete', 'direct_confirmed', 'derived_confirmed',
                          'unknown', 'not_complete_in_examined_scope', 'known_confirmed_carried_forward', 'unknown_hypothetical',
                          'corpus_conditional_identification_interval']
            rows.append({**identity, 'historical': {k: old[k] for k in count_keys if k in old},
                         'source_limited_human_positive_only_scenario': {k: new[k] for k in count_keys if k in new},
                         'changed': old != new})
        result[name] = rows
    return result


def run(repository):
    repository = Path(repository)
    files = {
        'data': repository/'current_input/documental_entrada_reconciliada.json',
        'population': repository/'input_snapshot/dados/populacoes_final.json',
        'residual': repository/'input_snapshot/dados/selecao_residual_final.json',
        'gaps': repository/'input_snapshot/dados/lacunas_cumulativas.json',
        'legacy_analysis': repository/'input_snapshot/codigo/analise_final.py',
        'historical_modality_analysis': repository/'current_analysis/analysis_by_modality.py',
        'historical_results': repository/'current_analysis/RESULTS_BY_MODALITY.json',
        'paired_ratings': repository/'validation/PAIRED_RATINGS_663.json',
        'technical_witnesses': repository/'validation/TECHNICAL_WITNESS_RECONCILIATION_57.json',
    }
    legacy = import_script(files['legacy_analysis'], 'positive_sensitivity_legacy')
    modality = import_script(files['historical_modality_analysis'], 'positive_sensitivity_modality')
    current = load(files['data'])
    pop, paired, technical = load(files['population']), load(files['paired_ratings']), load(files['technical_witnesses'])
    # Existing code checks the original distributed analysis before this scenario.
    historical = modality.run(repository/'input_snapshot', files['data'])
    distributed = load(files['historical_results'])
    for name in ['roster_sizes', 'modality_results', 'secondary_union_results', 'without_derived_completeness', 'illustrative_membership_scenarios']:
        assert historical[name] == distributed[name], 'Published historical result did not reproduce: '+name
    alternate, bridge, modified = apply_scenario(current, paired, technical, legacy)
    legacy.assert_structure(alternate, pop, load(files['gaps']))
    scenario = summarize(alternate, pop, legacy)
    independent_historical = summarize(current, pop, legacy)
    for name in ['roster_sizes', 'modality_results', 'secondary_union_results', 'without_derived_completeness', 'illustrative_membership_scenarios']:
        assert independent_historical[name] == historical[name], 'New descriptive table differs from inherited table: '+name
    assert len(modified) == 37 and len(bridge) == 57
    assert sum(row['scenario_effective_indicator'] == 1 for row in bridge) == 20
    assert all(legacy.indicator([row]) == 1 for row in current['assessments'] if key(row) in modified)
    assert all(legacy.indicator([row]) is None for row in alternate['assessments'] if key(row) in modified)
    comparison = compare_tables(historical, scenario)
    b3 = [r for r in comparison['secondary_union_results']
          if r['analysis_set'] == 'whole_population_posthoc_exploratory' and r['stage'] == 'B3']
    assert [(r['historical']['confirmed_total'], r['historical']['unknown'],
             r['source_limited_human_positive_only_scenario']['confirmed_total'],
             r['source_limited_human_positive_only_scenario']['unknown']) for r in b3] == [(1,26,1,26),(1,26,1,26),(15,26,5,36)]
    original_by_key = {key(r): r for r in current['assessments']}
    pairs_by_key = {key(r): r for r in paired['rows']}
    all_positions = []
    for row in sorted(alternate['assessments'], key=key):
        old, pair = original_by_key[key(row)], pairs_by_key.get(key(row))
        all_positions.append({**{k: row[k] for k in KEY},
            'position_id': pair['position_id'] if pair else None,
            'historical_source_scoped_status': old['status'],
            'historical_cumulative_indicator': legacy.indicator([old]),
            'sampled_for_current_human_reassessment': pair is not None,
            'R1_source_scoped_classification': pair['R1']['source_scoped_classification'] if pair else None,
            'R2_source_scoped_classification': pair['R2']['source_scoped_classification'] if pair else None,
            'R1_cumulative_classification': pair['R1']['cumulative_classification'] if pair else None,
            'R2_cumulative_classification': pair['R2']['cumulative_classification'] if pair else None,
            'scenario_imposed_position_status': row['status'],
            'scenario_cumulative_indicator': legacy.indicator([row]),
            'changed_in_sensitivity_only': key(row) in modified,
            'not_reassessed_or_negative_sample_codes_held_fixed_by_scenario_design': key(row) not in {key(r) for r in bridge},
        })
    # All baseline units, components, layers, modalities, references and windows
    # remain present. Only a status changes; no source migration occurs.
    assert {key(r) for r in all_positions} == set(original_by_key)
    return {
        'schema': SCHEMA, 'analysis_date': '2026-11-05',
        'purpose': 'Illustrative positive-only sensitivity linking the current source-limited human reassessment to the historical primary results',
        'primary_results_replaced': False, 'human_labels_altered': False,
        'new_clinical_effects_or_inferential_confidence_intervals': False,
        'historical_reproduction_verified_before_scenario': True,
        'scenario_rule': 'Of all 57 historically valid complete position keys, retain the 20 currently concordantly complete in both human returns, and set the other 37 to the exact concordant current unknown label. All other historical position codes and all proof flags, references, windows, populations, and source records are held fixed.',
        'scope_limitations': [
            'Positive-only scenario; not a full replacement of the 663 reassessments or a corrected complete corpus.',
            'The 37 indeterminate current reassessments are not demonstrated historical errors.',
            'Current human source coverage differs from historical cumulative coverage; these are not equivalent full extractions.',
            'The 425 sampled historical negatives now unknown and one partial negative are deliberately not recoded in this scenario.',
            'No extrapolation to unreviewed negatives, unknown positions, missing trials, or an exhaustive trial universe.',
            'Intervals are corpus-conditional identification intervals, not confidence intervals, clinical risks or estimated event rates.',
            'A valid exact-target complete witness has existential priority over unrelated gaps within the same position; no backward-layer or cross-modality migration is allowed.',
            'Historical technical confirmation is not new human verification or proof of accuracy.'
        ],
        'position_counts': {'historical_complete_census': 57, 'current_human_complete_retained': 20,
                            'historical_complete_set_unknown_in_scenario': 37,
                            'all_other_historical_codes_held_fixed': len(current['assessments'])-57,
                            'total_positions': len(current['assessments'])},
        'input_sha256': {str(p.relative_to(repository)).replace('\\','/'): sha(p) for p in files.values()},
        'historical': {k: historical[k] for k in scenario},
        'source_limited_human_positive_only_scenario': scenario,
        'comparisons': comparison,
        'positive_witness_bridge': bridge,
        'all_position_bridge': all_positions,
    }


def selftest(repository):
    legacy = import_script(Path(repository)/'input_snapshot/codigo/analise_final.py', 'sensitivity_test_legacy')
    def row(status, **kw):
        return {'status': status, 'unresolved_conflict_hold': False,
                'complete_fixed_reference_verified': True, 'both_eligible_arms_reconstructed': True,
                'derivation_validated': True, 'analysis_scope_closed_for_this_position': True,
                'cumulative_unresolved_gap_ids': [], **kw}
    tests = []
    def check(name, actual, expected):
        assert actual == expected, (name, actual, expected)
        tests.append(name)
    check('valid_exact_witness_beats_unrelated_unknown', legacy.indicator([row('complete_derived'), row('reference_unverifiable')]), 1)
    check('unknown_propagates_without_valid_witness', legacy.indicator([row('partial_reference'), row('reference_unverifiable')]), None)
    check('unresolved_cumulative_gap_propagates', legacy.indicator([row('partial_reference', cumulative_unresolved_gap_ids=['gap'])]), None)
    check('unverified_nominal_positive_is_unknown', legacy.indicator([row('complete_derived', derivation_validated=False)]), None)
    check('direct_only_excludes_valid_derivation', legacy.indicator([row('complete_derived')], allow_derivations=False), 0)
    check('direct_only_keeps_direct_witness', legacy.indicator([row('complete_direct')], allow_derivations=False), 1)
    check('direct_only_preserves_source_unknown', legacy.indicator([row('reference_unverifiable')], allow_derivations=False), None)
    before = row('complete_derived')
    after = copy.deepcopy(before)
    after['status'] = 'public_source_unavailable'
    check('positive_only_unknown_changes_effective_status', (legacy.indicator([before]), legacy.indicator([after])), (1, None))
    layers = {'A': [row('reference_unverifiable')], 'B3': [row('complete_direct')]}
    check('later_layer_not_carried_backward', (legacy.indicator(layers['A']), legacy.indicator(layers['B3'])), (None, 1))
    check('separate_modalities_not_carried_between_cells', (legacy.indicator([row('reference_unverifiable')]), legacy.indicator([row('complete_direct')])), (None, 1))
    def position(stage, status, modality='adverse_event_reports'):
        return {**row(status), 'unit_id': 'SYNTHETIC', 'component': 'suicide_death', 'stage': stage,
                'modality': modality, 'reference_id': 'R', 'window_id': 'W'}
    synthetic = {'assessments': [position('A','reference_unverifiable'),
        position('B1','complete_derived'), position('B3','complete_direct'),
        position('B3','partial_reference',modality='structured')]}
    source_snapshot = copy.deepcopy(synthetic)
    pairs, reconciled = [], []
    for p, current in [(synthetic['assessments'][1], 'public_source_unavailable'),
                       (synthetic['assessments'][2], 'complete_direct')]:
        keys = {k:p[k] for k in KEY}
        rating = {'cumulative_classification': current, 'source_scoped_classification': current,
                  'primary_source_examined': 'yes'}
        pairs.append({**keys, 'position_id': 'SYNTHETIC-'+p['stage'], 'R1':rating,'R2':rating})
        reconciled.append({**keys,'raw_cumulative_classification': {'R1':current,'R2':current},
            'technical_reconciliation': {'sufficient_witness_source_ids_within_this_row_layer':['SYNTHETIC'],
                                         'source_original_scopes':[]}})
    projected, _, changed = apply_scenario(synthetic, {'rows':pairs}, {'rows':reconciled}, legacy)
    check('projection_changes_only_exact_unknown_positive_key', changed, {key(synthetic['assessments'][1])})
    check('projection_preserves_original_data_object', synthetic, source_snapshot)
    check('projection_does_not_complete_earlier_layer', legacy.indicator([projected['assessments'][0]]), None)
    check('projection_does_not_change_other_modality_negative', legacy.indicator([projected['assessments'][3]]), 0)
    return {'passed': True, 'tests': len(tests), 'test_names': tests, 'synthetic_only': True}


def export(result, out):
    out = Path(out)
    write(out/'SOURCE_LIMITED_HUMAN_POSITIVE_SENSITIVITY.json', {k:v for k,v in result.items() if k not in {'positive_witness_bridge','all_position_bridge'}})
    write(out/'POSITIVE_WITNESS_BRIDGE_57.json', {'schema': SCHEMA, 'raw_human_labels_preserved': True,
          'primary_results_replaced': False, 'rows': result['positive_witness_bridge']})
    write(out/'POSITION_BRIDGE_5096.json', {'schema': SCHEMA, 'primary_results_replaced': False, 'rows': result['all_position_bridge']})
    write_csv(out/'POSITIVE_WITNESS_BRIDGE_57.csv', result['positive_witness_bridge'], list(result['positive_witness_bridge'][0]))
    write_csv(out/'POSITION_BRIDGE_5096.csv', result['all_position_bridge'], list(result['all_position_bridge'][0]))
    for name, rows in result['comparisons'].items():
        flat = []
        for row in rows:
            current = {k:v for k,v in row.items() if k not in {'historical','source_limited_human_positive_only_scenario'}}
            for prefix, vals in [('historical', row['historical']), ('source_limited_scenario', row['source_limited_human_positive_only_scenario'])]:
                current.update({prefix+'_'+k: v for k,v in vals.items()})
            flat.append(current)
        write_csv(out/(name.upper()+'_COMPARISON.csv'), flat, list(dict.fromkeys(k for row in flat for k in row)))
    b3_main = [row for row in result['comparisons']['secondary_union_results']
               if row['analysis_set'] == 'whole_population_posthoc_exploratory' and row['stage'] == 'B3']
    write(out/'TABLE_HUMAN_LINKED_SENSITIVITY_B3_WHOLE.json', {
        'title': 'Positive-only sensitivity linked to the source-limited human reassessment (B3, 159 whole-population units)',
        'not_error_correction_or_replacement_primary_analysis': True,
        'counts': b3_main,
        'note': 'Only the 37 historical complete positions currently unknown in both reassessments are set unknown, at their exact original keys. All other historical codes remain fixed. Complete current witnesses for five derived-death units remain. These conditional intervals are not accuracy estimates, clinical risks, or confidence intervals.'})
    readme = '''SOURCE-LIMITED HUMAN POSITIVE-ONLY SENSITIVITY, 2026-11-05

This is an illustrative sensitivity of the historical documentary analysis,
not an adjudication, error correction, or replacement primary analysis.
The original historical result and all raw human labels remain unchanged.

Rule: all 57 historical complete positions were in the reassessment census.
Twenty positions remain complete in both returns. In this scenario alone,
the other 37 take their exact concordant current unknown label. The remaining
5,039 historical position codes stay fixed. References, windows, source records,
proof flags, units, populations, and modality/layer keys do not move.
In particular, the 425 sampled historical negatives now unknown are not recoded.
Therefore this scenario is not a wholesale analysis of the 663 current returns.

Main B3 union (whole-population N=159):
Ideation: historical k=1,u=26; scenario k=1,u=26; interval 0.63%-16.98%.
Attempt: historical k=1,u=26; scenario k=1,u=26; interval 0.63%-16.98%.
Death: historical k=15,u=26; scenario k=5,u=36; interval 3.14%-25.79%
(historical 9.43%-25.79%). All five current complete death units are derived.

Source-limited human indeterminacy does not demonstrate historical error.
The historical technical witness checks are not new human verification.
Intervals are conditional on the admitted corpus and this scenario, not
sampling confidence intervals, clinical risks, or exhaustive-trial-universe
bounds. Nothing is extrapolated to unreviewed positions or unlocated trials.

FILES
SOURCE_LIMITED_HUMAN_POSITIVE_SENSITIVITY.json: full descriptive scenario,
84 modality cells, 36 secondary union cells, 9 direct-only summaries,
12 illustrative added-block scenarios, and all corresponding historical tables.
TABLE_HUMAN_LINKED_SENSITIVITY_B3_WHOLE.json: compact three-component main table.
POSITIVE_WITNESS_BRIDGE_57.json/csv: every historical positive's exact key,
paired human labels, scenario status, and original source/hash/locator witness.
POSITION_BRIDGE_5096.json/csv: complete position ledger, keeping historical
source-scoped observations, paired human cumulative judgments, and scenario-
imposed analytic statuses distinct, and identifying the 37 sensitivity-only deltas.
*_COMPARISON.csv: table exports for all modalities, layers, and three rosters.
REPRODUCTION_MANIFEST.json: input and generated-file SHA-256 hashes.

REPRODUCE (Python standard library only)
python reassessed_positive_sensitivity.py --repository PATH_TO_PUBLIC_REPOSITORY --out OUTPUT_DIRECTORY
python reassessed_positive_sensitivity.py --repository PATH_TO_PUBLIC_REPOSITORY --selftest

The script first reproduces all historical distributed modality tables using
the inherited code, verifies an independent descriptive table implementation,
then runs the scenario and 14 targeted synthetic checks. No original input,
historical result, public repository file, or human decision is modified.
The --repository directory must contain the v1.2.0-or-later input_snapshot,
current_input, current_analysis, and validation files recorded by hash.
'''
    (out/'README.txt').write_text(readme, encoding='utf-8', newline='\n')
    script_path = Path(__file__)
    target = out/script_path.name
    if target.resolve() != script_path.resolve():
        target.write_bytes(script_path.read_bytes())
    write(out/'REPRODUCTION_MANIFEST.json', {'schema': SCHEMA, 'input_sha256': result['input_sha256'],
        'generated_file_sha256': {p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != 'REPRODUCTION_MANIFEST.json'},
        'command': 'python reassessed_positive_sensitivity.py --repository PATH_TO_PUBLIC_REPOSITORY --out OUTPUT_DIRECTORY'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        print(json.dumps(selftest(args.repository), sort_keys=True))
        return
    assert args.out, '--out is required outside selftest'
    result = run(args.repository)
    result['synthetic_tests'] = selftest(args.repository)
    export(result, args.out)
    print(json.dumps({'position_counts': result['position_counts'],
        'table_counts': {k:len(v) for k,v in result['comparisons'].items()},
        'B3_whole': [r for r in result['comparisons']['secondary_union_results'] if r['analysis_set']=='whole_population_posthoc_exploratory' and r['stage']=='B3'],
        'synthetic_tests': result['synthetic_tests']}, sort_keys=True))


if __name__ == '__main__':
    main()
