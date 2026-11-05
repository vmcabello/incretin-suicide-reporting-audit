"""Reproduce Table S1 from the nominal flags on each saved representation.

Pure standard library, Python3.10+. This verifies the published projection and
exact joins. Original native exports remain licensed local verification inputs;
their physical reading is documented by the build QA, not fabricated by this check.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path


def semantic_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def validate(root):
    d = read(root / 'SEARCH_UPDATE_REPRESENTATIONS_2558_EN.json')
    rows = d['records']
    assert len(rows) == 2558 and len({r['representation_id'] for r in rows}) == 2558
    stripped = [{k: v for k, v in r.items() if k != 'new_identifier_subset_membership'} for r in rows]
    assert semantic_sha(stripped) == d['augmentation_original_rows_semantic_sha256']
    minimal = read(root / 'NEW_IDENTIFIER_SUBSET_MEMBERSHIP_2558_EN.json')['records']
    by = {r['representation_id']: r for r in minimal}
    assert len(by) == len(rows)
    for r in rows:
        m = r['new_identifier_subset_membership']
        a = by[r['representation_id']]
        assert all(a[k] == v for k, v in m.items())
        assert a['database'] == r['database'] and a['native_identifier'] == r['native_identifier']
        assert a['native_record_provenance'] == r['native_record_provenance']
        assert m['table_s1_membership_status'] == 'established_by_named_identifier_source'
        assert isinstance(m['table_s1_new_identifier_subset'], bool)
        assert m['new_identifier_vs_same_database_historical_export'] == (not m['historical_export_identifier_check']['present'])
        if m['table_s1_new_identifier_subset']:
            assert m['table_s1_route'] == ('745_lot' if r['case_ids'] else 'prior_master')
            assert r['case_ids'] or r['prior_library_decision_links']
        else:
            assert m['table_s1_route'] is None
        if r['database'] == 'CENTRAL':
            assert not m['central_filtered95_member'] or m['table_s1_new_identifier_subset']
        assert m['scientific_eligibility_or_exhaustiveness_inferred_from_subset_membership'] is False
    expected = read(root / 'TABLE_S1_REPRODUCED_FROM_MARKED_SUBSETS_EN.json')
    result = []
    for db in ('PUBMED', 'EMBASE', 'PSYCINFO', 'CENTRAL'):
        selected = [r for r in minimal if r['database'] == db and r['table_s1_new_identifier_subset']]
        c = collections.Counter(r['table_s1_route'] for r in selected)
        result.append({'database': db, 'new_identifier_representations': len(selected), '745_lot_route': c['745_lot'], 'prior_master_route': c['prior_master']})
    assert result == expected['table_s1_rows']
    assert sum(r['central_filtered95_member'] is True for r in minimal) == expected['central_filtered_subset_count']
    extra = sorted(r['native_identifier'] for r in minimal if r['database'] == 'CENTRAL' and r['table_s1_new_identifier_subset'] and not r['central_filtered95_member'])
    assert extra == expected['central_full_additions_not_in_filtered95']
    exceptions = read(root / 'PUBMED_14_NEW_NATIVE_IDS_ALREADY_KNOWN_TO_MASTER_EN.json')['records']
    calculated = [r for r in rows if r['database'] == 'PUBMED' and r['new_identifier_subset_membership']['new_identifier_vs_same_database_historical_export'] and not r['new_identifier_subset_membership']['table_s1_new_identifier_subset']]
    assert {r['representation_id'] for r in exceptions} == {r['representation_id'] for r in calculated}
    assert len(exceptions) == 14
    assert all(any('same_primary_publication_PMID' in p['identifier_match_basis_as_recorded'] for p in r['prior_library_decision_links']) for r in exceptions)
    with (root / 'SEARCH_UPDATE_REPRESENTATIONS_2558_EN.tsv').open('r', encoding='utf-8', newline='') as f:
        tsv = list(csv.DictReader(f, delimiter='\t'))
    assert [r['representation_id'] for r in tsv] == [r['representation_id'] for r in rows]
    assert all(json.loads(r['new_identifier_subset_membership']) == j['new_identifier_subset_membership'] for r, j in zip(tsv, rows))
    chronology = root.parent / 'corpus/PROTOCOL_AMENDMENT_CHRONOLOGY_EN.json'
    if chronology.exists():
        history = read(chronology)
        assert semantic_sha(history['events'][:8]) == history['historical_first_eight_events_semantic_sha256']
        assert len(history['events']) >= 14
        requested = [i for i, e in enumerate(history['events']) if e.get('status') == 'revision_requested_matched_source_human_work_not_established_by_this_chronology']
        assert len(requested) == 1
        assert history['events'][requested[0]-1]['journal_submission_sent'] is False
        # Later dated technical progress may be appended without rewriting the
        # preceding request or converting a prepared lot to completed readings.
        for event in history['events'][requested[0]+1:]:
            assert event['status'] == 'sensitivity_completed_targeted_human_review_pending'
            assert event['historical_primary_codes_changed'] is False
            assert event['new_human_votes_created'] is False
    for p in (root / 'SEARCH_UPDATE_REPRESENTATIONS_2558_EN.json', root / 'NEW_IDENTIFIER_SUBSET_MEMBERSHIP_2558_EN.json'):
        raw = p.read_bytes()
        assert b'\r\n' not in raw, p
        assert b'C:/Users/' not in raw and b'C:\\\\Users\\\\' not in raw
    return {'status': 'PASS', 'representations_verified': len(rows), 'table_s1_rows_reproduced': result, 'nominal_flags_unknown': 0, 'original_row_fields_preserved': True, 'pubmed_native_id_difference_exceptions': len(exceptions), 'screening_or_scientific_votes_created': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(json.dumps(validate(args.root.resolve()), ensure_ascii=False, indent=2))
