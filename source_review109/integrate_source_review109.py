"""Integrate a source-directed paired internal reassessment without extrapolation.

Standard library only. Historical inputs and the v1.3 sensitivity are immutable.
The 72 probability-sampled positions are updated individually; no error-rate,
population prevalence, clinical effect, or sampling confidence interval is fit.
"""
from pathlib import Path
import argparse
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import re

KEY = ('unit_id', 'component', 'stage', 'modality', 'reference_id', 'window_id')
COMPLETE = {'complete_direct', 'complete_derived'}
STAGES = ('A', 'B1', 'B2', 'B3')
UNKNOWN = {'public_source_unavailable', 'reference_unverifiable', 'pending_decision'}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(row):
    return tuple(row[field] for field in KEY)


def target(row):
    return tuple(row[field] for field in KEY if field != 'stage')


def dump(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True,
        indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def csv_dump(path, rows, fields):
    with Path(path).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({field: json.dumps(row.get(field), ensure_ascii=False,
                sort_keys=True) if isinstance(row.get(field), (list, dict))
                else row.get(field) for field in fields})


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def flattened(doc):
    result = {}
    for case in doc['cases']:
        for row in case['positions']:
            assert key(row) not in result, 'Duplicate assessment key'
            result[key(row)] = row
    return result


def prepare_pairs(raw1, raw2, roster, baseline, legacy):
    left, right = flattened(raw1), flattened(raw2)
    selected = {key(row): row for row in roster['rows']}
    old = {key(row): row for row in baseline['assessments']}
    assert set(left) == set(right) == set(selected) and len(left) == 109
    sources = {row['source_id']: row for row in raw1['sources']}
    assert sources == {row['source_id']: row for row in raw2['sources']}
    rows = []
    for k in sorted(left):
        a, b = left[k]['answer'], right[k]['answer']
        # Dates and an examiner's prose may differ without creating a substantive
        # classification disagreement. Preserve both actual assessments.
        critical = ('source_scoped_classification', 'cumulative_classification',
                    'six_dimensions', 'count_basis', 'reported_or_derived_counts_by_arm',
                    'denominators_by_arm', 'targeted_scope_coverage', 'source_bindings')
        concordance = {field: a[field] == b[field] for field in critical}
        assert all(concordance.values()), 'A paired discrepancy needs adjudication'
        bindings = []
        for item in a['source_bindings']:
            source = sources[item['source_id']]
            bindings.append({**item, 'source_content_sha256': source['source_content_sha256']})
        rows.append({**{field: left[k][field] for field in KEY},
            'position_id': left[k]['position_id'],
            'design_group': selected[k]['design_group'],
            'sampling_design': {field: selected[k].get(field) for field in
                ('stratum_id', 'N_h', 'n_h', 'm_h', 'phase1_probability',
                 'phase2_probability', 'composed_probability', 'weight')},
            'historical_source_scoped_status': old[k]['status'],
            'historical_effective_indicator': legacy.indicator([old[k]]),
            'R1': copy.deepcopy(a), 'R2': copy.deepcopy(b),
            'paired_field_concordance': concordance,
            'source_bindings_with_content_hashes': bindings,
            'new_positive_candidate': a['cumulative_classification'] in COMPLETE and
                not legacy.valid_complete(old[k]),
            'incomplete_relevant_scope': a['targeted_scope_coverage'] == 'incomplete_relevant_scope'})
    return rows


def witness(row):
    answer = row['R1']
    assert answer['cumulative_classification'] in COMPLETE
    assert all(value == 'established_compatible' for value in answer['six_dimensions'].values())
    assert answer['targeted_scope_coverage'] == 'sufficient_positive_witness_examined'
    assert answer['reported_or_derived_counts_by_arm'] and answer['denominators_by_arm']
    return {**{field: row[field] for field in KEY}, 'position_id': row['position_id'],
        'paired_human_classification': answer['cumulative_classification'],
        'six_dimensions': answer['six_dimensions'], 'count_basis': answer['count_basis'],
        'counts_by_arm': answer['reported_or_derived_counts_by_arm'],
        'denominators_by_arm': answer['denominators_by_arm'],
        'examined_primary_source_bindings': [item for item in
            row['source_bindings_with_content_hashes']
            if item['relevance_and_examination'] == 'examined_relevant'],
        'rationale': answer['evidence_and_rationale']}


def apply_pairs(baseline, paired, accepted_new, legacy,
                allow_pending_candidates=False, propagate_incomplete=False,
                proof_reuse_sets=None, proof_reuse_min_stages=None):
    revised = copy.deepcopy(baseline)
    by_key = {key(row): row for row in revised['assessments']}
    human_keys = {key(row) for row in paired}
    accepted_witnesses = []
    incomplete = []
    proof_reuse_sets = proof_reuse_sets or {}
    proof_reuse_min_stages = proof_reuse_min_stages or {}
    for pair in paired:
        k = key(pair)
        row, answer = by_key[k], pair['R1']
        incoming = answer['source_scoped_classification']
        is_positive = answer['cumulative_classification'] in COMPLETE
        if is_positive:
            if pair['new_positive_candidate'] and pair['position_id'] not in accepted_new and not allow_pending_candidates:
                # The independent human decision is preserved in the bridge, but
                # no new analytic positive is accepted before source checking.
                continue
            proof = witness(pair)
            row['status'] = answer['cumulative_classification']
            row['complete_fixed_reference_verified'] = True
            row['both_eligible_arms_reconstructed'] = True
            row['derivation_validated'] = row['status'] == 'complete_derived'
            row['source_review109_witness'] = proof
            row['analysis_scope_closed_for_this_position'] = True
            accepted_witnesses.append(proof)
        else:
            row['status'] = incoming
            row['complete_fixed_reference_verified'] = False
            row['both_eligible_arms_reconstructed'] = False
            row['derivation_validated'] = False
            relevant_unexamined = [item['source_id'] for item in answer['source_bindings']
                if item['relevance_and_examination'] == 'unexamined_relevant']
            if pair['incomplete_relevant_scope'] or answer['cumulative_classification'] in UNKNOWN:
                # A source-scoped partial result is not an effective zero where
                # a pertinent source, target identity, or full window remains open.
                row['analysis_scope_closed_for_this_position'] = False
                row['source_available_not_yet_assessed'] = True
                row['unexamined_relevant_source_ids'] = sorted(set(
                    row.get('unexamined_relevant_source_ids', []) + relevant_unexamined))
                row['source_review109_unresolved_scope'] = {
                    'position_id': pair['position_id'],
                    'cumulative_human_classification': answer['cumulative_classification'],
                    'coverage': answer['targeted_scope_coverage'],
                    'rationale': answer['scope_comparability_rationale']}
                incomplete.append(pair)
            else:
                assert answer['targeted_scope_coverage'] == 'comparable_relevant_source_union_examined'
                row['analysis_scope_closed_for_this_position'] = True
                # Never erase pre-existing formal gap IDs or unknown flags from
                # the immutable evidence ledger merely because one sampled row
                # now has source-comparable coverage.
        row['source_review109_integration'] = {
            'position_id': pair['position_id'],
            'human_assessment_exact_key': True,
            'source_scoped_classification': incoming,
            'cumulative_classification': answer['cumulative_classification'],
            'coverage': answer['targeted_scope_coverage'],
            'new_positive_source_check_accepted': pair['position_id'] in accepted_new
                if pair['new_positive_candidate'] else None}
    propagated = []
    # A positive witness may enter a strictly later cumulative layer. A witness
    # found during a later review can also be reused in an earlier layer ONLY
    # where every source necessary to the exact proof was already admissible,
    # with the same content hash, in that layer's cumulative source inventory.
    # This is not transport of a registry/regulatory result into article A.
    for proof in accepted_witnesses:
        origin = by_key[key(proof)]
        required_ids = set(proof_reuse_sets.get(proof['position_id'], []))
        proof_hashes = {binding['source_id']: binding['source_content_sha256']
            for binding in proof['examined_primary_source_bindings']}
        assert required_ids <= set(proof_hashes), 'Every necessary proof source must have been examined'
        for row in revised['assessments']:
            if target(row) != target(proof) or key(row) == key(proof):
                continue
            later_layer = STAGES.index(row['stage']) > STAGES.index(proof['stage'])
            admissible_source_hashes = {}
            if required_ids:
                for inventory_row in baseline['assessments']:
                    if target(inventory_row) != target(row) or STAGES.index(inventory_row['stage']) > STAGES.index(row['stage']):
                        continue
                    for ref in inventory_row.get('assessment_evidence_refs', []):
                        match = re.match(r'^(SRC-[^#]+)#sha256=([0-9a-f]{64})[;#]', ref)
                        if match:
                            assert match.group(1) not in admissible_source_hashes or admissible_source_hashes[match.group(1)] == match.group(2)
                            admissible_source_hashes[match.group(1)] = match.group(2)
            exact_sources_already_admissible = bool(required_ids) and all(
                admissible_source_hashes.get(source_id) == proof_hashes[source_id] for source_id in required_ids)
            exact_sources_already_admissible = exact_sources_already_admissible and STAGES.index(row['stage']) >= STAGES.index(
                proof_reuse_min_stages.get(proof['position_id'], 'A'))
            if not later_layer and not exact_sources_already_admissible:
                continue
            if legacy.valid_complete(row):
                continue
            # An explicit later human non-complete finding cannot be silently
            # overruled; report it for adjudication instead.
            if key(row) in human_keys:
                raise AssertionError('Positive cumulative witness conflicts with a later exact human decision')
            before = copy.deepcopy(row)
            row['status'] = proof['paired_human_classification']
            row['complete_fixed_reference_verified'] = True
            row['both_eligible_arms_reconstructed'] = True
            row['derivation_validated'] = row['status'] == 'complete_derived'
            row['source_review109_witness'] = copy.deepcopy(proof)
            deduction_kind = 'positive_witness_forward_deduction_not_a_new_human_vote' if later_layer else 'reuse_of_exact_admissible_original_witness_not_a_new_human_vote'
            row['source_review109_forward_propagation'] = {
                'kind': 'technical_deduction_not_a_new_human_vote',
                'origin_position_id': proof['position_id'], 'origin_stage': proof['stage'],
                'admissible_direction': 'strictly_later_cumulative_layer_only' if later_layer else 'exact_original_proof_already_admissible_in_this_layer',
                'required_original_source_ids': sorted(required_ids),
                'required_source_hashes_verified_in_this_layer': exact_sources_already_admissible}
            propagated.append({**{field: row[field] for field in KEY},
                'origin_position_id': proof['position_id'], 'origin_stage': proof['stage'],
                'kind': deduction_kind,
                'required_original_source_ids': sorted(required_ids),
                'required_original_source_hashes': {source_id: proof_hashes[source_id] for source_id in required_ids},
                'same_source_content_admissible_in_target_layer_verified': exact_sources_already_admissible,
                'before_status': before['status'], 'after_status': row['status'],
                'before_indicator': legacy.indicator([before]),
                'after_indicator': legacy.indicator([row])})
    if propagate_incomplete:
        # This deliberately conservative scenario treats each newly documented
        # incomplete target scope as still unresolved in later layers. It is
        # kept separate from the exact-key integration; it does not claim those
        # later source collections were newly examined by either reviewer.
        propagated_gaps = {}
        for pair in incomplete:
            required_unexamined_ids = {binding['source_id'] for binding in pair['R1']['source_bindings']
                if binding['relevance_and_examination'] == 'unexamined_relevant'}
            later_resolutions = []
            for later_pair in paired:
                if target(later_pair) != target(pair) or STAGES.index(later_pair['stage']) <= STAGES.index(pair['stage']):
                    continue
                if later_pair['R1']['targeted_scope_coverage'] != 'comparable_relevant_source_union_examined':
                    continue
                later_bindings = {binding['source_id']: binding for binding in later_pair['R1']['source_bindings']}
                resolved_ids = {source_id for source_id, binding in later_bindings.items()
                    if binding['relevance_and_examination'] in {'examined_relevant', 'not_relevant_for_this_target'}
                    and binding.get('locator_for_this_target') and binding.get('rationale')}
                if not required_unexamined_ids or required_unexamined_ids <= resolved_ids:
                    later_resolutions.append(later_pair)
            for row in revised['assessments']:
                if target(row) != target(pair) or STAGES.index(row['stage']) <= STAGES.index(pair['stage']):
                    continue
                if legacy.valid_complete(row):
                    continue
                if any(STAGES.index(resolved['stage']) <= STAGES.index(row['stage']) for resolved in later_resolutions):
                    # Resolution in B2 also resolves the same earlier-source
                    # gap in cumulative B3; new B3-specific gaps remain separate.
                    continue
                before = copy.deepcopy(row)
                row['analysis_scope_closed_for_this_position'] = False
                row['source_available_not_yet_assessed'] = True
                marker = {
                    'kind': 'conservative_technical_scenario_not_a_new_human_vote',
                    'origin_position_id': pair['position_id'], 'origin_stage': pair['stage'],
                    'scope_gap_type': 'named_relevant_source_not_yet_examined' if required_unexamined_ids
                        else 'current_assessment_coverage_not_established_no_missing_paper_inferred',
                    'named_unexamined_source_ids': sorted(required_unexamined_ids)}
                row.setdefault('source_review109_incomplete_scope_forward_scenario', []).append(marker)
                if key(row) not in propagated_gaps:
                    propagated_gaps[key(row)] = {**{field: row[field] for field in KEY},
                        'origin_position_ids': [], 'origin_stages': [],
                        'kind': 'incomplete_scope_forward_conservative_scenario',
                        'before_status': before['status'], 'after_status': row['status'],
                        'before_indicator': legacy.indicator([before]),
                        'after_indicator': legacy.indicator([row]),
                        'indicator_changed': legacy.indicator([before]) != legacy.indicator([row]),
                        'gap_descriptors': []}
                propagated_gaps[key(row)]['origin_position_ids'].append(pair['position_id'])
                propagated_gaps[key(row)]['origin_stages'].append(pair['stage'])
                propagated_gaps[key(row)]['gap_descriptors'].append(marker)
        propagated.extend(propagated_gaps[k] for k in sorted(propagated_gaps))
    return revised, propagated


def make_stats(paired, raw1, raw2, legacy, integrated):
    by_key = {key(row): row for row in integrated['assessments']}
    groups = collections.defaultdict(list)
    for row in paired:
        groups[(row['design_group'], row['component'], row['stage'], row['modality'])].append(row)
    stats = []
    for labels, rows in sorted(groups.items()):
        stats.append({**dict(zip(('design_group', 'component', 'stage', 'modality'), labels)),
            'positions': len(rows),
            'historical_statuses': dict(collections.Counter(row['historical_source_scoped_status'] for row in rows)),
            'current_human_source_scoped': dict(collections.Counter(row['R1']['source_scoped_classification'] for row in rows)),
            'current_human_cumulative': dict(collections.Counter(row['R1']['cumulative_classification'] for row in rows)),
            'integrated_effective_indicators': dict(collections.Counter(
                'unknown' if legacy.indicator([by_key[key(row)]]) is None else
                str(legacy.indicator([by_key[key(row)]])) for row in rows)),
            'incomplete_relevant_scope': sum(row['incomplete_relevant_scope'] for row in rows)})
    source_coverage = {}
    for name, raw in (('R1', raw1), ('R2', raw2)):
        examinations = [source for case in raw['cases'] for source in case['source_examinations']]
        source_coverage[name] = {
            'case_source_examinations': len(examinations),
            'distinct_source_ids': len({row['source_id'] for row in examinations}),
            'by_examination_status': dict(collections.Counter(row['examination_status'] for row in examinations)),
            'case_count': len(raw['cases']), 'position_count': len(paired)}
    by_group = []
    for group in sorted({row['design_group'] for row in paired}):
        subset = [row for row in paired if row['design_group'] == group]
        by_group.append({'design_group': group, 'positions': len(subset),
            'current_source_scoped': dict(collections.Counter(row['R1']['source_scoped_classification'] for row in subset)),
            'current_cumulative': dict(collections.Counter(row['R1']['cumulative_classification'] for row in subset)),
            'coverage': dict(collections.Counter(row['R1']['targeted_scope_coverage'] for row in subset))})
    def agreement(rows, field):
        labels = sorted({row[reviewer][field] for row in rows for reviewer in ('R1', 'R2')})
        n = len(rows)
        observed = sum(row['R1'][field] == row['R2'][field] for row in rows) / n if n else None
        left = collections.Counter(row['R1'][field] for row in rows)
        right = collections.Counter(row['R2'][field] for row in rows)
        expected = sum(left[label]*right[label] for label in labels)/n**2 if n else None
        return {'n': n, 'observed_agreement': observed,
            'Cohen_kappa_internal_descriptive': (observed-expected)/(1-expected)
                if expected is not None and expected != 1 else None,
            'kappa_not_estimable_reason': 'Single-class margins' if expected == 1 else None,
            'confidence_interval': None, 'not_an_external_accuracy_measure': True}
    return {'paired_positions': len(paired), 'exact_classification_agreement_positions':
        sum(row['R1']['source_scoped_classification'] == row['R2']['source_scoped_classification'] and
            row['R1']['cumulative_classification'] == row['R2']['cumulative_classification'] for row in paired),
        'historical_complete_rechecked': sum(row['design_group'] != 'phase2_original_negative_probability_sample' for row in paired),
        'phase2_historical_negative_positions': sum(row['design_group'] == 'phase2_original_negative_probability_sample' for row in paired),
        'current_source_scoped_classifications': dict(collections.Counter(row['R1']['source_scoped_classification'] for row in paired)),
        'current_cumulative_classifications': dict(collections.Counter(row['R1']['cumulative_classification'] for row in paired)),
        'coverage': dict(collections.Counter(row['R1']['targeted_scope_coverage'] for row in paired)),
        'internal_paired_agreement': {field: agreement(paired, field) for field in
            ('source_scoped_classification', 'cumulative_classification')},
        'internal_paired_agreement_by_design_group': {group: {
            field: agreement([row for row in paired if row['design_group'] == group], field)
            for field in ('source_scoped_classification', 'cumulative_classification')}
            for group in sorted({row['design_group'] for row in paired})},
        'source_examinations': source_coverage, 'by_design_group': by_group,
        'grouped_by_design_component_layer_modality': stats,
        'no_external_accuracy_claim': True, 'no_error_rate_extrapolated': True,
        'no_naive_sampling_confidence_interval': True,
        'author_reported_independent_internal_assessments': True,
        'external_or_memory_blinded_validation': False}


def deltas(before, after, legacy):
    old = {key(row): row for row in before['assessments']}
    result = []
    for row in after['assessments']:
        original = old[key(row)]
        if original != row:
            changed = {field: {'before': original.get(field), 'after': row.get(field)}
                for field in sorted(set(original) | set(row)) if original.get(field) != row.get(field)}
            result.append({**{field: row[field] for field in KEY},
                'before_indicator': legacy.indicator([original]),
                'after_indicator': legacy.indicator([row]),
                'changed_fields': changed})
    return result


def selftest(legacy):
    count = 0
    def check(actual, expected):
        nonlocal count
        assert actual == expected, (actual, expected)
        count += 1
    def row(status='partial_reference', **kwargs):
        return {'status': status, 'unresolved_conflict_hold': False,
            'complete_fixed_reference_verified': False, 'both_eligible_arms_reconstructed': False,
            'derivation_validated': False, 'analysis_scope_closed_for_this_position': True, **kwargs}
    check(legacy.indicator([row()]), 0)
    check(legacy.indicator([row(analysis_scope_closed_for_this_position=False)]), None)
    check(legacy.indicator([row(source_available_not_yet_assessed=True)]), None)
    check(legacy.indicator([row(unexamined_relevant_source_ids=['S'])]), None)
    check(legacy.indicator([row('reference_unverifiable')]), None)
    positive = row('complete_derived', complete_fixed_reference_verified=True,
                   both_eligible_arms_reconstructed=True, derivation_validated=True)
    check(legacy.indicator([positive]), 1)
    check(legacy.indicator([positive, row(analysis_scope_closed_for_this_position=False)]), 1)
    check(legacy.indicator([positive], allow_derivations=False), 0)
    check(legacy.indicator([row('complete_derived')]), None)
    # Target identity excludes only stage, never modality or reference/window.
    base = dict(zip(KEY, ('U', 'D', 'B2', 'M', 'R', 'W')))
    check(target(base) == target({**base, 'stage': 'B3'}), True)
    for field in ('unit_id', 'component', 'modality', 'reference_id', 'window_id'):
        check(target(base) == target({**base, field: 'different'}), False)
    def data():
        cells = [{**dict(zip(KEY, ('U', 'D', stage, 'M', 'R', 'W'))), **row()}
            for stage in STAGES]
        cells.extend([{**cells[-1], 'modality': 'other'}, {**cells[-1], 'window_id': 'other'}])
        return {'assessments': cells}
    def pair_at(stage, complete=False, coverage='incomplete_relevant_scope', bindings=None):
        answer = {'source_scoped_classification': 'complete_derived' if complete else 'partial_reference',
            'cumulative_classification': 'complete_derived' if complete else 'partial_reference',
            'six_dimensions': {name: 'established_compatible' for name in
                ('numerator', 'denominator', 'window', 'subpopulation', 'counting_unit', 'source_access')},
            'count_basis': 'derived_from_explicit_report', 'reported_or_derived_counts_by_arm': {'a': {'n': 0}, 'b': {'n': 0}},
            'denominators_by_arm': {'a': {'N': 10}, 'b': {'N': 10}},
            'targeted_scope_coverage': 'sufficient_positive_witness_examined' if complete else coverage,
            'source_bindings': bindings or [], 'evidence_and_rationale': 'Synthetic source-specific test',
            'scope_comparability_rationale': 'Synthetic target-scope test'}
        return {**dict(zip(KEY, ('U', 'D', stage, 'M', 'R', 'W'))), 'position_id': 'P'+stage,
            'R1': answer, 'R2': copy.deepcopy(answer), 'source_bindings_with_content_hashes': [],
            'new_positive_candidate': complete, 'incomplete_relevant_scope': not complete and coverage == 'incomplete_relevant_scope'}
    positive_pair = pair_at('B2', complete=True)
    revised, propagation = apply_pairs(data(), [positive_pair], {'PB2'}, legacy)
    lookup = {key(r): r for r in revised['assessments']}
    for stage, expected in [('A', 0), ('B1', 0), ('B2', 1), ('B3', 1)]:
        check(legacy.indicator([lookup[('U', 'D', stage, 'M', 'R', 'W')]]), expected)
    check(len(propagation), 1)
    check(legacy.indicator([lookup[('U', 'D', 'B3', 'other', 'R', 'W')]]), 0)
    check(legacy.indicator([lookup[('U', 'D', 'B3', 'M', 'R', 'other')]]), 0)
    pending, _ = apply_pairs(data(), [positive_pair], set(), legacy)
    check(sum(legacy.indicator([r]) == 1 for r in pending['assessments']), 0)
    incomplete_pair = pair_at('A')
    exact, _ = apply_pairs(data(), [incomplete_pair], set(), legacy)
    check([legacy.indicator([r]) for r in exact['assessments'][:4]], [None, 0, 0, 0])
    forward, _ = apply_pairs(data(), [incomplete_pair], set(), legacy, propagate_incomplete=True)
    check([legacy.indicator([r]) for r in forward['assessments'][:4]], [None, None, None, None])
    check([legacy.indicator([r]) for r in forward['assessments'][4:]], [0, 0])
    resolution = pair_at('B2', coverage='comparable_relevant_source_union_examined')
    resolved, _ = apply_pairs(data(), [incomplete_pair, resolution], set(), legacy, propagate_incomplete=True)
    check([legacy.indicator([r]) for r in resolved['assessments'][:4]], [None, None, 0, 0])
    named_gap = pair_at('A', bindings=[{'source_id': 'S', 'relevance_and_examination': 'unexamined_relevant'}])
    unresolved, _ = apply_pairs(data(), [named_gap, resolution], set(), legacy, propagate_incomplete=True)
    check([legacy.indicator([r]) for r in unresolved['assessments'][:4]], [None, None, None, None])
    resolution['R1']['source_bindings'] = [{'source_id': 'S', 'relevance_and_examination': 'examined_relevant',
        'locator_for_this_target': 'Synthetic p2', 'rationale': 'Relevant source examined'}]
    resolved_named, _ = apply_pairs(data(), [named_gap, resolution], set(), legacy, propagate_incomplete=True)
    check([legacy.indicator([r]) for r in resolved_named['assessments'][:4]], [None, None, 0, 0])
    # A sufficient positive is existential even when another relevant source is
    # unexamined; this never converts a missing adverse-event term into zero.
    incomplete_positive = pair_at('A')
    positive_later = pair_at('B2', complete=True)
    later_positive, _ = apply_pairs(data(), [incomplete_positive, positive_later], {'PB2'}, legacy,
        propagate_incomplete=True)
    check([legacy.indicator([r]) for r in later_positive['assessments'][:4]], [None, None, 1, 1])
    # Reuse an original proof only when exact required bytes were already in
    # the earlier layer's source inventory; discovery date is irrelevant.
    source_hash = 'a'*64
    proof_data = data()
    for r in proof_data['assessments']:
        r['assessment_evidence_refs'] = ['SRC-A#sha256='+source_hash+';Synthetic original article']
    reusable = pair_at('B3', complete=True)
    reusable['source_bindings_with_content_hashes'] = [{'source_id': 'SRC-A',
        'source_content_sha256': source_hash, 'relevance_and_examination': 'examined_relevant'}]
    reused, reuse_log = apply_pairs(proof_data, [reusable], {'PB3'}, legacy,
        proof_reuse_sets={'PB3': ['SRC-A']})
    check([legacy.indicator([r]) for r in reused['assessments'][:4]], [1, 1, 1, 1])
    check(len(reuse_log), 3)
    stage_restricted, _ = apply_pairs(proof_data, [reusable], {'PB3'}, legacy,
        proof_reuse_sets={'PB3': ['SRC-A']}, proof_reuse_min_stages={'PB3': 'B2'})
    check([legacy.indicator([r]) for r in stage_restricted['assessments'][:4]], [0, 0, 1, 1])
    bad_bytes = copy.deepcopy(proof_data)
    for r in bad_bytes['assessments'][:3]:
        r['assessment_evidence_refs'] = ['SRC-A#sha256='+'b'*64+';Wrong version']
    blocked, _ = apply_pairs(bad_bytes, [reusable], {'PB3'}, legacy,
        proof_reuse_sets={'PB3': ['SRC-A']})
    check([legacy.indicator([r]) for r in blocked['assessments'][:4]], [0, 0, 0, 1])
    check([legacy.indicator([r]) for r in reused['assessments'][4:]], [0, 0])
    return {'passed': count, 'all_passed': True}


def run(repository, r1, r2, accepted_file, out, public_paired=None):
    repository, out = Path(repository), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    legacy = module(repository / 'input_snapshot/codigo/analise_final.py', 'legacy_source109')
    sensitivity = module(repository / 'validation_sensitivity/reassessed_positive_sensitivity.py', 'sensitivity_source109')
    baseline_path = repository / 'current_input/documental_entrada_reconciliada.json'
    pop_path = repository / 'input_snapshot/dados/populacoes_final.json'
    baseline, pop = load(baseline_path), load(pop_path)
    roster_path = repository / 'linked_review_protocol/SELECTION_ROSTER.json'
    if public_paired:
        public_input = load(public_paired)
        paired = public_input['rows']
        selected_keys = {key(row) for row in load(roster_path)['rows']}
        assert {key(row) for row in paired} == selected_keys and len(paired) == 109
        assert all(row['R1']['source_scoped_classification'] == row['R2']['source_scoped_classification']
            and row['R1']['cumulative_classification'] == row['R2']['cumulative_classification'] for row in paired)
        raw1 = public_input['source_examination_ledger']['R1']
        raw2 = public_input['source_examination_ledger']['R2']
        raw_hashes = public_input['input_provenance']
    else:
        raw1, raw2 = load(r1), load(r2)
        paired = prepare_pairs(raw1, raw2, load(roster_path), baseline, legacy)
        # Only anonymous rater codes and finite, source-linked scientific fields
        # are projected. Local paths, personal declarations, signatures, and
        # licensed full texts are not needed to reproduce the calculation.
        allowed = ('source_scoped_classification', 'cumulative_classification',
            'six_dimensions', 'count_basis', 'reported_or_derived_counts_by_arm',
            'denominators_by_arm', 'targeted_scope_coverage', 'scope_comparability_rationale',
            'source_bindings', 'evidence_and_rationale')
        for row in paired:
            for reviewer in ('R1', 'R2'):
                row[reviewer] = {field: row[reviewer][field] for field in allowed}
        raw_hashes = {'locked_return_R1': sha(r1), 'locked_return_R2': sha(r2)}
    acceptance = load(accepted_file) if accepted_file else {'accepted_position_ids': [], 'status': 'source_check_pending'}
    accepted = set(acceptance['accepted_position_ids'])
    proof_reuse_sets = acceptance.get('required_original_source_ids_by_position', {})
    proof_reuse_min_stages = {row['positive_position_id_verified']: row['earliest_admissible_stage_if_guard_passes']
        for row in acceptance.get('minimal_source_sets', [])}
    candidate_ids = {row['position_id'] for row in paired if row['new_positive_candidate']}
    assert len(candidate_ids) == 4 and accepted <= candidate_ids
    historical = sensitivity.summarize(baseline, pop, legacy)
    v13_path = repository / 'validation_sensitivity/SOURCE_LIMITED_HUMAN_POSITIVE_SENSITIVITY.json'
    v13 = load(v13_path)
    assert historical == v13['historical'], 'Historical results must exactly reproduce before integration'
    integrated, propagated = apply_pairs(baseline, paired, accepted, legacy, proof_reuse_sets=proof_reuse_sets,
        proof_reuse_min_stages=proof_reuse_min_stages)
    conservative, conservative_propagated = apply_pairs(baseline, paired, accepted, legacy,
        propagate_incomplete=True, proof_reuse_sets=proof_reuse_sets, proof_reuse_min_stages=proof_reuse_min_stages)
    current = sensitivity.summarize(integrated, pop, legacy)
    forward = sensitivity.summarize(conservative, pop, legacy)
    stats = make_stats(paired, raw1, raw2, legacy, conservative)
    for row in paired:
        if row['incomplete_relevant_scope']:
            exact = next(r for r in integrated['assessments'] if key(r) == key(row))
            assert legacy.indicator([exact]) is None
    retained = [row for row in paired if not row['new_positive_candidate'] and row['R1']['cumulative_classification'] in COMPLETE]
    assert len(retained) == 37
    assert all(legacy.valid_complete(next(r for r in integrated['assessments'] if key(r) == key(p))) for p in retained)
    exact_changes = deltas(baseline, integrated, legacy)
    changes = deltas(baseline, conservative, legacy)
    undo = copy.deepcopy(conservative)
    by_key = {key(row): row for row in undo['assessments']}
    for delta in changes:
        for field, values in delta['changed_fields'].items():
            if values['before'] is None and field not in {key_: val for row in baseline['assessments'] if key(row)==key(delta) for key_,val in row.items()}:
                by_key[key(delta)].pop(field, None)
            else:
                by_key[key(delta)][field] = values['before']
    assert undo == baseline, 'Integration log must reverse without information loss'
    report = {'schema': 'source-directed-paired-internal-reassessment-integration-v1',
        'analysis_date': '2026-11-05', 'new_positive_acceptance_status': acceptance['status'],
        'accepted_new_positive_ids': sorted(accepted), 'pending_new_positive_ids': sorted(candidate_ids-accepted),
        'historical_inputs_overwritten': False, 'source_review_count': 109,
        'historical_positive_census': {'previously_confirmed': 20, 'newly_rechecked_confirmed': 37,
                                      'total_historical_positive_positions_confirmed': 57},
        'no_unreviewed_negative_sample_extrapolation': True,
        'interpretation': 'Internal source-directed verification; exact human decisions, forward positive-witness deductions, and reuse of exact original proofs only where all necessary identical source bytes were already admissible. No clinical inference or external accuracy claim.',
        'primary_comparison_scope': 'Same fixed corpus and 159/170/182 rosters; not the universe of trials',
        'historical': historical, 'v1_3_source_limited_sensitivity': v13['source_limited_human_positive_only_scenario'],
        'primary_model': 'accepted_conservative_cumulative_integration',
        'secondary_model': 'accepted_targeted_integration_without_scope_gap_propagation',
        'accepted_conservative_cumulative_integration': forward,
        'accepted_targeted_integration_without_scope_gap_propagation': current,
        'comparisons_historical_to_accepted_conservative': sensitivity.compare_tables(historical, forward),
        'comparisons_historical_to_accepted_targeted_without_scope_gap_propagation': sensitivity.compare_tables(historical, current),
        'comparisons_v1_3_sensitivity_to_accepted_conservative': sensitivity.compare_tables(v13['source_limited_human_positive_only_scenario'], forward),
        'source_examination_and_paired_review': stats,
        'propagated_positive_witness_deductions': propagated,
        'conservative_scope_forward_deductions': conservative_propagated,
        'synthetic_tests': selftest(legacy),
        'qa': {'historical_reproduced': True, 'exact_109_keys_match_selected_roster': True,
            'all_37_historical_positives_confirmed': True, 'all_13_incomplete_scopes_preserved_unknown': True,
            'change_log_reversible': True, 'no_import_of_later_only_source_into_earlier_layer': True,
            'no_cross_modality_reference_window_propagation': True},
        'input_sha256': {'historical_reconciled_data': sha(baseline_path), 'population_roster': sha(pop_path),
            **raw_hashes, 'selection_roster': sha(roster_path),
            'v1_3_human_linked_sensitivity': sha(v13_path),
            'source_check_acceptance': sha(accepted_file) if accepted_file else None}}
    source_examination_ledger = {reviewer: {'cases': [{'case_id': case['case_id'],
        'source_examinations': [{'source_id': item['source_id'], 'examination_status': item['examination_status']}
            for item in case['source_examinations']]} for case in raw['cases']]}
        for reviewer, raw in (('R1', raw1), ('R2', raw2))}
    dump(out / 'HUMAN_SOURCE_REVIEW109_PAIRED.json', {'schema': 'paired-source-review109-v1', 'rows': paired,
        'source_examination_ledger': source_examination_ledger, 'input_provenance': raw_hashes,
        'author_names_private_contacts_absent': True, 'no_new_human_votes_inferred': True})
    dump(out / 'SOURCE_REVIEW109_INTEGRATION_RESULTS.json', report)
    dump(out / 'SOURCE_REVIEW109_GROUPED_COUNTS.json', stats)
    dump(out / 'SOURCE_REVIEW109_REVERSIBLE_CHANGE_LOG.json', {'rows': changes,
        'model': report['primary_model'], 'base_sha256': sha(baseline_path), 'reversible_to_original': True,
        'exact_key_model_changes': exact_changes})
    dump(out / 'SOURCE_REVIEW109_INTEGRATED_INPUT.json', conservative)
    dump(out / 'SOURCE_REVIEW109_EXACT_KEY_SENSITIVITY_INPUT.json', integrated)
    dump(out / 'SOURCE_REVIEW109_POSITIVE_FORWARD_DEDUCTIONS.json', {'rows': propagated,
        'technical_deductions_not_new_human_votes': True})
    compact = []
    for model, values in [('historical', historical), ('v1_3_source_limited_sensitivity', v13['source_limited_human_positive_only_scenario']),
                          ('accepted_conservative_cumulative_integration', forward),
                          ('accepted_targeted_integration_without_scope_gap_propagation', current)]:
        for table in ('modality_results', 'secondary_union_results', 'without_derived_completeness', 'illustrative_membership_scenarios'):
            for row in values[table]:
                compact.append({'model': model, 'table': table, **row})
    fields = ['model', 'table', 'analysis_set', 'component', 'stage', 'modality', 'N', 'direct_confirmed',
        'derived_confirmed', 'confirmed_total', 'direct_complete', 'unknown', 'not_complete_in_examined_scope',
        'corpus_conditional_identification_interval', 'scenario', 'N_hypothetical',
        'assumed_additional_distinct_fully_eligible_units', 'known_confirmed_carried_forward', 'unknown_hypothetical']
    csv_dump(out / 'SOURCE_REVIEW109_RESULTS_COMPARISON.csv', compact, fields)
    dump(out / 'SOURCE_REVIEW109_RESULT_TABLES.json', {'primary_model': report['primary_model'],
        'secondary_model': report['secondary_model'], 'rows': compact})
    dump(out / 'SOURCE_REVIEW109_QA.json', {**report['qa'], 'synthetic_tests': report['synthetic_tests'],
        'accepted_new_positive_ids': sorted(accepted), 'pending_new_positive_ids': sorted(candidate_ids-accepted)})
    origin_counts = {
        'exact_human_position_keys_integrated': len(paired),
        'exact_human_keys_effective_indicator_changed': sum(
            delta['before_indicator'] != delta['after_indicator'] for delta in exact_changes
            if key(delta) in {key(row) for row in paired}),
        'exact_human_keys_source_scoped_label_changed': sum(
            row['historical_source_scoped_status'] != row['R1']['source_scoped_classification'] for row in paired),
        'strictly_forward_positive_witness_keys': sum(row['kind'] == 'positive_witness_forward_deduction_not_a_new_human_vote' for row in propagated),
        'strictly_forward_positive_witness_effective_indicator_changes': sum(
            row['kind'] == 'positive_witness_forward_deduction_not_a_new_human_vote' and
            row['before_indicator'] != row['after_indicator'] for row in propagated),
        'exact_original_proof_reuse_in_earlier_admissible_layer_keys': sum(
            row['kind'] == 'reuse_of_exact_admissible_original_witness_not_a_new_human_vote' for row in propagated),
        'forward_incomplete_scope_keys_annotated': sum(row['kind'] == 'incomplete_scope_forward_conservative_scenario'
            for row in conservative_propagated),
        'forward_incomplete_scope_effective_indicator_changes': sum(row['kind'] == 'incomplete_scope_forward_conservative_scenario'
            and row['indicator_changed'] for row in conservative_propagated),
        'principal_any_metadata_or_indicator_changed_keys': len(changes),
        'principal_effective_indicator_changed_keys': sum(delta['before_indicator'] != delta['after_indicator'] for delta in changes)}
    indicator_counts = dict(collections.Counter('unknown' if legacy.indicator([row]) is None else
        ('complete' if legacy.indicator([row]) == 1 else 'not_complete_in_examined_scope')
        for row in conservative['assessments']))
    dump(out / 'SOURCE_REVIEW109_EDITOR_SUMMARY.json', {
        'status': acceptance['status'], 'primary_model': report['primary_model'],
        'primary_B3_whole_population_union': [row for row in forward['secondary_union_results']
            if row['analysis_set'] == 'whole_population_posthoc_exploratory' and row['stage'] == 'B3'],
        'targeted_sensitivity_without_scope_gap_propagation_B3_whole_population_union': [row for row in current['secondary_union_results']
            if row['analysis_set'] == 'whole_population_posthoc_exploratory' and row['stage'] == 'B3'],
        'primary_B3_whole_population_modalities': [row for row in forward['modality_results']
            if row['analysis_set'] == 'whole_population_posthoc_exploratory' and row['stage'] == 'B3'],
        'changed_keys_by_origin': origin_counts,
        'principal_all_5096_effective_position_counts': indicator_counts,
        'principal_all_5096_source_scoped_status_counts': dict(collections.Counter(row['status'] for row in conservative['assessments'])),
        'linked_review_summary': stats,
        'historical_positive_confirmation_across_separate_rounds': report['historical_positive_census'],
        'rounds_are_not_772_independent_assessments': True,
        'all_57_historical_positive_positions_now_confirmed_in_two_reported_internal_rounds': True,
        'four_of_72_is_not_a_corpus_error_rate': True,
        'historical_20_of_57_source_limited_confirmation_preserved_as_past_round': True,
        'table_sizes_each_model': {field: len(forward[field]) for field in (
            'modality_results', 'secondary_union_results', 'without_derived_completeness', 'illustrative_membership_scenarios')}})
    dump(out / 'ACCEPTANCE_FOUR_POSITIVE_WITNESSES.json', acceptance)
    dump(out / 'REPRODUCTION_MANIFEST.json', {'algorithm': 'sha256', 'files': {
        p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != 'REPRODUCTION_MANIFEST.json'}})
    print(json.dumps({'status': acceptance['status'], 'paired_positions': 109,
        'confirmed_historical_positive_positions': 57, 'new_positive_candidates': 4,
        'accepted_new_positive_positions': len(accepted), 'incomplete_scopes_kept_unknown': 13,
        'output_directory': str(out), 'synthetic_tests': report['synthetic_tests']}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repository', required=True)
    p.add_argument('--r1')
    p.add_argument('--r2')
    p.add_argument('--public-paired')
    p.add_argument('--accepted-new-positives')
    p.add_argument('--out', required=True)
    args = p.parse_args()
    assert args.public_paired or (args.r1 and args.r2)
    run(args.repository, args.r1, args.r2, args.accepted_new_positives, args.out, args.public_paired)


if __name__ == '__main__':
    main()
