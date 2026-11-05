"""Validate the public search trail using only Python's standard library.

Usage: python validate_search_trace.py --root PATH_TO_SEARCH_TRACE_DIRECTORY
This checks structure, identifiers, joins, TSV projections and file hashes.
It does not assess eligibility, classification accuracy or human independence.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args();root=args.root.resolve()
    def rd(name):return json.loads((root/name).read_text(encoding='utf-8-sig'))
    cases=rd('SEARCH_UPDATE_CASES_745_EN.json')['records']
    rows=rd('SEARCH_UPDATE_REPRESENTATIONS_2558_EN.json')['records']
    prior=rd('PRIOR_LIBRARY_DECISIONS_REUSED_EN.json')['records']
    edges=rd('CASE_REPRESENTATION_EDGES_EN.json')['records']
    special=rd('SEPARATE_REGISTRY55_AND_QUERY_ABSENCE_EN.json')['records']
    summary=rd('SEARCH_TRACE_SUMMARY_EN.json')
    cby={r['case_id']:r for r in cases};rby={r['representation_id']:r for r in rows};pby={r['group_id']:r for r in prior}
    assert len(cases)==len(cby)==745
    assert len(rows)==len(rby)==2558
    assert len(special)==len({r['representation_id'] for r in special})==56
    assert len(prior)==len(pby)==summary['counts']['distinct_reused_prior_library_groups']
    assert len(edges)==summary['counts']['case_representation_edges']
    assert {r['case_id'] for r in edges}==set(cby)
    for c in cases:
        for role in ['initial_R1','initial_R2']:
            assert c[role]['decision_code'] and c[role]['rationale_as_recorded_pt']
        assert c['family_unit_linkage_is_not_scientific_admission'] is True
        assert c['independent_blinded_validation_established_by_this_export'] is False
    for r in rows:
        assert r['case_ids'] or r['prior_library_decision_links']
        assert all(cid in cby for cid in r['case_ids'])
        assert all(p['group_id'] in pby for p in r['prior_library_decision_links'])
        assert r['native_record_provenance']['record_ordinal']>=1
        assert re.fullmatch('[0-9a-f]{64}',r['native_record_provenance']['native_file_sha256'])
        assert r['scientific_closure_or_independent_review_inferred'] is False
    represented=set(rby)|{r['representation_id'] for r in special}
    assert all(e['representation_id'] in represented for e in edges)
    for json_name,tsv_name,key in [
      ('SEARCH_UPDATE_CASES_745_EN.json','SEARCH_UPDATE_CASES_745_EN.tsv','case_id'),
      ('SEARCH_UPDATE_REPRESENTATIONS_2558_EN.json','SEARCH_UPDATE_REPRESENTATIONS_2558_EN.tsv','representation_id'),
      ('PRIOR_LIBRARY_DECISIONS_REUSED_EN.json','PRIOR_LIBRARY_DECISIONS_REUSED_EN.tsv','group_id')]:
        original=rd(json_name)['records']
        with (root/tsv_name).open(encoding='utf-8-sig',newline='') as f:tab=list(csv.DictReader(f,delimiter='\t'))
        assert len(original)==len(tab)
        assert [r[key] for r in original]==[r[key] for r in tab]
    missing=rd('MISSING_LINKS_AND_LIMITS_EN.json')
    assert len(missing['prior_group_ids_without_recovered_study_specific_reason'])==summary['counts']['prior_group_rationales_not_recovered']
    assert summary['counts']['missing_initial_update_returns']==0
    assert summary['counts']['representations_without_case_or_prior_identity_route']==0
    manifest=rd('PUBLIC_FILE_MANIFEST_SHA256.json')
    for item in manifest['files']:
        path=(root/item['path']).resolve()
        assert path.is_relative_to(root),item['path']
        assert path.is_file() and path.stat().st_size==item['bytes'],item['path']
        # hashlib.file_digest is not available in Python3.10.
        h=hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        assert h.hexdigest()==item['sha256'],item['path']
        if path.suffix in ['.json','.tsv','.html','.txt']:
            text=path.read_text(encoding='utf-8-sig')
            assert not re.search(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file:///',text,re.I),item['path']
            assert not re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',text),item['path']
            assert not re.search(r'"(?:literal_evidence|abstract_as_exported|historical_abstract|updated_abstract|raw_ris_record)"\s*:',text),item['path']
    print(json.dumps({'status':'PASS','cases':len(cases),'update_representations':len(rows),
      'prior_groups':len(prior),'case_representation_edges':len(edges),'special_registry_and_absence':len(special),
      'manifest_files_checked':len(manifest['files']),'accuracy_or_independence_tested':False},indent=2))

if __name__=='__main__':main()
